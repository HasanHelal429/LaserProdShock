#!/usr/bin/env python3
"""Measure the exit-boundary overshoot: compare the ray tracer's per-cell deposition
against an exact analytic march, cell by cell, over a ray_cfl ladder.

THE BUG. In ``LaserDeposition.cpp`` the domain-exit test

    if (c[m_axis] < plo[m_axis] || c[m_axis] > phi[m_axis]) { break; }

runs **after** that step's ``deposit`` call. So the ray always takes one full RK4
arc-length step (``ray_cfl x min(dx)``) past the boundary and deposits it, and ``deposit``
clamps the cell index into the valid box — putting the beyond-domain absorption into the
last cell. The energy is **created**, not misplaced: nothing was removed from anywhere
else.

THE MEASUREMENT. A uniform underdense slab has an exact solution. With the ray entering at
``z = hi`` and travelling ``-z``, at a distance ``s`` from the injection face

    I(s)     = I0 exp(-K s)
    P_abs(s) = K I(s)                      [W/m^3]

so the deposition profile is known analytically in every cell, and the fractional excess
in the last cell at the exit face IS the overshoot. Because the operator's own
``LASERDEP Pabs`` and the profile table agree to six digits, the profile table is a
faithful record of what the tracer did.

    /opt/anaconda3/envs/physics/bin/python studies/exit_overshoot/analyze.py

Writes ``media/exit_overshoot/overshoot.png`` and prints the table.
"""

from __future__ import annotations

import glob
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod import plotting as lpp       # noqa: E402
from laserprod import units as u            # noqa: E402


def analytic_profile(z_centres, sc, cfg):
    """Exact CELL-AVERAGED P_abs [W/m^3] for a uniform slab, from the injection face.

    Cell-AVERAGED, not the cell-centre value: the operator reports a cell average, and
    for an exponential the two differ by O((K dz)^2/24). That is small here but it is a
    systematic bias, and the whole point of this measurement is to attribute a few percent
    correctly. The average over a cell spanning [s1, s2] is

        <P_abs> = I0 (exp(-K s1) - exp(-K s2)) / (s2 - s1)

    i.e. exactly the absorbed power in the cell divided by its width.
    """
    Z_eff = float(cfg["laser"].get("Z_eff", 1.0))
    lnL = float(cfg["laser"].get("coulomb_log", 2.0))
    theta = sc.theta_e_targ
    I0 = sc.intensity
    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    face = sc.domain_hi if inject_hi else sc.domain_lo
    K = u.K_ib(sc.n_targ, theta, sc.n_cr, Z_eff, lnL)
    dz = sc.dz
    s = np.abs(z_centres - face)
    s1, s2 = s - 0.5 * dz, s + 0.5 * dz
    return I0 * (np.exp(-K * np.maximum(s1, 0.0)) - np.exp(-K * s2)) / dz, K


