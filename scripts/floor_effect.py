#!/usr/bin/env python
"""What the laser temperature floor does to absorption and to T_e.

`LaserDeposition.cpp` sets `m_theta_floor = m_theta_e`, so the floor DEFAULTS to
`electron_temperature`, and a measured per-cell temperature is accepted only if
`kT > kT_floor`. With `electron_temperature` = 378.3 eV and a ~120 eV plume the measurement is
never accepted: `Tlocalfrac` reads 0 and the IB coefficient is evaluated at 378.3 eV for the
whole run. Since `K` goes as `T^(-3/2)` that suppresses absorption.

Four panels: (a) absorbed fraction, (b) `Tlocalfrac` -- the direct evidence the local mode is
inert, (c) plume `T_e` against FLASH and PSC, (d) the `T_e` profile at one time.

Everything that has been revised before is a flag: --legs, --times, --tau, --zlim, --out.
"""
import argparse, os, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, "/home/hhelal/psc-raytrace")
import xcode_compare as xc                                    # noqa: E402
from laserprod import plotting as lpp                          # noqa: E402

DEFAULT_LEGS = (("control (floor = 378.3 eV)", "runs/P4/P4_lez_kin_ic6", "#c1441a"),
                ("floor 20 eV",               "runs/P4/P4_lez_kin_ic6_tfloor", "#1f6f8b"),
                ("ppc 2000 (floor unchanged)","runs/P4/P4_lez_kin_ic6_ppc2k", "#8a8a8a"))
I0 = 1e17


def laserdep(run_dir):
    """(tau_own, f_abs, Tlocalfrac) from the LASERDEP log lines."""
    t, f, tl = [], [], []
    with open(os.path.join(run_dir, "run.log"), "rb") as fh:
        for line in fh:
            if b"LASERDEP step" in line:
                p = line.decode(errors="ignore").split()
                try:
                    t.append(float(p[4]) / xc.TAU_W); f.append(float(p[6]) / I0)
                    tl.append(float(p[10]))
                except Exception:
                    pass
    return np.array(t), np.array(f), np.array(tl)


