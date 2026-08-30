#!/usr/bin/env python3
"""WarpX / FLASH as a ratio-versus-tau CURVE, not a single-time ratio.

Phase 4's headline was a ratio quoted at one time -- `tau_own` 5.39, a fifth of the way into
FLASH's flat top, at which neither code is near its asymptote. Retraction ledger 15 had
already killed one "the FLASH<->kinetic benchmark passes" for exactly that reason. This tool
replaces the number with a curve, and reports which of three things is true:

  * the ratio is FLAT              -> a genuine code difference, and it is quotable
  * the ratio RISES                -> a rate difference; the single-time ratio was a
                                      stopwatch artifact and the codes are converging
  * the ratio is neither           -> the codes disagree about the SHAPE of the ablation
                                      history, which is a different and larger problem

Three things it does that `xcode_compare.history()` does not:

1. **Ratios, not overlaid curves.** R(tau) = WarpX/FLASH per observable, with a linear fit in
   log R against tau so "flat" is a measured slope with an uncertainty, not an eyeball call.
2. **G3 subtraction.** With `--g3`, the laser-off control's plume-band T_e rise is removed
   from the WarpX leg before any ratio is formed. Absorption and grid heating both look like
   energy arriving, so over a 1 ns leg this is not optional.
3. **A band.** With `--band`, a seed replicate sets the error bar. A slope is only a finding
   if it clears the band.

Only mu = 1 legs are accepted. A reduced-mass leg's seconds are not FLASH's seconds
(HANDOFF.md 4) and its absorption is broken as mu^0.490 (7.4), so no window on FLASH's clock
is the right comparison and the tool refuses rather than producing a plausible wrong number.

Needs the physics env (yt, h5py):
    /opt/anaconda3/envs/physics/bin/python scripts/xcode_trajectory.py runs/P5/P5_full

Usage
-----
    ... xcode_trajectory.py runs/P5/P5_full
    ... xcode_trajectory.py runs/P5/P5_full --g3 runs/P5/P5_full_off --band runs/P5/P5_seed
    ... xcode_trajectory.py runs/P5/P5_full --keys Te_mean_plume L_n --csv out.csv
"""
import argparse
import os
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

# The five FLASH can adjudicate. ne_peak is deliberately NOT here: FLASH's solid is 795 n_cr
# and every PIC leg is capped at 10, so that row is never comparable (HANDOFF.md 2).
KEYS = [("Te_mean_plume", "plume $T_e$ (density-weighted) [eV]"),
        ("zeta_cr", r"critical surface $\zeta_{cr}$"),
        ("L_n", r"density scale length $L_n/d_{i0}$"),
        ("zeta_front", r"plume front $\zeta(10^{-2} n_{cr})$"),
        ("v_at_0p1", r"$v_z/C_{S0}$ at $0.1\,n_{cr}$")]

TAU_HANDOFF_F = 2.696      # 0.1 ns on FLASH's clock, in its own tau


def mu_of(run_dir):
    cfg = yaml.safe_load(open(os.path.join(run_dir, "config.yaml")))
    return float(cfg["reference"]["mass_ratio"]) / 49542.0


def series(run_dir, colour="#c1441a"):
    """Per-dump comparison scalars for one WarpX leg, on FLASH's clock."""
    from xcode_compare import load_leg, leg_state, scalars
    leg = load_leg(os.path.basename(run_dir), run_dir, colour)
    rows = []
    for s in leg["S"]:
        if s["tau"] <= 0:
            continue
        st = leg_state(leg, s["tau"])
        r = scalars(st["zeta"], st["ne"], st.get("Te"), st.get("v"))
        r["tau"] = s["tau"] + TAU_HANDOFF_F
        rows.append(r)
    return rows


def flash_rows():
    from xcode_compare import flash_series, FLASH_DIR, scalars
    return [dict(tau=s["tau"], **scalars(s["zeta"], s["ne"], s["Te"], s["v"]))
            for s in flash_series(FLASH_DIR, "lez1d") if s["tau"] > 0]


def at(rows, key, taus):
    """Linearly interpolate one observable onto a tau grid. nan outside the leg's span."""
    t = np.array([r["tau"] for r in rows], float)
    y = np.array([r.get(key, np.nan) for r in rows], float)
    ok = np.isfinite(t) & np.isfinite(y)
    if ok.sum() < 2:
        return np.full(len(taus), np.nan)
    t, y = t[ok], y[ok]
    o = np.argsort(t)
    out = np.interp(taus, t[o], y[o], left=np.nan, right=np.nan)
    return np.where((taus < t.min()) | (taus > t.max()), np.nan, out)


