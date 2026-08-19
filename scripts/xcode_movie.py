#!/usr/bin/env python3
"""Animated FLASH-vs-WarpX comparison on the normalised axes.

    /opt/anaconda3/envs/physics/bin/python scripts/xcode_movie.py \
        runs/P4/P4_lez_kin_flashic
    ... scripts/xcode_movie.py runs/P4/P4_lez_kin_flashic runs/P4/P4_lez_kin --fps 4

Writes ``media/xcode/movie_<ids>.mp4``.

WHY A SEPARATE SCRIPT FROM compare_movie.py. That one overlays two WarpX runs, which share
a unit system; this one crosses codes, and the crossing is the whole difficulty. Every axis
here is normalised per TEST_PLAN 12.2 -- ``zeta = z/d_i0`` with each code's OWN ``d_i0``,
time as ``tau = t/(d_i0/C_S0)`` -- because FLASH runs real aluminium and the WarpX legs run
the paper's reduced mass ratio, so a shared micron axis would be a 4.29x rescaling error.
The loaders, the unit map and the scalars are imported from ``xcode_compare.py`` rather than
re-derived, so the movie and the tables cannot drift apart.

CADENCE, STATED RATHER THAN HIDDEN. All three panels need a particle moment for the WarpX
legs (``T_e`` is a moment, not a field, in a kinetic run), and only ``diag1`` carries the
particle record -- so the movie runs at the ``diag1`` cadence and every panel in a frame
comes from the SAME dump. FLASH is then matched to each frame by tau, and the worst pairing
mismatch is printed. Nothing is held over from a neighbouring time.

The overdense interiors are NOT comparable (n_max 795 n_cr in FLASH against 40 or 10 in
WarpX -- decision D5) and the shaded band marks that; read the underdense plume.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import numpy as np                                      # noqa: E402

from xcode_compare import (BAND, FLASH_DIR, SP_KIN, TE_REF, TSS_REDUCED,   # noqa: E402
                           banner, flash_series, pick, scalars, warpx_particles)
from laserprod import config as lpconfig                # noqa: E402
from laserprod import plotting as lpp                   # noqa: E402

COLS = ["#c1441a", "#2a8a5f", "#7a3fa0"]                # WarpX legs
FLASH_COL = "#1f4e9c"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="one or more WarpX run dirs")
    ap.add_argument("--fps", type=int, default=4)
    ap.add_argument("--zmax", type=float, default=110.0, help="zeta axis limit")
    ap.add_argument("--labels", nargs="*", default=None)
    a = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    banner()
    F = flash_series(FLASH_DIR, "lez1d")
    legs = []
    for rd in a.runs:
        legs.append(dict(rid=lpconfig.run_id(lpconfig.load(rd)),
                         S=warpx_particles(rd, SP_KIN)))
    labels = a.labels or [q["rid"] for q in legs]

    # Frame on the SPARSEST leg, so every frame has real data in every panel.
    lead = min(legs, key=lambda q: len(q["S"]))
    taus = [s["tau"] for s in lead["S"] if s["tau"] > 0]
    worst = max(abs(pick(F, t)["tau"] - t) for t in taus)
    print(f"\n  {len(taus)} frames at the diag1 cadence, tau = {taus[0]:.2f}..{taus[-1]:.2f}")
    print(f"  worst FLASH pairing mismatch: {worst:.3f} tau "
          f"({worst / max(taus) * 100:.1f} % of the run)")

    rid = "_vs_".join([q["rid"] for q in legs] + ["FLASH"])
    d = lpp.movie_dir(rid, "xcode")
    for i, tau in enumerate(taus):
        f = pick(F, tau)
        fig, ax = plt.subplots(3, 1, figsize=(9.6, 9.8), sharex=True)

        series = [("FLASH (real $m_i$)", f, FLASH_COL, "-", 2.1, True)]
        for j, (q, lab) in enumerate(zip(legs, labels)):
            series.append((lab, pick(q["S"], tau), COLS[j % len(COLS)], "--", 1.6, False))

        for lab, s, col, ls, lw, isF in series:
            ne = s["ne"]
            Te = s["Te"] if isF else s.get("Te")
            v = s["v"] if isF else s.get("v")
            ax[0].semilogy(s["zeta"], np.maximum(ne, 1e-6), color=col, lw=lw, ls=ls,
                           label=lab)
            # T_e and v are drawn SOLID inside the comparison band and faded outside it.
            # Outside, a kinetic leg's per-bin moment is carried by a handful of
            # macroparticles and swings by hundreds of eV frame to frame -- real sampling
            # noise, not structure. Plotting it at full weight makes the panel unreadable
            # and invites reading the noise as physics; deleting it would hide how far the
            # comparison actually reaches. Fading does neither.
            inband = np.isfinite(ne) & (ne >= BAND[0]) & (ne <= BAND[1])
            for axis, y in ((ax[1], Te), (ax[2], v)):
                if y is None:
                    continue
                axis.plot(s["zeta"], np.where(inband, y, np.nan), color=col, lw=lw, ls=ls)
                axis.plot(s["zeta"], np.where(inband, np.nan, y), color=col, lw=lw * 0.7,
                          ls=ls, alpha=0.22)

        # n_e -- and the band the comparison is actually made on
        ax[0].axhspan(BAND[0], BAND[1], color="0.85", alpha=0.35, zorder=0)
        ax[0].axhline(1.0, color="0.35", ls=":", lw=1.0)
        ax[0].text(0.004, 1.0, " n$_{cr}$", transform=ax[0].get_yaxis_transform(),
                   va="bottom", fontsize=8, color="0.3")
        ax[0].text(0.004, BAND[0] * 1.3, " comparison band (10$^{-2}$..1 n$_{cr}$)",
                   transform=ax[0].get_yaxis_transform(), va="bottom", fontsize=7.5,
                   color="0.35")
        ax[0].set_ylim(1e-4, 3e3)
        ax[0].set_ylabel(r"$n_e/n_{cr}$")
        ax[0].legend(loc="upper right", fontsize=8.5, framealpha=0.92)
        ax[0].set_title(rf"$\tau$ = {tau:5.2f}   ($t/(d_{{i0}}/C_{{S0}})$;  FLASH 1 ns "
                        rf"$\equiv$ WarpX 54.7 ps $\equiv$ $\tau$ = 27)",
                        loc="left", fontweight="bold", fontsize=10)

        ax[1].axhline(TE_REF, color="0.35", ls=":", lw=1.0)
        ax[1].axhline(TSS_REDUCED, color="0.35", ls="--", lw=1.0)
        ax[1].text(0.004, TE_REF, f" {TE_REF:.0f} eV  Manheimer, real $m_i$ (FLASH)",
                   transform=ax[1].get_yaxis_transform(), va="bottom", fontsize=7,
                   color="0.3")
        ax[1].text(0.004, TSS_REDUCED,
                   f" {TSS_REDUCED:.0f} eV  same at the REDUCED $m_i$ (WarpX)",
                   transform=ax[1].get_yaxis_transform(), va="bottom", fontsize=7,
                   color="0.3")
        ax[1].set_ylim(0, 1200)
        ax[1].set_ylabel(r"$T_e$  [eV]")
        ax[1].text(0.995, 0.05, "solid = inside the comparison band; faded = outside, "
                                "where a kinetic moment is macroparticle noise",
                   transform=ax[1].transAxes, ha="right", va="bottom", fontsize=7,
                   color="0.35")

        ax[2].axhline(0.0, color="0.7", lw=0.7)
        ax[2].set_ylim(-0.6, 6.0)
        ax[2].set_ylabel(r"$v_z/C_{S0}$")
        ax[2].set_xlabel(r"$\zeta = z/d_{i0}$   (each code's OWN $d_{i0}$:"
                         r" 7.256 $\mu$m FLASH, 1.693 $\mu$m WarpX)")

        # the number the comparison is about, on every frame
        sf = scalars(f["zeta"], f["ne"], f["Te"], f["v"])
        txt = []
        for lab, s, _, _, _, isF in series[1:]:
            sc = scalars(s["zeta"], s["ne"], s.get("Te"), s.get("v"))
            r = [f"front {sc['zeta_front']/sf['zeta_front']:.2f}" if sf.get("zeta_front")
                 else "front --",
                 f"T_e {sc['Te_mean_plume']/sf['Te_mean_plume']:.2f}"
                 if sf.get("Te_mean_plume") else "T_e --"]
            txt.append(f"{lab} / FLASH:  " + ",  ".join(r))
        ax[2].text(0.995, 0.04, "\n".join(txt), transform=ax[2].transAxes, ha="right",
                   va="bottom", fontsize=7.5, color="0.2")

        for k in range(3):
            ax[k].set_xlim(-8, a.zmax)
            ax[k].grid(alpha=0.15)
        fig.tight_layout()
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=115)
        plt.close(fig)

    out = os.path.join(lpp.media_dir(run_id=rid), f"movie_xcode.mp4")
    lpp.encode(d, out, fps=a.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
