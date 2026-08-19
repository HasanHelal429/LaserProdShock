#!/usr/bin/env python3
"""The reservoir A/B: a pinned target against the same run unpinned, against FLASH.

    /opt/anaconda3/envs/physics/bin/python scripts/reservoir_ab.py
    ... scripts/reservoir_ab.py --taus 6.7 13.5 20.3 27 --xlim 0 110
    ... scripts/reservoir_ab.py --units de --ylim 1e-6 1e2 --out reservoir_ab_de.png

WHAT IT SHOWS, AND WHY BOTH HALVES ARE NEEDED. `P4_lez_kin_flashic_res` differs from
`P4_lez_kin_flashic_ct` in one thing: WarpX's `TargetInjector` pins the REAR HALF of the
slab at its initial 40 n_cr, standing in for the semi-infinite solid FLASH has and a PIC
foil does not. The claim being tested is that the finite reservoir is what turns FLASH's
smooth exponential into the PIC plateau-and-cliff.

  TOP ROW  the density profiles -- does the cliff become a tail?
  BOTTOM   the MASS BUDGET -- did the injector actually inject?

The bottom row is not decoration. A null result on the top row means nothing unless the
injector demonstrably worked, and "it ran without crashing" is not that: a box placed
outside the domain, or a target density at or below the local one, injects nothing and
leaves a run that looks exactly like the unpinned case. Total weight end/start is the
one number that separates "the reservoir does not matter" from "the reservoir was never
tested".

EVERY DISPLAY CHOICE IS A FLAG. Times, axis units, both limits, the box overlay and the
output name -- because figure requests always iterate, and a second time list should cost
one command rather than one edit.
"""
from __future__ import annotations

import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                    # noqa: E402
import xcode_compare as X                             # noqa: E402
from laserprod import plotting as lpp                 # noqa: E402
from laserprod import io as lpio                      # noqa: E402

C_FLASH  = "#1f4e9c"
C_FOIL   = "#c7522a"      # the project's piston colour: the unpinned run
C_PINNED = "#1f6f8b"      # the project's ambient colour: the pinned run
C_BOX    = "#8a8a8a"


