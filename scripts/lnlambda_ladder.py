#!/usr/bin/env python3
"""The laser-lnLambda ladder: plume T_e against absorbed fraction, WarpX vs PSC.

    /opt/anaconda3/envs/physics/bin/python scripts/lnlambda_ladder.py

THE ARGUMENT THE FIGURE MAKES. Every cross-code table reduces a leg by
`T_ss = 823 mu^(1/3) f_abs^(2/3)`, and that reduction does not survive its own mass-ratio
sweep (RESULTS 2026-08-27: 1529/838/495 eV for mr25/mr100/mr400, a 3.1x spread where a valid
reduction gives one constant). So instead of correcting for `f_abs`, MATCH it: walk WarpX's
laser lnLambda up a ladder at FIXED mass ratio until its time-integrated <f_abs> lands on
PSC's, and read the temperatures off directly. What is left between the codes is then the ion
mass alone -- and dividing PSC by mu^(1/3) puts it on the WarpX ladder.

Everything is MEASURED from the run directories, not hardcoded: <f_abs> from the LASERDEP
lines (the time-integrated fraction, `xcode_compare.absorbed()['f_mean']`, NOT the final
instantaneous f_end that the older tables quote), plume T_e from the last plotfile with
`mass_ratio_scan.leg` (n-weighted over 0.05 < n_e/n_cr < 1, each leg on its own zeta).

Every choice is a flag: --legs, --psc-te, --psc-fabs, --mu, --xlim/--ylim, --guide, --out.
"""
from __future__ import annotations

import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warnings; warnings.filterwarnings("ignore")

import xcode_compare as xc                                    # noqa: E402
from mass_ratio_scan import leg as measure_leg                # noqa: E402
from laserprod import plotting as lpp                         # noqa: E402

