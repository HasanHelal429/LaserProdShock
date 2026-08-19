#!/usr/bin/env python
"""Fig. 3 of Lezhnin et al., Phys. Plasmas 32, 022701 (2025) — recreated with a WarpX leg
in place of the paper's PSC run.

The paper's figure is a five-panel FLASH-vs-PIC comparison of the profile evolution:
(a) electron density, (b) electron temperature, (c) ion temperature, (d) flow speed, and
(e) the laser power absorption profile, at t = 0.2/0.4/0.6/0.8 ns in red/blue/green/magenta,
FLASH solid and the PIC code dashed.

Two things about the clocks, both of which change what the figure means:

* **The codes' clocks are offset by 2.696 tau.** Every Phase-4 WarpX initial condition stands
  for FLASH's t = 0.1 ns state, so a WarpX leg at its own tau is FLASH's tau + 2.696. The
  requested times are FLASH times; the WarpX leg is sampled at (tau_FLASH - offset). Passing
  ``--tau-offset 0`` reproduces the older, misaligned comparison.
* **WarpX's dump cadence is coarse compared with FLASH's.** ic6_long dumps particles every
  5.391 tau while FLASH dumps every ~0.54 tau, so a requested time lands up to ~2.7 tau from
  the nearest WarpX dump. Every curve is therefore labelled with the time ACTUALLY used, and
  ``--report`` prints the mismatch. ``--times 0.3 0.5 0.7 0.9`` happens to land on ic6_long's
  dumps almost exactly, if an exact match matters more than the paper's nominal times.

Axes are each code's own normalised coordinates (zeta = z/d_i0, v/C_S0), which is the
similarity transfer the whole Phase-4 comparison rests on: d_i0 and C_S0 differ between the
codes because the WarpX legs run a reduced mass ratio, so raw microns and eV are NOT
comparable but the normalised profiles are.
"""
import argparse
import glob
import os
import re
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import xcode_compare as xc                                          # noqa: E402
from laserprod import plotting as lpp                               # noqa: E402

# The paper's own times and colour order (Fig. 3 caption: red, blue, green, magenta).
PAPER_TIMES_NS = (0.2, 0.4, 0.6, 0.8)
PAPER_COLORS = ("#d62728", "#1f77b4", "#2ca02c", "#c02cc0")

PANELS = (("ne", r"$n_e / n_{cr}$", True),
          ("Te", r"$T_e$  [eV]", False),
          ("Ti", r"$T_i$  [eV]", False),
          ("v",  r"$v_z / C_{S0}$", False),
          ("depo", "laser deposition\n(unit integral)", False))


