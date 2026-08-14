#!/usr/bin/env python3
"""Overplot the electron density of two runs in one movie.

    /opt/anaconda3/envs/physics/bin/python scripts/compare_movie.py \
        runs/P4/P4_lez_kin_bg runs/P4/P4_lez_hyb_bg3

Writes ``media/<idA>_vs_<idB>/movie_compare.mp4``.

**Why a separate script rather than a flag on make_movies.py.** A comparison movie has one
job the single-run movies do not: it must make the two runs COMMENSURABLE, and refuse when
they are not. Two runs can only be overplotted on a shared axis if they share the length
normalisation and the time base, and Phase 4 has already been bitten by exactly that -- the
paper carries two incompatible `d_i0`, and a figure that silently rescales one curve is how
a 4.29x error becomes a published claim. So this script checks first and aborts on a
mismatch instead of plotting something that looks fine.

Frames are interpolated onto the SPARSER run's dump times, never resampled in space: the
two grids are compared on their own cell centres.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import plotting as lpp       # noqa: E402


def load(run_dir):
    from plot_fields import load_series, electron_density
    from laserprod.deck import _species_table

    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    species = list(_species_table(cfg))
    t, z, rows = load_series(cfg["_run_dir"], "diag_fields", sc, species)
    if t is None:
        raise SystemExit(f"no diag_fields plotfiles in {run_dir}")
    ne = electron_density(rows, species, sc) / sc.n_cr
    return dict(cfg=cfg, sc=sc, rid=lpconfig.run_id(cfg), t=t,
                z_de=z / sc.de_ref, ne=ne)


def commensurable(a, b):
    """Refuse to overplot runs that do not share the normalisation. Returns warnings."""
    warn = []
    if abs(a["sc"].de_ref / b["sc"].de_ref - 1.0) > 1e-9:
        raise SystemExit(
            f"REFUSING to overplot: different d_e,ref "
            f"({a['sc'].de_ref:.4e} vs {b['sc'].de_ref:.4e} m). The z axes are not the "
            f"same quantity, and a shared axis would be a rescaling error, not a plot.")
    if abs(a["sc"].n_cr / b["sc"].n_cr - 1.0) > 1e-9:
        raise SystemExit("REFUSING to overplot: different n_cr, so n_e/n_cr differs.")
    ta, tb = a["t"][-1] * 1e12, b["t"][-1] * 1e12
    if abs(ta / tb - 1.0) > 0.02:
        warn.append(f"runs end at different times ({ta:.2f} vs {tb:.2f} ps); "
                    f"the movie stops at the shorter one")
    if abs(a["sc"].mass_ratio - b["sc"].mass_ratio) > 1e-9:
        warn.append(f"different mass ratios ({a['sc'].mass_ratio} vs "
                    f"{b['sc'].mass_ratio}) -- the time bases are not comparable")
    return warn


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--labels", nargs=2, default=None)
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    a, b = load(args.run_a), load(args.run_b)
    for w in commensurable(a, b):
        print(f"  WARNING: {w}")
    la, lb = args.labels or (a["rid"], b["rid"])

    # Frame on the SPARSER series, and pair each of its dumps with the nearest in the other
    # run -- reporting the worst mismatch, because a comparison movie whose two curves are
    # from different times is the same failure mode as a rescaled axis.
    lead, other = (a, b) if len(a["t"]) <= len(b["t"]) else (b, a)
    idx = [int(np.argmin(np.abs(other["t"] - tt))) for tt in lead["t"]]
    dt_worst = max(abs(other["t"][j] - tt) for j, tt in zip(idx, lead["t"])) * 1e12
    print(f"  {len(lead['t'])} frames; worst time pairing mismatch {dt_worst:.4f} ps")

    pos = np.concatenate([a["ne"][a["ne"] > 0], b["ne"][b["ne"] > 0]])
    n_lo = max(float(np.percentile(pos, 1.0)), 1e-7)
    n_hi = float(max(a["ne"].max(), b["ne"].max())) * 1.6
    z_lo = min(a["z_de"][0], b["z_de"][0])
    z_hi = max(a["z_de"][-1], b["z_de"][-1])

    rid = f"{a['rid']}_vs_{b['rid']}"
    d = lpp.movie_dir(rid, "compare")
    for i, tt in enumerate(lead["t"]):
        j = idx[i]
        na = lead["ne"][i] if lead is a else other["ne"][j]
        nb = other["ne"][j] if lead is a else lead["ne"][i]
        za = a["z_de"]
        zb = b["z_de"]

        fig, ax = plt.subplots(figsize=(9.6, 4.6))
        ax.plot(za, na, color=lpp.C_TARGET, lw=2.0, label=la)
        ax.plot(zb, nb, color=lpp.C_AMBIENT, lw=1.6, ls="--", label=lb)
        ax.axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        ax.text(0.004, 1.0, " n$_{cr}$", transform=ax.get_yaxis_transform(),
                va="bottom", fontsize=8, color=lpp.INK)
        ax.set_yscale("log")
        ax.set_ylim(n_lo, n_hi)
        ax.set_xlim(z_lo, z_hi)
        ax.set_xlabel("z  [d$_e$ at critical density]")
        ax.set_ylabel("n$_e$ / n$_{cr}$")
        ax.set_title(f"t = {tt*1e12:6.2f} ps", loc="left", fontweight="bold")
        # The number the comparison is actually about, on every frame.
        ratio = nb.max() / na.max() if na.max() > 0 else float("nan")
        ax.text(0.995, 0.955, f"peak ratio  {lb} / {la}  =  {ratio:.2f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=8.5,
                color=lpp.INK)
        ax.legend(loc="upper right", bbox_to_anchor=(0.995, 0.90), fontsize=9,
                  framealpha=0.9)
        ax.grid(alpha=0.15)
        fig.tight_layout()
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=120)
        plt.close(fig)

    out = os.path.join(lpp.media_dir(run_id=rid), "movie_compare.mp4")
    lpp.encode(d, out, fps=args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