def weights(run_dir, sc, box=None):
    """(tau, total electron weight, weight inside `box`) per plotfile."""
    import yt
    out = []
    for pf in lpio.plotfiles(run_dir, prefix="diag1"):
        try:
            ds = yt.load(pf)
            ds.force_periodicity()
            ad = ds.all_data()
            w = np.asarray(ad[("targ_electrons", "particle_weight")])
            z = np.asarray(ad[("targ_electrons", "particle_position_x")]) / X.DE_CR
        except Exception:
            continue
        wb = float(w[(z >= box[0]) & (z <= box[1])].sum()) if box else np.nan
        out.append((float(ds.current_time) / sc["tau"], float(w.sum()), wb))
    return np.array(sorted(out)) if out else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pinned", default="runs/P4/P4_lez_kin_flashic_res")
    ap.add_argument("--foil",   default="runs/P4/P4_lez_kin_flashic_ct")
    ap.add_argument("--mass-ratio", dest="mr", type=float, default=None,
                    help="m_i/m_e for the WarpX legs; default: read from the pinned "
                         "run's own config, which is what makes zeta and tau its own")
    ap.add_argument("--taus", type=float, nargs="+", default=(6.7, 13.5, 20.3, 27.0),
                    help="times to draw, in tau = t/(d_i0/C_S0)")
    ap.add_argument("--units", choices=("di0", "de"), default="di0",
                    help="x axis: zeta = z/d_i0 (default) or z/d_e")
    ap.add_argument("--xlim", type=float, nargs=2, default=(-5.0, 110.0))
    ap.add_argument("--ylim", type=float, nargs=2, default=(1e-5, 5e2))
    ap.add_argument("--box", type=float, nargs=2, default=(-200.0, -100.0),
                    metavar=("LO_DE", "HI_DE"),
                    help="the pinned box in d_e, for the mass-budget panel")
    ap.add_argument("--no-box-overlay", action="store_true",
                    help="do not shade the pinned box on the profile panels")
    ap.add_argument("--out", default="reservoir_ab.png")
    ap.add_argument("--dpi", type=int, default=130)
    a = ap.parse_args()

    from laserprod import config as lpconfig
    cfg = lpconfig.load(a.pinned)
    mr = a.mr if a.mr else float(cfg["reference"]["mass_ratio"])
    sc = X.warpx_scales(mr)
    unit = sc["di0"] / X.DE_CR if a.units == "di0" else 1.0     # d_e per x unit
    xlab = (r"$\zeta = z/d_{i0}$" if a.units == "di0" else r"$z/d_e$")

    print(f"  m_i/m_e {mr:.0f}  ->  d_i0 = {sc['di0']/X.DE_CR:.3f} d_e, "
          f"tau unit {sc['tau']*1e12:.4f} ps, T_e,SS {sc['tss']:.1f} eV")

    F = X.flash_series(X.FLASH_DIR, "lez1d")
    Sf = X.warpx_particles(a.foil,   X.SP_KIN, sc=sc)
    Sp = X.warpx_particles(a.pinned, X.SP_KIN, sc=sc)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    box_note = [""]
    n = len(a.taus)
    fig = plt.figure(figsize=(3.5 * n, 7.4))
    gs = fig.add_gridspec(2, n, height_ratios=(1.35, 1.0), hspace=0.34, wspace=0.06)

    # --- top row: the profiles ------------------------------------------------
    for c, tau in enumerate(a.taus):
        ax = fig.add_subplot(gs[0, c])
        for S, col, lab, ls in ((None, C_FLASH, "FLASH", "-"),
                                (Sf, C_FOIL, "foil (unpinned)", "--"),
                                (Sp, C_PINNED, "pinned (injector)", "-.")):
            d = X.pick(F, tau) if S is None else X.pick(S, tau)
            if d is None:
                continue
            ax.semilogy(np.asarray(d["zeta"]) * (1.0 if a.units == "di0" else unit),
                        np.maximum(d["ne"], 1e-30), color=col, ls=ls,
                        lw=2.0 if S is None else 1.5, label=lab)
        # The pinned box sits BEHIND the target, at negative zeta, so on the default
        # plume window it is off-screen. Shade it only when it is actually visible --
        # an axvspan clipped to nothing still leaves a stranded label, which reads as a
        # mislabelled feature rather than an absent one.
        if not a.no_box_overlay:
            lo, hi = a.box[0] / unit, a.box[1] / unit
            if hi > a.xlim[0] and lo < a.xlim[1]:
                ax.axvspan(lo, hi, color=C_BOX, alpha=0.16, lw=0)
                if c == 0:
                    ax.text(0.5 * (max(lo, a.xlim[0]) + min(hi, a.xlim[1])),
                            a.ylim[0] * 3, "pinned", color="#5a5a5a",
                            fontsize=7, ha="center", va="bottom", style="italic")
            elif c == 0:
                # Off-window: say so in the caption, not inside the axes, where it
                # collided with the legend.
                box_note[0] = (f"The pinned box [{a.box[0]:g}, {a.box[1]:g}] $d_e$ lies "
                               f"behind the target, outside the plume window shown.")
        ax.axhline(1.0, color="0.55", ls=":", lw=0.9)
        ax.set_xlim(*a.xlim); ax.set_ylim(*a.ylim)
        ax.set_title(rf"$\tau$ = {tau:g}", loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel(xlab)
        lpp.style_axes(ax)
        if c == 0:
            ax.set_ylabel(r"$n_e/n_{cr}$")
            ax.legend(loc="lower left", fontsize=8, framealpha=0.92)
        else:
            ax.tick_params(labelleft=False)

    # --- bottom row: the mass budget, i.e. did the injector inject? -----------
    Wf = weights(a.foil, sc, box=a.box)
    Wp = weights(a.pinned, sc, box=a.box)

    axw = fig.add_subplot(gs[1, 0:max(1, n // 2)])
    for W, col, lab in ((Wf, C_FOIL, "foil (unpinned)"), (Wp, C_PINNED, "pinned")):
        if W is None:
            continue
        axw.plot(W[:, 0], W[:, 1] / W[0, 1], color=col, lw=1.9, label=lab)
        axw.annotate(f"{W[-1, 1] / W[0, 1]:.3f}", xy=(W[-1, 0], W[-1, 1] / W[0, 1]),
                     xytext=(4, 0), textcoords="offset points", color=col,
                     fontsize=9, fontweight="bold", va="center")
    axw.axhline(1.0, color="0.55", ls=":", lw=0.9)
    # The profiles above are read at the FLASH-matched window; these histories run the
    # whole run, which is 5.2x longer (RESULTS.md 2026-08-18: max_step was sized by
    # mixing the two d_i0 conventions). Mark it so the two rows cannot be misread as
    # covering the same span.
    for _ax in (axw,):
        _ax.axvline(max(a.taus), color="0.4", ls="--", lw=1.0)
        _ax.annotate(rf"$\tau$ = {max(a.taus):g}, the window above", xy=(max(a.taus), 1.0),
                     xytext=(6, 14), textcoords="offset points", fontsize=7.5,
                     color="0.35", rotation=90, va="bottom")
    axw.set_xlabel(r"$\tau$"); axw.set_ylabel("total electron weight / initial")
    axw.set_title("Did the injector inject?  (the null is only real if this rises)",
                  loc="left", fontsize=9.5)
    axw.legend(fontsize=8, loc="upper left")
    lpp.style_axes(axw)

    axb = fig.add_subplot(gs[1, max(1, n // 2):])
    for W, col, lab in ((Wf, C_FOIL, "foil"), (Wp, C_PINNED, "pinned")):
        if W is None or not np.isfinite(W[:, 2]).any():
            continue
        axb.plot(W[:, 0], W[:, 2] / W[0, 2], color=col, lw=1.9, label=lab)
        axb.annotate(f"{W[-1, 2] / W[0, 2]:.3f}", xy=(W[-1, 0], W[-1, 2] / W[0, 2]),
                     xytext=(4, 0), textcoords="offset points", color=col,
                     fontsize=9, fontweight="bold", va="center")
    axb.axhline(1.0, color="0.55", ls=":", lw=0.9)
    axb.axvline(max(a.taus), color="0.4", ls="--", lw=1.0)
    axb.set_xlabel(r"$\tau$")
    axb.set_ylabel(f"weight in [{a.box[0]:g}, {a.box[1]:g}] $d_e$ / initial")
    axb.set_title("...and inside the pinned box specifically", loc="left", fontsize=9.5)
    axb.legend(fontsize=8, loc="lower left")
    lpp.style_axes(axb)

    fig.suptitle(
        "The semi-infinite reservoir does NOT close the profile gap. One change from the "
        f"parent: the rear half of the slab pinned at 40 $n_{{cr}}$.  "
        f"$m_i/m_e$ = {mr:.0f}, each code on its own $d_{{i0}}$.",
        fontsize=10.5, y=0.985)
    if box_note[0]:
        fig.text(0.5, 0.952, box_note[0], ha="center", fontsize=8.5, color="0.35")
    return 0 if lpp.savefig(fig, a.out, run_id="P4_lez_kin_flashic_res", dpi=a.dpi) else 1


if __name__ == "__main__":
    raise SystemExit(main())