def band_mean(z, ne, q):
    m = np.isfinite(ne) & (ne >= 1e-2) & (ne <= 1.0) & np.isfinite(q)
    return float(np.average(q[m], weights=ne[m])) if m.any() else np.nan


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leg", action="append", metavar="LABEL=PATH[=COLOR]")
    ap.add_argument("--tau", type=float, default=2.70, help="tau_own for panel (d)")
    ap.add_argument("--zlim", type=float, nargs=2, default=(-3.0, 20.0))
    ap.add_argument("--smooth", type=int, default=201, help="running-mean window on f_abs")
    ap.add_argument("--out", default="floor_effect")
    ap.add_argument("--run-id", default="P4_lez_kin_ic6_tfloor")
    a = ap.parse_args()
    import matplotlib.pyplot as plt

    legs = []
    for spec in (a.leg or []):
        parts = spec.split("=")
        legs.append((parts[0], parts[1], parts[2] if len(parts) > 2 else None))
    if not legs:
        legs = list(DEFAULT_LEGS)

    sc = xc.warpx_scales(2698.0)
    F = xc.flash_series(xc.FLASH_DIR, "lez1d")
    fig, ax = plt.subplots(4, 1, figsize=(7.4, 10.4), constrained_layout=True)

    def smooth(t, y, n):
        """Running mean, trimming the half-window at each end -- 'same' mode tapers
        against zero there and drew a spurious collapse in the last points."""
        if n <= 1 or len(y) < n:
            return t, y
        k = np.ones(n) / n
        ys = np.convolve(y, k, mode="valid")
        h = (n - 1) // 2
        return t[h:len(t) - (n - 1 - h)], ys

    for lbl, rd, col in legs:
        t, f, tl = laserdep(rd)
        ts, fs = smooth(t, f, a.smooth)
        ax[0].plot(ts, fs, "-", color=col, lw=1.5, label=lbl)
        ax[1].plot(t, tl, "-", color=col, lw=1.5, label=lbl)
        W = xc.warpx_particles(rd, xc.SP_KIN, nbin=2500, sc=sc)
        tt = [r["tau"] for r in W]
        te = [band_mean(r["zeta"], r["ne"], r["Te"]) for r in W]
        ax[2].plot(tt, te, "o-", color=col, lw=1.5, ms=4, label=lbl)
        r = xc.pick(W, a.tau)
        m = np.isfinite(r["ne"]) & (r["ne"] >= 1e-2) & (r["ne"] <= 1.0)
        ax[3].plot(r["zeta"][m], r["Te"][m], "-", color=col, lw=1.5, label=lbl)

    # FLASH and PSC references, on the aligned clock
    tF = np.array([s["tau"] - xc.TAU_HANDOFF for s in F])
    teF = np.array([band_mean(s["zeta"], s["ne"], s["Te"]) for s in F])
    fm = (tF >= -0.2) & (tF <= 6.0)
    ax[2].plot(tF[fm], teF[fm], "-", color="#1f4e9c", lw=2.0, label="FLASH")
    ax[0].axhline(0.870, color="#1f4e9c", ls="--", lw=1.4)
    ax[0].text(0.08, 0.885, "FLASH 0.870", color="#1f4e9c", fontsize=8)
    ax[0].axhspan(0.47, 0.56, color="#2a8a5f", alpha=0.16, lw=0)
    ax[0].text(0.08, 0.585, "PSC 0.47-0.56", color="#2a8a5f", fontsize=8)
    for tp, vp in ((1.35, 454.7), (2.70, 516.0), (4.04, 556.6), (5.39, 562.9)):
        ax[2].plot(tp, vp, "s", color="#2a8a5f", ms=6,
                   label="PSC" if tp == 1.35 else None)
    f0 = xc.pick(F, a.tau + xc.TAU_HANDOFF)
    mm = np.isfinite(f0["ne"]) & (f0["ne"] >= 1e-2) & (f0["ne"] <= 1.0)
    ax[3].plot(f0["zeta"][mm], f0["Te"][mm], "-", color="#1f4e9c", lw=2.0, label="FLASH")

    for j, (lab, ttl) in enumerate((
            (r"$f_{abs}$", "(a) absorbed fraction"),
            ("Tlocalfrac", "(b) fraction of cells with a MEASURED $T_e$"),
            (r"$T_e$ in the plume [eV]", "(c) plume $T_e$, density-weighted"),
            (r"$T_e$ [eV]", f"(d) $T_e$ profile at $\\tau_{{own}}$ = {a.tau:g}"))):
        lpp.style_axes(ax[j]); ax[j].set_ylabel(lab, fontsize=9)
        # title ABOVE the axes, so it cannot collide with a legend inside them
        ax[j].set_title(ttl, loc="left", fontsize=9.5, fontweight="bold")
    for j in (0, 1, 2):
        ax[j].set_xlim(0, 5.5); ax[j].set_xlabel(r"$\tau_{own}$", fontsize=9)
    ax[0].set_ylim(0, 1.0); ax[1].set_ylim(-0.02, 0.8); ax[2].set_ylim(0, 700)
    ax[3].set_xlim(*a.zlim); ax[3].set_ylim(0, 800)
    ax[3].set_xlabel(r"$\zeta = z/d_{i0}$", fontsize=9)
    ax[0].legend(fontsize=8, loc="lower right", frameon=False)
    ax[2].legend(fontsize=8, loc="upper left", ncol=2, frameon=False)
    fig.suptitle("The laser temperature FLOOR suppresses absorption\n"
                 "floor defaults to electron_temperature (378.3 eV); a measured $T_e$ is used "
                 "only if it EXCEEDS the floor", fontsize=10)
    lpp.savefig(fig, a.out, run_id=a.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
