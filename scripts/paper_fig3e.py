#!/usr/bin/env python
"""Fig. 3(e) alone — laser power deposition, one panel per time, FLASH vs WarpX.

Panel (e) of ``paper_fig3.py`` carries four times on one axis, which is unreadable once the
profiles are logarithmic and overlapping. This splits them: one stacked panel per time, a
shared log y axis so the shapes are directly comparable panel to panel, and per-panel
annotation of where each code actually puts its energy.

**Times are anchored on the WarpX deposition dumps by default, not on the paper's grid.**
The deposition profile is written by ``laser_deposition.profile_intervals``, which is far
coarser than the plotfile cadence and (in every run before ``P4_lez_kin_thick``) fires only
at the LCM with ``laser_deposition.intervals``. Anchoring on the paper's 0.2/0.4/0.6/0.8 ns
leaves panels with no WarpX curve at all; anchoring on the dumps and pulling FLASH across to
the same aligned time gives every panel both codes, simultaneous to <0.01 tau.

Each panel reports, for both codes:
  zeta_cr    where n_e crosses n_cr -- deposition should peak just outside it
  median     the zeta containing half the absorbed power, the concentration measure
  zeta_90    the zeta containing 90 % of it
"""
import argparse
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import xcode_compare as xc                                          # noqa: E402
from laserprod import plotting as lpp                               # noqa: E402
from paper_fig3 import warpx_depo, unit_integral                    # noqa: E402

F_COL = "#1f4e9c"      # FLASH
W_COL = "#c1441a"      # WarpX