A_AL = 26.9815
# run-id : (label, laser lnLambda as configured)
DEFAULT_LEGS = [("P4_lez_kin_mr100",   "nrl per-cell\n(4.75 in plume)"),
                ("P4_lez_kin_cl_ctrl", "constant 4.75"),
                ("P4_lez_kin_clmatch", "constant 11.2"),
                ("P4_lez_kin_cl_psc",  "constant 20.35")]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--legs", nargs="+", default=[r for r, _ in DEFAULT_LEGS],
                    help="WarpX run IDs under runs/P4/, in ladder order")
    ap.add_argument("--labels", nargs="+", default=[l for _, l in DEFAULT_LEGS],
                    help="one label per leg; must match --legs in length")
    ap.add_argument("--mass-ratio", type=float, default=A_AL * 100,
                    help="m_i/m_e of the WarpX legs (they must share it)")
    ap.add_argument("--lo-de", type=float, default=-50.0, help="plume binning window, d_e")
    ap.add_argument("--hi-de", type=float, default=2450.0)
    ap.add_argument("--psc-te", type=float, default=508.8, help="PSC plume T_e, eV")
    ap.add_argument("--psc-fabs", type=float, default=0.5833, help="PSC time-integrated <f_abs>")
    ap.add_argument("--psc-label", default="PSC run_ourflash_511keV")
    ap.add_argument("--mu", type=float, default=None,
                    help="ion-mass ratio PSC/WarpX; default = 1.008/(mu of the legs)")
    ap.add_argument("--guide", choices=["fabs23", "none"], default="fabs23",
                    help="overplot the f_abs^(2/3) curve through the ladder's first point")
    ap.add_argument("--xlim", type=float, nargs=2, default=None)
    ap.add_argument("--ylim", type=float, nargs=2, default=None)
    ap.add_argument("--xticks", type=float, nargs="+", default=[0.35, 0.4, 0.5, 0.6, 0.75],
                    help="explicit log ticks -- the data spans well under a decade, so the "
                         "default decade locator leaves both axes unlabelled")
    ap.add_argument("--yticks", type=float, nargs="+",
                    default=[150, 200, 250, 300, 400, 500, 600])
    ap.add_argument("--out", default="lnlambda_ladder.png")
    ap.add_argument("--run-id", default="P4_lez_kin_clmatch",
                    help="which media/<phase>/<run_id>/ the figure lands in")
    a = ap.parse_args()
    if len(a.labels) != len(a.legs):
        ap.error(f"--labels has {len(a.labels)} entries for {len(a.legs)} legs")

    import matplotlib.pyplot as plt

    # (A_AL*MP/ME)/mass_ratio is m_i,REAL / m_i,leg -- 18.36 for the mr100 family.
    # PSC's ion is real Al (1.008x), so PSC/WarpX ion-mass ratio is 1.008 times that.
    inv_mu_w = (A_AL * xc.MP / xc.ME) / a.mass_ratio
    mu = a.mu if a.mu is not None else 1.008 * inv_mu_w
    cube = mu ** (1.0 / 3.0)

    F, T, L = [], [], []
    print(f"{'leg':22s} {'<f_abs>':>8s} {'plume T_e':>10s} {'cells':>6s}")
    for rid, lab in zip(a.legs, a.labels):
        rd = f"runs/P4/{rid}"
        q = xc.absorbed(rd)
        r = measure_leg(rd, a.mass_ratio, a.lo_de, a.hi_de)
        if q is None or r is None:
            print(f"{rid:22s}  no output — skipped"); continue
        F.append(q["f_mean"]); T.append(r["Te"]); L.append(lab)
        print(f"{rid:22s} {q['f_mean']:8.4f} {r['Te']:9.1f}  {r['ncell']:6d}")
    F, T = np.array(F), np.array(T)
    print(f"\n{a.psc_label:22s} {a.psc_fabs:8.4f} {a.psc_te:9.1f}")
    print(f"{'PSC / mu^(1/3)':22s} {a.psc_fabs:8.4f} {a.psc_te/cube:9.1f}   (mu^(1/3) = {cube:.3f})")

    # where the WarpX ladder sits at PSC's f_abs, by log-log interpolation
    o = np.argsort(F)
    te_at_psc = float(np.exp(np.interp(np.log(a.psc_fabs), np.log(F[o]), np.log(T[o]))))
    ratio = a.psc_te / te_at_psc
    print(f"\nWarpX ladder at <f_abs> = {a.psc_fabs:.4f}: {te_at_psc:.1f} eV")
    print(f"PSC / ladder = {ratio:.3f}   vs mu^(1/3) = {cube:.3f}   -> {abs(ratio/cube-1)*100:.1f}% apart")

    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    lpp.style_axes(ax)

    if a.guide == "fabs23":
        xs = np.linspace(min(F.min(), a.psc_fabs) * 0.88, max(F.max(), a.psc_fabs) * 1.12, 200)
        ax.plot(xs, T[o][0] * (xs / F[o][0]) ** (2.0 / 3.0), color=lpp.INK_MUTED,
                lw=1.1, ls=(0, (5, 3)), zorder=1)
        ax.annotate(r"$T_e \propto f_{\rm abs}^{2/3}$", xy=(xs[-1], T[o][0] * (xs[-1] / F[o][0]) ** (2 / 3)),
                    xytext=(-4, 7), textcoords="offset points", ha="right",
                    color=lpp.INK_MUTED, fontsize=8.5, style="italic")

    ax.plot(F[o], T[o], color=lpp.C_LASER, lw=1.6, zorder=2, alpha=0.9)
    ax.scatter(F, T, s=62, color=lpp.C_LASER, edgecolor="white", linewidth=1.2, zorder=4)
    for f, t, lab in zip(F, T, L):
        ax.annotate(lab, xy=(f, t), xytext=(0, -15), textcoords="offset points",
                    ha="center", va="top", fontsize=7.6, color=lpp.INK_MUTED, linespacing=1.25)

    # PSC, and PSC brought onto the WarpX ion mass
    ax.scatter([a.psc_fabs], [a.psc_te], s=112, marker="D", color=lpp.C_TARGET,
               edgecolor="white", linewidth=1.3, zorder=5)
    ax.annotate(f"{a.psc_label}\n{a.psc_te:.1f} eV", xy=(a.psc_fabs, a.psc_te),
                xytext=(9, 4), textcoords="offset points", fontsize=8.4,
                color=lpp.C_TARGET, fontweight="bold", linespacing=1.3)
    ax.scatter([a.psc_fabs], [a.psc_te / cube], s=112, marker="D",
               facecolor="white", edgecolor=lpp.C_TARGET, linewidth=1.6, zorder=5)
    ax.annotate(f"PSC / $\\mu^{{1/3}}$ = {a.psc_te/cube:.1f} eV",
                xy=(a.psc_fabs, a.psc_te / cube), xytext=(14, -6),
                textcoords="offset points", fontsize=8.4, color=lpp.C_TARGET)
    ax.annotate("", xy=(a.psc_fabs, a.psc_te / cube * 1.06),
                xytext=(a.psc_fabs, a.psc_te * 0.94),
                arrowprops=dict(arrowstyle="-|>", color=lpp.C_TARGET, lw=1.4,
                                shrinkA=0, shrinkB=0, alpha=0.85))
    ax.annotate(f"$\\div\\ \\mu^{{1/3}}$ = {cube:.3f}",
                xy=(a.psc_fabs, np.sqrt(a.psc_te * a.psc_te / cube)),
                xytext=(-8, 0), textcoords="offset points", ha="right",
                fontsize=8.6, color=lpp.C_TARGET, fontweight="bold")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(r"time-integrated absorbed fraction  $\langle f_{\rm abs}\rangle$", fontsize=9.5)
    ax.set_ylabel(r"plume $T_e$  [eV]" "\n" r"n-weighted, 0.05 < $n_e/n_{cr}$ < 1", fontsize=9.5)
    ax.set_xlim(*(a.xlim or (0.325, 0.83)))
    ax.set_ylim(*(a.ylim or (120, 660)))
    from matplotlib.ticker import FuncFormatter, NullLocator
    fmt = FuncFormatter(lambda v, p: f"{v:g}")
    ax.set_xticks(a.xticks); ax.set_yticks(a.yticks)
    ax.xaxis.set_minor_locator(NullLocator()); ax.yaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    ax.tick_params(labelsize=8.6, colors=lpp.INK_MUTED)

    ax.set_title("WarpX walks its laser $\\ln\\Lambda$ up to PSC's absorbed fraction;\n"
                 "what is left between the codes is $\\mu^{1/3}$",
                 fontsize=11.5, color=lpp.INK, pad=11, linespacing=1.35)
    fig.text(0.5, -0.045,
             f"At PSC's $\\langle f_{{\\rm abs}}\\rangle$ = {a.psc_fabs:.4f} the WarpX ladder reads "
             f"{te_at_psc:.1f} eV; PSC/ladder = {ratio:.3f} against $\\mu^{{1/3}}$ = {cube:.3f}, "
             f"{abs(ratio/cube-1)*100:.1f}% apart on a 13.5% noise floor.   "
             f"All legs at $m_i/m_e$ = {a.mass_ratio:.0f}, $\\tau_{{\\rm own}}$ = 5.39.",
             ha="center", fontsize=8.2, color=lpp.INK_MUTED, linespacing=1.4)
    lpp.savefig(fig, a.out, run_id=a.run_id)


if __name__ == "__main__":
    main()
