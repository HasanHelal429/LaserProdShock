#!/usr/bin/env python3
"""Is a truncated domain equivalent on the FRONT side? A controlled A/B for geometry.

`compare_runs.py` overlays whole-domain quantities, which is the wrong test when the runs
have *different domains*: total particle number and total energy must differ if one run
simply contains less plasma. This script compares only what is supposed to be unchanged —
the region on the laser side of the target — so a truncation can be judged on whether it
altered the ablation rather than on whether it removed material.

    /opt/anaconda3/envs/physics/bin/python scripts/compare_frontside.py \
        runs/P0_bc_open_B runs/P0_rear_reflect runs/P0_rear_open --front -40

What it compares, all restricted to ``z > --front``:

* ``f_abs(t)`` and ``E_abs(t)`` — the drive. These are whole-domain by nature, but the ray
  turns inside the target, so they *should* be insensitive to anything behind it.
* ``n_e(z)`` at matched times — the plume profile.
* the plume front position, taken as the furthest z where ``n_e`` exceeds a threshold.
* the target ions' net **+z momentum**, which is the quantity a rear boundary can change:
  reflecting the rear rarefaction returns its momentum to the slab instead of letting it
  leave.

Writes ``media/<name>/frontside.png``.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod import plotting as lpp       # noqa: E402

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]


def collect(run_dir, front_de):
    import yt
    from plot_fields import load_series, electron_density
    from laserprod.deck import _species_table

    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    species = list(_species_table(cfg))
    t, z, rows = load_series(rd, "diag_fields", sc, species)
    z_de = z / sc.de_ref
    ne = electron_density(rows, species, sc) / sc.n_cr
    m = z_de > front_de

    # plume front: furthest z where the FRONT-SIDE electron density exceeds a threshold
    # set above the ambient so the front is the plume's, not the ambient's
    thr = (3.0 * sc.n_amb_over_ncr) if sc.n_amb_over_ncr else 1e-3
    front = []
    for i in range(len(t)):
        idx = np.where(ne[i][m] > thr)[0]
        front.append(z_de[m][idx.max()] if idx.size else np.nan)

    # target-ion +z momentum on the front side, from the phase-space dumps
    pmom, ptime = [], []
    for p in lpio.plotfiles(rd, "diag_phase"):
        ds = yt.load(p)
        try:
            ad = ds.all_data()
            zi = np.asarray(ad[("targ_ions", "particle_position_x")]) / sc.de_ref
            ui = np.asarray(ad[("targ_ions", "particle_momentum_z")])
            wi = np.asarray(ad[("targ_ions", "particle_weight")])
        except Exception:
            continue
        sel = zi > front_de
        ptime.append(float(ds.current_time))
        pmom.append(float(np.sum(ui[sel] * wi[sel])))

    hist = lpio.laserdep_history(rd)
    return dict(id=lpconfig.run_id(cfg), cfg=cfg, sc=sc, t=t, z_de=z_de, ne=ne, mask=m,
                front=np.asarray(front), hist=hist,
                P_inc=lpio.incident_power(sc, cfg),
                ptime=np.asarray(ptime), pmom=np.asarray(pmom),
                lo=cfg["geometry"]["axis"]["lo_de"],
                bc=lpconfig.boundary_faces(cfg)[
                    str(cfg["geometry"].get("normal_axis", "z"))])


def main() -> int:
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+", help="the REFERENCE run first")
    ap.add_argument("--front", type=float, default=-40.0,
                    help="front-side region is z > this, in d_e (default -40, the "
                         "target's laser-facing face)")
    ap.add_argument("--name", default="frontside")
    args = ap.parse_args()

    runs = [collect(d, args.front) for d in args.run_dirs]
    ref = runs[0]
    print(f"FRONT-SIDE COMPARISON (z > {args.front:g} d_e), reference = {ref['id']}")
    print(f"{'run':18s} {'lo_de':>6s} {'lo BC':>11s} {'f_abs(0)':>9s} {'E_abs':>10s} "
          f"{'front@end':>10s} {'p_z(+) end':>11s}")
    for r in runs:
        f = r["hist"].f_abs(r["P_inc"])
        print(f"{r['id']:18s} {r['lo']:6g} {r['bc'][0]:>11s} {f[0]:9.4f} "
              f"{r['hist'].Eabs[-1]:10.4g} {r['front'][-1]:10.1f} "
              f"{r['pmom'][-1] if r['pmom'].size else float('nan'):11.4g}")
    print()
    for r in runs[1:]:
        # interpolate the reference onto this run's times for a fair difference
        fr = np.interp(r["t"], ref["t"], ref["front"])
        d_front = np.nanmax(np.abs(r["front"] - fr))
        # FINAL E_abs, not the max over time: E_abs starts near zero, so a relative
        # difference taken early is dominated by the first application's noise (f_abs(0)
        # carries a 10.4% 1-sigma -- studies/fabs_noise) and reads ~20% even for runs that
        # agree to 1% once integrated.
        er = np.interp(r["hist"].t, ref["hist"].t, ref["hist"].Eabs)
        d_E = (r["hist"].Eabs[-1] / er[-1] - 1) * 100 if er[-1] else float("nan")
        pr = (np.interp(r["ptime"], ref["ptime"], ref["pmom"])
              if r["pmom"].size and ref["pmom"].size else None)
        d_p = ((r["pmom"][-1] / pr[-1] - 1) * 100 if pr is not None and pr[-1] else
               float("nan"))
        print(f"  {r['id']:18s} vs reference:  ΔE_abs(final) = {d_E:+6.2f}%   "
              f"max |Δfront| = {d_front:5.2f} d_e   Δp_z(front side) = {d_p:+6.2f}%")

    # --- figure -----------------------------------------------------------
    fig, axes = plt.subplots(4, 1, figsize=(11.0, 11.0))
    for i, r in enumerate(runs):
        c = COLORS[i % len(COLORS)]
        lab = f"{r['id']}  (lo {r['lo']:g}, {r['bc'][0]})"
        t_ps = np.asarray(r["hist"].t) * 1e12
        axes[0].plot(t_ps, r["hist"].f_abs(r["P_inc"]), color=c, lw=1.1, label=lab)
        axes[1].plot(t_ps, r["hist"].Eabs, color=c, lw=1.8, label=lab)
        axes[2].plot(r["t"] * 1e12, r["front"], color=c, lw=1.8, label=lab)
        if r["pmom"].size:
            axes[3].plot(r["ptime"] * 1e12, r["pmom"], color=c, lw=1.8, marker="o",
                         ms=3, label=lab)

    axes[0].set_ylabel("f$_{abs}$")
    axes[0].set_title("The drive. The ray turns at the critical surface INSIDE the target, "
                      "so it should not see the rear boundary at all.", loc="left",
                      fontweight="bold")
    axes[1].set_ylabel("E$_{abs}$  [J/m²]")
    axes[1].set_title("Cumulative coupled energy — same reasoning", loc="left",
                      fontweight="bold")
    axes[2].set_ylabel(f"plume front  [d$_e$]")
    axes[2].set_title(f"Front-side plume front (furthest z with n$_e$ > 3 n$_{{amb}}$) — "
                      f"the observable a truncation would move", loc="left",
                      fontweight="bold")
    axes[3].set_ylabel("target-ion p$_z$  [kg m/s per m²]")
    axes[3].set_title("Net +z momentum of target ions on the front side — the quantity a "
                      "rear boundary can change, by returning the rear rarefaction's "
                      "momentum instead of letting it leave", loc="left",
                      fontweight="bold")
    axes[3].set_xlabel("t  [ps]")
    for ax in axes:
        ax.legend(loc="best", fontsize=7.5)
        lpp.style_axes(ax)
    fig.text(0.005, 0.995, f"front-side comparison, z > {args.front:g} d_e  |  "
             + ", ".join(r["id"] for r in runs), ha="left", va="top", fontsize=8,
             color=lpp.INK_2)
    lpp.savefig(fig, "frontside.png", run_id=args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