def quantile_zeta(zeta, y, q, lo, hi):
    """zeta below which a fraction q of the deposited power lies, inside the window."""
    m = np.isfinite(y) & (zeta >= lo) & (zeta <= hi) & (y > 0)
    if m.sum() < 3:
        return np.nan
    z, w = zeta[m], y[m]
    o = np.argsort(z)
    z, w = z[o], w[o]
    c = np.cumsum(w)
    c = c / c[-1]
    return float(np.interp(q, c, z))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", default="runs/P4/P4_lez_kin_ic6")
    ap.add_argument("--times", type=float, nargs="+", default=None, metavar="NS",
                    help="FLASH-clock times in ns. Default: anchor on the WarpX deposition "
                         "dumps so every panel has both codes.")
    ap.add_argument("--skip-t0", action="store_true", default=True,
                    help="drop the tau_own = 0 dump (the initial condition)")
    ap.add_argument("--keep-t0", dest="skip_t0", action="store_false")
    ap.add_argument("--tau-offset", type=float, default=xc.TAU_HANDOFF)
    ap.add_argument("--zlim", type=float, nargs=2, default=(-2.0, 45.0), metavar=("LO", "HI"))
    ap.add_argument("--ylim", type=float, nargs=2, default=None, metavar=("LO", "HI"),
                    help="shared y limits; default is 5 decades below the largest drawn")
    ap.add_argument("--scale", choices=("log", "linear"), default="log")
    ap.add_argument("--decades", type=float, default=5.0)
    ap.add_argument("--flash-dir", default=xc.FLASH_DIR)
    ap.add_argument("--flash-base", default="lez1d")
    ap.add_argument("--no-marks", action="store_true",
                    help="omit the critical-surface and median markers")
    ap.add_argument("--out", default="paper_fig3e_bytime")
    a = ap.parse_args()

    import matplotlib.pyplot as plt

    run_id = os.path.basename(os.path.normpath(a.run_dir))
    from laserprod import config as lpconfig
    cfg = lpconfig.load(a.run_dir)
    mr = float(cfg["reference"]["mass_ratio"])
    sc = xc.warpx_scales(mr)
    dz = float(cfg["geometry"]["dz_over_de"]) * xc.DE_CR
    dt = float(cfg["numerics"]["cfl"]) * dz / xc.C

    D = warpx_depo(a.run_dir, sc)
    for d in D:
        d["tau"] = d["step"] * dt / sc["tau"]
    if a.skip_t0:
        D = [d for d in D if d["tau"] > 1e-6]
    if not D:
        raise SystemExit("no WarpX deposition dumps to plot")

    F = xc.flash_series(a.flash_dir, a.flash_base)

    if a.times is None:
        pairs = [(d["tau"] + a.tau_offset, d) for d in D]
    else:
        pairs = []
        for t_ns in a.times:
            tw = t_ns * 1e-9 / xc.TAU_F - a.tau_offset
            k = int(np.argmin([abs(d["tau"] - tw) for d in D]))
            pairs.append((D[k]["tau"] + a.tau_offset, D[k]))

    lo, hi = a.zlim
    n = len(pairs)
    fig, ax = plt.subplots(n, 1, figsize=(7.6, 2.3 * n + 0.5),
                           sharex=True, sharey=True, constrained_layout=True)
    ax = np.atleast_1d(ax)
    allv, rows = [], []

    for i, (tau_f, d) in enumerate(pairs):
        axi = ax[i]
        f = xc.pick(F, tau_f)
        yw = unit_integral(d["zeta"], d["P"], lo, hi)
        yf = None
        if f is not None and f.get("depo") is not None:
            yf = unit_integral(f["zeta"],
                               np.asarray(f["depo"]) * np.asarray(f["dens"]), lo, hi)

        zcr_w = xc.outermost(d["zeta"], d["ne"], 1.0) if "ne" in d else np.nan
        zcr_f = xc.outermost(f["zeta"], f["ne"], 1.0) if f is not None else np.nan

        if yf is not None:
            axi.plot(f["zeta"], yf, "-", color=F_COL, lw=1.7, label="FLASH")
            allv += yf[np.isfinite(yf) & (yf > 0)].tolist()
        if yw is not None:
            axi.plot(d["zeta"], yw, "-", color=W_COL, lw=1.3, alpha=0.9,
                     label=f"WarpX {run_id}")
            allv += yw[np.isfinite(yw) & (yw > 0)].tolist()

        qf = [quantile_zeta(f["zeta"], yf, q, lo, hi) if yf is not None else np.nan
              for q in (0.5, 0.9)]
        qw = [quantile_zeta(d["zeta"], yw, q, lo, hi) if yw is not None else np.nan
              for q in (0.5, 0.9)]
        rows.append((tau_f, d["tau"], tau_f * xc.TAU_F * 1e9, zcr_f, zcr_w, qf, qw))

        if not a.no_marks:
            for z, c in ((qf[0], F_COL), (qw[0], W_COL)):
                if np.isfinite(z):
                    axi.axvline(z, color=c, ls=":", lw=1.2, alpha=0.85)
            for z, c in ((zcr_f, F_COL), (zcr_w, W_COL)):
                if np.isfinite(z):
                    axi.axvline(z, color=c, ls="--", lw=1.0, alpha=0.45)

        axi.text(0.985, 0.90,
                 rf"$t_F$ = {tau_f * xc.TAU_F * 1e9:.2f} ns    "
                 rf"$\tau_F$ {tau_f:.1f} / $\tau_W$ {d['tau']:.1f}",
                 transform=axi.transAxes, ha="right", va="top", fontsize=9)
        txt = "median $\\zeta$:  "
        if np.isfinite(qf[0]):
            txt += f"FLASH {qf[0]:.1f}"
        if np.isfinite(qw[0]):
            txt += f"   WarpX {qw[0]:.1f}"
        if np.isfinite(qf[0]) and np.isfinite(qw[0]) and qw[0] > 0:
            txt += f"   ({qf[0] / qw[0]:.2f}x)"
        axi.text(0.985, 0.76, txt, transform=axi.transAxes, ha="right", va="top",
                 fontsize=8.5, color="#333333")
        lpp.style_axes(axi)
        axi.axvline(0.0, color="#555555", ls="--", lw=0.9, alpha=0.6)
        axi.set_ylabel("deposition\n(unit integral)", fontsize=9)

    if a.scale == "log":
        ax[0].set_yscale("log")
        if a.ylim:
            ax[0].set_ylim(*a.ylim)
        elif allv:
            top = np.percentile(np.array(allv), 99.9) * 3.0
            ax[0].set_ylim(top * 10 ** (-a.decades), top)
    elif a.ylim:
        ax[0].set_ylim(*a.ylim)
    ax[0].set_xlim(lo, hi)
    ax[0].legend(fontsize=9, loc="lower right", frameon=False)
    ax[-1].set_xlabel(r"$\zeta = z / d_{i0}$   (each code in its OWN $d_{i0}$)", fontsize=10)
    fig.suptitle("Laser power deposition, FLASH vs WarpX, one panel per time\n"
                 f"{run_id}   |   clocks aligned, WarpX at "
                 rf"$\tau_{{FLASH}}-{a.tau_offset:g}$   |   "
                 "dotted = median $\\zeta$ of deposition, dashed = that code's $\\zeta_{cr}$",
                 fontsize=9.5)
    lpp.savefig(fig, a.out, run_id=run_id)

    print("\n   t_F[ns]  tau_F  tau_W |    zeta_cr     |     median zeta      |   90% zeta")
    print("                        |  FLASH  WarpX  |  FLASH  WarpX  ratio |  FLASH  WarpX")
    for tf, tw, tns, zcf, zcw, qf, qw in rows:
        r = qf[0] / qw[0] if np.isfinite(qf[0]) and np.isfinite(qw[0]) and qw[0] else np.nan
        print(f"   {tns:6.2f} {tf:6.2f} {tw:6.2f} | {zcf:6.2f} {zcw:6.2f}  |"
              f" {qf[0]:6.2f} {qw[0]:6.2f} {r:6.2f} | {qf[1]:6.2f} {qw[1]:6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