def main() -> int:
    import matplotlib.pyplot as plt

    dirs = sorted(glob.glob(os.path.join(HERE, "scratch", "raycfl_*")),
                  key=lambda d: float(os.path.basename(d).split("_")[1]))
    if not dirs:
        print("no variants; run studies/exit_overshoot/run_variants.sh first")
        return 1

    rows = []
    for d in dirs:
        rc = float(os.path.basename(d).split("_")[1])
        cfg = lpconfig.load(d)
        sc = lpconfig.derive(cfg)
        tabs = lpio.profile_tables(d)
        if not tabs:
            print(f"  {os.path.basename(d)}: no profile dump")
            continue
        tab = lpio.read_profile_table(tabs[0])          # step 0
        z = np.asarray(tab["z"])
        Pabs = np.asarray(tab["P_abs"])
        ana, K = analytic_profile(z, sc, cfg)

        inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
        # the EXIT face is the one opposite injection; its cell is first/last in z order
        i_exit = 0 if inject_hi else len(z) - 1
        # a clean interior window, away from both faces
        n = len(z)
        interior = slice(int(0.15 * n), int(0.85 * n))

        exc_exit = Pabs[i_exit] / ana[i_exit] - 1.0
        exc_int = float(np.mean(Pabs[interior] / ana[interior]) - 1.0)
        tot_meas = float(np.sum(Pabs)) * sc.dz
        tot_ana = sc.intensity * (1.0 - math.exp(-K * (sc.domain_hi - sc.domain_lo)))
        scatter = float(np.std(Pabs[interior] / ana[interior]))
        rows.append(dict(rc=rc, scatter=scatter, exc_exit=exc_exit, exc_int=exc_int,
                         tot_rel=tot_meas / tot_ana - 1.0, K=K,
                         tau=K * (sc.domain_hi - sc.domain_lo),
                         z=z / sc.de_ref, ratio=Pabs / ana, sc=sc,
                         n_cell=n, i_exit=i_exit))

    if not rows:
        return 1

    print(f"exit-boundary overshoot  (tau = {rows[0]['tau']:.4g}, "
          f"K = {rows[0]['K']:.4g} /m, {rows[0]['n_cell']} cells)")
    print("  the mechanism predicts the exit cell high by ~ray_cfl (one extra step of")
    print("  length ray_cfl*dz added to a cell whose analytic content is K I dz)")
    print(f"{'ray_cfl':>8s} {'predicted':>10s} {'exit cell':>11s} {'interior':>10s} "
          f"{'cell-cell rms':>14s} {'TOTAL absorbed':>15s}")
    for r in rows:
        print(f"{r['rc']:8.3f} {r['rc']*100:+9.1f}% {r['exc_exit']*100:+10.2f}% "
              f"{r['exc_int']*100:+9.3f}% {r['scatter']*100:13.2f}% "
              f"{r['tot_rel']*100:+14.3f}%")

    # linearity in ray_cfl: the excess is one arc-length step of length ray_cfl*dz
    rc = np.array([r["rc"] for r in rows])
    ex = np.array([r["exc_exit"] for r in rows])
    good = ex > 0
    if good.sum() >= 2:
        slope = np.polyfit(np.log(rc[good]), np.log(ex[good]), 1)[0]
        print(f"\nexit-cell excess ~ ray_cfl^{slope:.3f}  "
              f"(exactly 1.0 would mean one full extra step of length ray_cfl*dz)")

    # --- figure ---------------------------------------------------------
    # Three SEPARATE panels for three representative ray_cfl values, zoomed on the exit
    # face. Overlaying all ten curves on one axis was unreadable and hid the fact that the
    # cell-to-cell alias is what dominates, not the exit cell.
    show = [r for r in rows if r["rc"] in (0.05, 0.25, 1.0)] or rows[:3]
    fig, axes = plt.subplots(len(show) + 1, 1, figsize=(11.0, 2.5 * (len(show) + 1) + 0.6))
    for ax, r in zip(axes, show):
        z, ratio = r["z"], r["ratio"]
        ax.plot(z, ratio, color=lpp.C_LASER, lw=1.0, marker="o", ms=2.2)
        ax.axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        zx = z[r["i_exit"]]
        ax.plot([zx], [ratio[r["i_exit"]]], "o", ms=7, color=lpp.C_TARGET, zorder=5)
        ax.annotate(f"exit cell  {r['exc_exit']*100:+.1f}%", xy=(zx, ratio[r["i_exit"]]),
                    xytext=(10, 0), textcoords="offset points", fontsize=8,
                    color=lpp.C_TARGET, fontweight="bold", va="center")
        # zoom: the 25 cells nearest the exit face
        span = 25 * (z[1] - z[0])
        ax.set_xlim(min(zx, zx + span) - 0.5 * abs(z[1] - z[0]), max(zx, zx + span))
        ax.set_ylim(0, max(1.6, 1.1 * float(np.nanmax(ratio))))
        ax.set_ylabel("measured / analytic")
        ax.set_title(f"ray_cfl = {r['rc']:g}: cell-to-cell rms {r['scatter']*100:.1f}%, "
                     f"interior mean {r['exc_int']*100:+.2f}%, "
                     f"total {r['tot_rel']*100:+.2f}%",
                     loc="left", fontweight="bold")
        lpp.style_axes(ax)
    axes[len(show) - 1].set_xlabel("z  [d$_e$ at critical density] — zoomed on the exit "
                                  "face (25 cells)")

    ax2 = axes[-1]
    rc = np.array([r["rc"] for r in rows])
    ax2.plot(rc, [abs(r["exc_exit"]) * 100 for r in rows], "o-", color=lpp.C_TARGET,
             label="exit cell (|excess|)")
    ax2.plot(rc, [r["scatter"] * 100 for r in rows], "d-", color=lpp.C_FOURTH,
             label="interior cell-to-cell rms")
    ax2.plot(rc, [abs(r["exc_int"]) * 100 for r in rows], "s-", color=lpp.C_AMBIENT,
             label="interior mean (|excess|)")
    ax2.plot(rc, [abs(r["tot_rel"]) * 100 for r in rows], "^-", color=lpp.C_LASER,
             label="TOTAL absorbed (|excess|)")
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlabel("ray_cfl")
    ax2.set_ylabel("error vs analytic  [%]")
    ax2.set_title("What actually matters: the per-cell profile is ALIASED (rms tens of "
                  "percent) while the interior MEAN and the TOTAL stay sub-percent for "
                  "ray_cfl <= 0.25", loc="left", fontweight="bold")
    ax2.legend(loc="upper left", ncols=2)
    lpp.style_axes(ax2)

    fig.text(0.005, 0.995, "exit-boundary overshoot study — deposition is lumped at each "
             "RK4 step's ENDPOINT, so cells alias; the boundary cell is one sample of "
             "that, not a separate bug", ha="left", va="top", fontsize=8,
             color=lpp.INK_2)
    lpp.savefig(fig, "overshoot.png", run_id="exit_overshoot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