def slope_of(tau, R):
    """d(ln R)/d(tau) with its standard error. The whole 'flat or rising' question."""
    ok = np.isfinite(tau) & np.isfinite(R) & (R > 0)
    if ok.sum() < 3:
        return np.nan, np.nan
    x, y = tau[ok], np.log(R[ok])
    A = np.vstack([x, np.ones_like(x)]).T
    beta, res, *_ = np.linalg.lstsq(A, y, rcond=None)
    dof = ok.sum() - 2
    if dof <= 0 or res.size == 0:
        return beta[0], np.nan
    s2 = res[0] / dof
    cov = s2 * np.linalg.inv(A.T @ A)
    return beta[0], float(np.sqrt(cov[0, 0]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--g3", metavar="OFF_RUN", default=None,
                    help="laser-off control; its plume-band T_e rise is subtracted first")
    ap.add_argument("--band", metavar="SEED_RUN", default=None,
                    help="seed replicate; sets the error bar the slope must clear")
    ap.add_argument("--keys", nargs="+", default=[k for k, _ in KEYS])
    ap.add_argument("--csv", default=None)
    ap.add_argument("--out", default="media/xcode/trajectory.png")
    a = ap.parse_args()

    mu = mu_of(a.run_dir)
    if abs(mu - 1.0) > 1e-3:
        sys.exit(f"{a.run_dir} runs mu = {mu:.4f}.\n"
                 "Only real-mass legs can be put on FLASH's clock: a reduced-mass leg's\n"
                 "seconds are not FLASH's seconds (HANDOFF.md 4) and its absorption is\n"
                 "broken as mu^0.490 regardless (7.4). Refusing.")

    W = series(a.run_dir)
    F = flash_rows()
    if not W:
        sys.exit(f"no usable dumps in {a.run_dir}")

    tw = np.array([r["tau"] for r in W])
    tf = np.array([r["tau"] for r in F])
    taus = tw[(tw >= max(tw.min(), tf.min())) & (tw <= min(tw.max(), tf.max()))]
    if taus.size < 3:
        sys.exit("fewer than 3 overlapping dumps -- nothing to fit")

    off = series(a.g3) if a.g3 else None
    band = series(a.band) if a.band else None

    print(f"leg   : {a.run_dir}   (mu = {mu:.4f})")
    print(f"FLASH : {len(F)} dumps, tau {tf.min():.2f} - {tf.max():.2f}")
    print(f"overlap: {taus.size} points, tau {taus.min():.2f} - {taus.max():.2f}"
          f"   (t_FLASH {taus.min()*0.037098:.3f} - {taus.max()*0.037098:.3f} ns)")
    if off:
        print(f"G3    : {a.g3}  -- plume-band T_e subtracted")
    if band:
        print(f"band  : {a.band}")
    print()

    hdr = f"  {'observable':22s} {'R(first)':>9s} {'R(last)':>9s} {'dlnR/dtau':>12s} {'+-':>9s}  verdict"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    table = {"tau": taus}
    for key, _lab in KEYS:
        if key not in a.keys:
            continue
        w = at(W, key, taus)
        f = at(F, key, taus)
        if off is not None and key == "Te_mean_plume":
            o = at(off, key, taus)
            base = o[np.isfinite(o)][0] if np.isfinite(o).any() else np.nan
            if np.isfinite(base):
                w = w - (o - base)          # remove the control's RISE, not its level
        R = w / f
        s, se = slope_of(taus, R)
        tol = np.nan
        if band is not None:
            b = at(band, key, taus)
            m = np.isfinite(b) & np.isfinite(w) & (b > 0)
            tol = float(np.nanmean(np.abs(w[m] / b[m] - 1.0))) if m.sum() else np.nan
        rf = R[np.isfinite(R)]
        if rf.size < 2:
            continue
        span = taus[-1] - taus[0]
        if not np.isfinite(se) or se == 0:
            verdict = "-"
        elif abs(s) < 2 * se:
            verdict = "FLAT -- a code difference"
        elif s * span > 0:
            verdict = "RISING -- converging, the single-time ratio was an artifact"
        else:
            verdict = "FALLING -- diverging"
        if np.isfinite(tol) and abs(s * span) < tol:
            verdict += "  (inside the seed band)"
        print(f"  {key:22s} {rf[0]:9.4f} {rf[-1]:9.4f} {s:12.5f} {se:9.5f}  {verdict}")
        table[key + "_warpx"] = w
        table[key + "_flash"] = f
        table[key + "_ratio"] = R

    if a.csv:
        import csv as _csv
        ks = list(table)
        os.makedirs(os.path.dirname(os.path.abspath(a.csv)) or ".", exist_ok=True)
        with open(a.csv, "w", newline="") as fh:
            w_ = _csv.writer(fh); w_.writerow(ks)
            for i in range(len(taus)):
                w_.writerow([f"{table[k][i]:.6g}" for k in ks])
        print(f"\n  csv: {a.csv}")

    # ---- figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ks = [(k, l) for k, l in KEYS if k in a.keys and k + "_ratio" in table]
    if not ks:
        return
    fig, ax = plt.subplots(2, len(ks), figsize=(3.3 * len(ks), 6.4), squeeze=False)
    for j, (k, lab) in enumerate(ks):
        ax[0][j].plot(taus, table[k + "_flash"], color="#1f4e9c", lw=1.9, label="FLASH")
        ax[0][j].plot(taus, table[k + "_warpx"], color="#c1441a", lw=1.6, ls="--",
                      label="WarpX")
        ax[0][j].set_title(lab, fontsize=9)
        ax[0][j].grid(alpha=0.15)
        ax[1][j].axhline(1.0, color="0.6", lw=0.9, ls=":")
        ax[1][j].plot(taus, table[k + "_ratio"], color="#7a3fa0", lw=1.7)
        ax[1][j].set_xlabel(r"$\tau$ (FLASH's clock)")
        ax[1][j].set_ylabel("WarpX / FLASH" if j == 0 else "")
        ax[1][j].grid(alpha=0.15)
    ax[0][0].legend(fontsize=8)
    fig.suptitle("FLASH benchmark as a trajectory. Top: both codes. Bottom: the ratio -- "
                 "flat is a code difference, rising is a stopwatch artifact.", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    fig.savefig(a.out, dpi=135)
    print(f"  figure: {a.out}")


if __name__ == "__main__":
    main()
