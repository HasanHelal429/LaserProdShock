#!/usr/bin/env python3
"""talk_xcode.py -- the ablation cross-code comparison, drawn for a projector.

``xcode_compare.py`` writes the working figures: ``history.png`` is four panels
across 17.5 inches and ``profiles.png`` is a 5x3 grid. Both are meant to be read
at a desk. On a slide the panel titles land near 4 pt and the grid is
unparseable, so this redraws the SAME series -- same loaders, same unit map,
same scalars -- as two or three large panels sized for one slide.

    /opt/anaconda3/envs/physics/bin/python scripts/talk_xcode.py
    /opt/anaconda3/envs/physics/bin/python scripts/talk_xcode.py --panels front,v,Te

Nothing here recomputes physics; it imports xcode_compare so the talk figure
cannot drift from the notebook figure. Writes media/xcode/talk_ablation.png.

CAVEAT TO CARRY ONTO THE SLIDE: RESULTS.md 2026-08-18 records two disqualifiers
on the hybrid's agreement with FLASH -- it absorbs 2.1x less laser yet expands
faster, and it is not robust to the background density (bg3 -> bg4 moves the
plume front 1.8x). The right claim from this figure is that the ray-traced
laser drives an ablation whose bulk hydrodynamics are the right SHAPE, not that
the hybrid is validated against FLASH.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                          # noqa: E402
import xcode_compare as X                                   # noqa: E402

PANELS = {
    "Te":    ("Te_mean_plume", r"$T_e$ in the plume  [eV]"),
    "front": ("zeta_front",    r"plume front  $\zeta$  [$d_{i0}$]"),
    "v":     ("v_at_0p1",      r"outflow  $v_z/C_{S0}$"),
    "Ln":    ("L_n",           r"scale length  $L_n/d_{i0}$"),
}


def series(kin, hyb):
    """The same three legs history() builds, in the same units."""
    F = X.flash_series(X.FLASH_DIR, "lez1d")
    K = X.warpx_particles(kin, X.SP_KIN)
    H = X.warpx_particles(hyb, X.SP_HYB)
    Hf = X.warpx_fields(hyb)
    out = {}
    for name, S in (("FLASH", F), ("kinetic", K), ("hybrid", H)):
        rows = []
        for s in S:
            if s["tau"] <= 0:
                continue
            if name == "hybrid":
                hf = X.pick(Hf, s["tau"], "Te")
                Te = np.interp(s["zeta"], hf["zeta"], hf["Te"]) if hf else None
            else:
                Te = s.get("Te")
            sc = X.scalars(s["zeta"], s["ne"], Te, s.get("v"))
            sc["tau"] = s["tau"]
            rows.append(sc)
        out[name] = rows
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kinetic", default="runs/P4/P4_lez_kin_bg")
    ap.add_argument("--hybrid", default="runs/P4/P4_lez_hyb_bg3")
    ap.add_argument("--panels", default="front,v",
                    help="comma list from " + ",".join(PANELS))
    ap.add_argument("--fontsize", type=float, default=17.0)
    ap.add_argument("--figsize", type=float, nargs=2, default=None,
                    help="inches; default 5.2 per panel x 4.3")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--out", default="media/xcode/talk_ablation.png")
    a = ap.parse_args()

    keys = [k.strip() for k in a.panels.split(",") if k.strip()]
    bad = [k for k in keys if k not in PANELS]
    if bad:
        ap.error(f"unknown panel(s) {bad}; choose from {list(PANELS)}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ser = series(a.kinetic, a.hybrid)

    plt.rcParams.update({
        "font.size": a.fontsize,
        "axes.labelsize": a.fontsize,
        "axes.titlesize": a.fontsize,
        "xtick.labelsize": a.fontsize - 3,
        "ytick.labelsize": a.fontsize - 3,
        "legend.fontsize": a.fontsize - 2,
    })

    fs = tuple(a.figsize) if a.figsize else (5.2 * len(keys), 4.3)
    fig, ax = plt.subplots(1, len(keys), figsize=fs, squeeze=False)
    ax = ax[0]

    for j, k in enumerate(keys):
        field, label = PANELS[k]
        for name, col in X.COLS.items():
            r = ser[name]
            ls = "-" if name == "FLASH" else ("--" if name == "kinetic" else "-.")
            ax[j].plot([q["tau"] for q in r], [q.get(field, np.nan) for q in r],
                       color=col, ls=ls, lw=2.6 if name == "FLASH" else 2.2,
                       label=name)
        ax[j].set_xlabel(r"$\tau = t/(d_{i0}/C_{S0})$")
        ax[j].set_title(label)
        ax[j].set_xlim(0, 27.5)
        ax[j].grid(alpha=0.15)
        for side in ("top", "right"):
            ax[j].spines[side].set_visible(False)
        if k == "Te":
            # Each leg has its OWN Manheimer target: T_e,SS ~ mu^(1/3), and the
            # WarpX legs run 18.36x lighter. Drawing only 823 eV is the error
            # RESULTS.md 2026-08-18 retracts.
            ax[j].axhline(X.TE_REF, color="0.45", ls=":", lw=1.2)
            ax[j].axhline(X.TSS_REDUCED, color="0.45", ls="--", lw=1.2)
            ax[j].set_ylim(0, 1000)

    ax[0].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.savefig(a.out, dpi=a.dpi)
    print(f"  figure: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