def warpx_depo(run_dir, sc):
    """Per-cell laser deposition profiles, (tau, zeta, dP/dzeta normalised to unit integral).

    Columns are ``z n_e H P_abs theta_e A lnLambda`` (the file's own header). P_abs is
    column 3 -- taking the last column instead silently plots lnLambda, which is constant.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(run_dir, "diags", "laserdep_profile_[0-9]*.txt")),
                    key=lambda q: int(re.search(r"(\d+)\.txt$", q).group(1))):
        step = int(re.search(r"(\d+)\.txt$", p).group(1))
        d = np.loadtxt(p)
        z = d[:, 0] / sc["di0"]
        P = np.maximum(np.nan_to_num(d[:, 3]), 0.0)
        out.append(dict(step=step, zeta=z, P=P))
    return out


def mask_low(y, ne, floor):
    """Blank a moment wherever there is essentially no plasma to take a moment of."""
    if y is None:
        return None
    y = np.asarray(y, dtype=float).copy()
    if ne is None:
        return y
    ne = np.asarray(ne, dtype=float)
    n = min(len(y), len(ne))
    out = np.full(len(y), np.nan)
    out[:n] = np.where(np.isfinite(ne[:n]) & (ne[:n] >= floor), y[:n], np.nan)
    return out


def unit_integral(zeta, y, lo, hi):
    """Normalise y to unit integral over the plotted window; nan if it carries nothing."""
    m = np.isfinite(y) & (zeta >= lo) & (zeta <= hi)
    if not m.any():
        return None
    A = np.trapezoid(y[m], zeta[m]) if hasattr(np, "trapezoid") else np.trapz(y[m], zeta[m])
    if not np.isfinite(A) or A <= 0:
        return None
    return np.where(np.isfinite(y), y / A, np.nan)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", default="runs/P4/P4_lez_kin_ic6_long",
                    help="the WarpX leg standing in for the paper's PSC run")
    ap.add_argument("--times", type=float, nargs="+", default=list(PAPER_TIMES_NS),
                    metavar="NS", help="comparison times in ns on FLASH's clock (default: "
                                       "the paper's 0.2 0.4 0.6 0.8, which land on "
                                       "P4_lez_kin_ic6's 1.348 tau dump grid almost "
                                       "exactly). NOTE on ic6_LONG the dump spacing is "
                                       "5.391 tau and the 2.696 clock offset is half of "
                                       "it, so the paper's grid lands mid-interval there; "
                                       "--snap (on by default) keeps the pair simultaneous "
                                       "but the achieved times shift. Use ic6.")
    ap.add_argument("--no-snap", dest="snap", action="store_false",
                    help="do not snap to WarpX dumps; sample each code at the requested "
                         "time independently, which can leave the two curves in a colour "
                         "pair up to half a dump interval apart")
    ap.add_argument("--tau-offset", type=float, default=xc.TAU_HANDOFF,
                    help="WarpX is sampled at (tau_FLASH - offset). 0 = the misaligned "
                         f"comparison (default {xc.TAU_HANDOFF})")
    ap.add_argument("--zlim", type=float, nargs=2, default=(-6.0, 45.0), metavar=("LO", "HI"),
                    help="zeta window in d_i0 (default -6 45)")
    ap.add_argument("--colors", nargs="+", default=list(PAPER_COLORS))
    ap.add_argument("--flash-dir", default=xc.FLASH_DIR)
    ap.add_argument("--flash-base", default="lez1d")
    ap.add_argument("--depo-tol", type=float, default=3.0,
                    help="max |dtau| between a requested time and an available WarpX "
                         "deposition dump before panel (e) omits it (default 3)")
    ap.add_argument("--no-depo", action="store_true", help="drop panel (e)")
    ap.add_argument("--nfloor", type=float, default=1e-3, metavar="N_CR",
                    help="mask T_e, T_i and v where n_e/n_cr is below this (default 1e-3). "
                         "Two independent reasons: FLASH's delivered T_i carries a known "
                         "VACUUM ARTIFACT that reaches ~1.4e5 eV where there is no plasma "
                         "(see runs/P4/P4_lez_flash/DELIVERY.md), and a WarpX per-bin "
                         "moment out in the wing is a handful of macroparticles. Both make "
                         "the panel autoscale to noise.")
    ap.add_argument("--tnorm", choices=("tss", "none"), default="tss",
                    help="tss (default): plot T/T_e,SS with EACH code in its OWN steady-state "
                         "temperature -- FLASH 823 eV at real mass, WarpX 823/mu^(1/3). The "
                         "paper's Fig. 3 is in eV, but the WarpX legs run a reduced mass "
                         "ratio and T_e,SS scales as mu^(1/3), so raw eV compares two "
                         "different physical scales and makes an agreeing run look 2.6x "
                         "cold. 'none' reproduces the paper's absolute axis.")
    ap.add_argument("--te-lim", type=float, nargs=2, default=None, metavar=("LO", "HI"))
    ap.add_argument("--ti-lim", type=float, nargs=2, default=None, metavar=("LO", "HI"))
    ap.add_argument("--v-lim", type=float, nargs=2, default=None, metavar=("LO", "HI"))
    ap.add_argument("--out", default="paper_fig3")
    ap.add_argument("--report", action="store_true", help="print the times actually used")
    a = ap.parse_args()

    import matplotlib.pyplot as plt

    run_id = os.path.basename(os.path.normpath(a.run_dir))
    cfg = None
    try:
        from laserprod import config as lpconfig
        cfg = lpconfig.load(a.run_dir)
        mr = float(cfg["reference"]["mass_ratio"])
    except Exception:
        mr = xc.MASS_RATIO_SIM
    sc = xc.warpx_scales(mr)

    F = xc.flash_series(a.flash_dir, a.flash_base)
    W = xc.warpx_particles(a.run_dir, xc.SP_KIN, sc=sc)
    D = [] if a.no_depo else warpx_depo(a.run_dir, sc)
    # dt = cfl * dz / c, with dz = dz_over_de * d_e,cr -- read both from the config
    # rather than assuming the 0.5 default, which is a per-run choice (gate G7).
    if cfg:
        dz = float(cfg["geometry"]["dz_over_de"]) * xc.DE_CR
        dt = float(cfg["numerics"]["cfl"]) * dz / xc.C
        for d in D:
            d["tau"] = d["step"] * dt / sc["tau"]
    else:
        for d in D:
            d["tau"] = np.nan

    panels = [p for p in PANELS if not (a.no_depo and p[0] == "depo")]
    fig, ax = plt.subplots(len(panels), 1, figsize=(7.4, 2.05 * len(panels)),
                           sharex=True, constrained_layout=True)
    lo, hi = a.zlim
    used = []
    seen = {}
    depo_drawn = 0

    for i, t_ns in enumerate(a.times):
        col = a.colors[i % len(a.colors)]
        tau_f = t_ns * 1e-9 / xc.TAU_F
        tau_w = tau_f - a.tau_offset
        w = xc.pick(W, tau_w)
        if w is None:
            continue
        # Snap FLASH to the WarpX dump actually used, so the two curves in a colour pair
        # are SIMULTANEOUS. WarpX's cadence is the binding constraint (5.391 tau against
        # FLASH's ~0.54), so anchoring on it and pulling FLASH across is the only way to
        # remove the offset rather than merely report it.
        if a.snap:
            tau_f = w["tau"] + a.tau_offset
        f = xc.pick(F, tau_f)
        if f is None:
            continue
        used.append((t_ns, tau_f, f["tau"], tau_w, w["tau"]))

        for j, (key, _lab, _log) in enumerate(panels):
            axj = ax[j]
            if key == "depo":
                fy = f.get("depo")
                if fy is not None:
                    y = unit_integral(f["zeta"], np.asarray(fy) * np.asarray(f["dens"]),
                                      lo, hi)
                    if y is not None:
                        axj.plot(f["zeta"], y, "-", color=col, lw=1.6)
                if D:
                    k = int(np.argmin([abs(d["tau"] - tau_w) for d in D]))
                    if abs(D[k]["tau"] - tau_w) <= a.depo_tol:
                        y = unit_integral(D[k]["zeta"], D[k]["P"], lo, hi)
                        if y is not None:
                            axj.plot(D[k]["zeta"], y, "--", color=col, lw=1.5)
                            depo_drawn += 1
                continue
            fy = mask_low(f.get(key), f.get("ne"), a.nfloor)
            wy = mask_low(w.get(key), w.get("ne"), a.nfloor)
            if a.tnorm == "tss" and key in ("Te", "Ti"):
                # each code by its OWN steady-state temperature (the similarity transfer)
                fy = None if fy is None else fy / xc.TE_REF
                wy = None if wy is None else wy / sc["tss"]
            if fy is not None:
                seen.setdefault(key, []).extend(np.asarray(fy)[np.isfinite(fy)].tolist())
            if wy is not None:
                seen.setdefault(key, []).extend(np.asarray(wy)[np.isfinite(wy)].tolist())
            if fy is not None:
                axj.plot(f["zeta"], fy, "-", color=col, lw=1.6,
                         label=(rf"$\tau_F${f['tau']:.1f} / $\tau_W${w['tau']:.1f}"
                                if j == 0 else None))
            if wy is not None:
                axj.plot(w["zeta"], wy, "--", color=col, lw=1.5, alpha=0.95)

    for j, (key, lab, log) in enumerate(panels):
        axj = ax[j]
        lpp.style_axes(axj)
        if a.tnorm == "tss" and key == "Te":
            lab = r"$T_e / T_{e,SS}$"
        elif a.tnorm == "tss" and key == "Ti":
            lab = r"$T_i / T_{e,SS}$"
        axj.set_ylabel(lab, fontsize=9)
        if a.tnorm == "tss" and key in ("Te", "Ti"):
            axj.axhline(1.0, color="#8a8a8a", ls=":", lw=1.0)
        axj.set_xlim(lo, hi)
        if log:
            axj.set_yscale("log")
            axj.set_ylim(1e-3, 30)
            axj.axhline(1.0, color="#8a8a8a", ls=":", lw=1.0)
            axj.text(hi, 1.0, r" $n_{cr}$", color="#8a8a8a", fontsize=8,
                     va="center", ha="left")
        # the paper's vertical dashed line: the t=0 target edge, -4.5..0 d_i
        axj.axvline(0.0, color="#555555", ls="--", lw=0.9, alpha=0.7)
        axj.axvspan(-4.5, 0.0, color="#999999", alpha=0.10, lw=0)
        axj.text(0.012, 0.86, f"({chr(97 + j)})", transform=axj.transAxes,
                 fontsize=10, fontweight="bold")
    explicit = {"Te": a.te_lim, "Ti": a.ti_lim, "v": a.v_lim}
    for j, (key, _l, _g) in enumerate(panels):
        if key not in ("Te", "Ti", "v"):
            continue
        if explicit.get(key):
            ax[j].set_ylim(*explicit[key])
        elif seen.get(key):
            vals = np.array(seen[key])
            top = np.percentile(vals, 99.5) * 1.15
            bot = min(0.0, np.percentile(vals, 0.5))
            if np.isfinite(top) and top > bot:
                ax[j].set_ylim(bot, top)
        if key == "v":
            ax[j].axhline(0.0, color="#8a8a8a", ls=":", lw=1.0)

    if not a.no_depo and not depo_drawn:
        ax[-1].text(0.5, 0.62, "no WarpX deposition dump within "
                    f"{a.depo_tol:g} tau of these times\n"
                    "(profile_intervals was not a multiple of laser.intervals, so only "
                    "4 of 20 dumps were written; fixed in P4_lez_kin_thick)",
                    transform=ax[-1].transAxes, ha="center", va="center",
                    fontsize=8, color="#b03030", style="italic")
    ax[-1].set_xlabel(r"$\zeta = z / d_{i0}$   (each code in its OWN $d_{i0}$)", fontsize=10)
    h, l = ax[0].get_legend_handles_labels()
    ax[0].legend(h, l, fontsize=8, ncol=len(a.times), loc="upper right", frameon=False)
    from matplotlib.lines import Line2D
    ax[1].legend(handles=[Line2D([], [], color="#444", ls="-", lw=1.6, label="FLASH"),
                          Line2D([], [], color="#444", ls="--", lw=1.5, label=f"WarpX {run_id}")],
                 fontsize=8, loc="upper right", frameon=False)

    fig.suptitle("Lezhnin et al. 2025 Fig. 3, recreated: FLASH vs WarpX profile evolution\n"
                 f"{run_id}   |   clocks aligned, WarpX sampled at "
                 rf"$\tau_{{FLASH}}-{a.tau_offset:g}$   |   $\mu$ = {mr:g}"
                 + (rf"   |   $T_{{e,SS}}$: FLASH {xc.TE_REF:.0f} eV, "
                    rf"WarpX {sc['tss']:.0f} eV" if a.tnorm == "tss" else ""),
                 fontsize=9.5)
    p = lpp.savefig(fig, a.out, run_id=run_id)

    if True:
        print(f"\n  panel (e): FLASH deposition x density, WarpX P_abs; each normalised to "
              f"unit integral over {lo:g} <= zeta <= {hi:g}")
        print("\n  requested   FLASH tau (used)      WarpX tau_own (used)     mismatch")
        for t_ns, tf, tfu, tw, twu in used:
            print(f"  {t_ns:5.2f} ns  {tf:7.3f} ({tfu:7.3f})   {tw:8.3f} ({twu:8.3f})"
                  f"     {twu - tw:+6.3f} tau")
        if D:
            taus = ", ".join("%.1f" % d["tau"] for d in D)
            print("\n  WarpX deposition dumps available at tau_own: " + taus)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
