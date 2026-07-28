#!/usr/bin/env python3
"""Overlay several runs to answer a boundary or geometry question.

Phase 0 is a set of *controlled comparisons*: each run differs from its parent in one
setting, so the evidence is the difference between curves, not any single curve. This
script builds that comparison from plain-text diagnostics only — the reduced diags and
the operator's ``LASERDEP`` lines — so it needs no plotfile reader and works while runs
are still going.

    python scripts/compare_runs.py runs/P0_bc_periodic runs/P0_bc_open
    python scripts/compare_runs.py runs/P0_* --name p0_boundaries

Panels, all sharing a time axis (never a dual y-axis):

1. **Macroparticle number, normalised to t = 0** — the direct boundary signature. With
   periodic boundaries nothing can leave, so the curve is exactly flat; with
   ``open`` (absorbing particles) it must fall as the runaway ablation front exits.
2. **Absorbed fraction f_abs(t)** — whether the boundary choice perturbed the *drive*.
   Two runs that differ only in a boundary must agree here while the plume is far from
   both faces; a divergence from t = 0 means the comparison is not controlled.
3. **Cumulative coupled energy E_abs(t)** from the ray tracer.
4. **Total particle kinetic energy** — with panel 3, this is gate G6: the tracer's
   accounting is immune to grid heating, the particles' is not, so the gap between them
   is the grid-heating budget.

Writes ``media/<name>/compare.png`` (default name: ``compare``).
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402

# Run-identity series use the VALIDATED canonical categorical order (blue, orange, aqua,
# yellow, magenta), assigned in fixed order and never cycled. Validated for the adjacent
# pairlist on the light surface; the sub-3:1 contrast slots are relieved by the direct
# labels every series carries.
RUN_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]


def collect(run_dir):
    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    hist = lpio.laserdep_history(cfg["_run_dir"])
    pn = lpio.reduced_diag(cfg["_run_dir"], "PN")
    t_ke, ke = lpio.particle_energy(cfg["_run_dir"])
    return {
        "id": lpconfig.run_id(cfg),
        "cfg": cfg, "sc": sc, "hist": hist,
        "P_inc": lpio.incident_power(sc, cfg),
        "t_pn": pn.get("time(s)", []),
        "npart": pn.get("total_macroparticles()", []),
        "t_ke": t_ke, "ke": ke,
        "faces": lpconfig.boundary_faces(cfg),
        "steps": lpio.last_step(cfg["_run_dir"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--name", default="compare", help="media/<name>/compare.png")
    args = ap.parse_args()

    runs = []
    for d in args.run_dirs:
        if not os.path.isfile(os.path.join(d, "config.yaml")):
            continue
        try:
            runs.append(collect(d))
        except Exception as exc:                      # keep going on a partial run
            print(f"  skipped {d}: {exc}")
    if len(runs) < 1:
        print("no usable runs")
        return 1
    if len(runs) > len(RUN_COLORS):
        print(f"  NOTE {len(runs)} runs but {len(RUN_COLORS)} validated colour slots; "
              f"plotting the first {len(RUN_COLORS)} and dropping "
              f"{[r['id'] for r in runs[len(RUN_COLORS):]]}")
        runs = runs[:len(RUN_COLORS)]

    import matplotlib.pyplot as plt

    print(f"COMPARING {len(runs)} runs")
    for r in runs:
        ax_faces = r["faces"][str(r["cfg"]["geometry"].get("normal_axis", "z"))]
        n0 = r["npart"][0] if r["npart"] else float("nan")
        n1 = r["npart"][-1] if r["npart"] else float("nan")
        lost = (1.0 - n1 / n0) * 100 if r["npart"] and n0 else float("nan")
        f = r["hist"].f_abs(r["P_inc"])
        print(f"  {r['id']:18s} {r['sc'].dims}D  axis {ax_faces[0]}/{ax_faces[1]:9s} "
              f"steps {r['steps']:6d}  particles lost {lost:6.2f}%  "
              f"f_abs {max(f) if f else float('nan'):.3f}->"
              f"{f[-1] if f else float('nan'):.3f}  "
              f"E_abs {r['hist'].Eabs_final:.4g}")

    fig, axes = plt.subplots(4, 1, figsize=(11.5, 11.0), sharex=True)
    fig.subplots_adjust(hspace=0.38)

    def tag(ax, x, y, text, color, i):
        """Direct label, staggered by series index.

        Curves in a controlled comparison very often coincide (that is usually the
        POINT -- see the f_abs panel), so labels placed at the curve end overlap and
        become unreadable. The stagger is in points, not data units, so it works
        whatever the y-scale is.
        """
        ax.annotate(f" {text}", xy=(x, y), xytext=(4, 9 * (len(runs) - 1 - 2 * i)),
                    textcoords="offset points", color=color, fontsize=8,
                    fontweight="bold", va="center", ha="left",
                    annotation_clip=False)

    for i, r in enumerate(runs):
        c = RUN_COLORS[i]
        lab = r["id"]
        # 1. macroparticle number, normalised
        if r["npart"]:
            t = [v * 1e12 for v in r["t_pn"]]
            y = [v / r["npart"][0] for v in r["npart"]]
            axes[0].plot(t, y, color=c, label=lab)
            tag(axes[0], t[-1], y[-1], lab, c, i)
        # 2. absorbed fraction
        f = r["hist"].f_abs(r["P_inc"])
        if f:
            t = [v * 1e12 for v in r["hist"].t]
            axes[1].plot(t, f, color=c, lw=1.2, label=lab, alpha=0.9)
        # 3. cumulative absorbed energy
        if len(r["hist"]):
            t = [v * 1e12 for v in r["hist"].t]
            axes[2].plot(t, r["hist"].Eabs, color=c, label=lab)
            tag(axes[2], t[-1], r["hist"].Eabs[-1], lab, c, i)
        # 4. particle kinetic energy
        if r["ke"]:
            t = [v * 1e12 for v in r["t_ke"]]
            axes[3].plot(t, r["ke"], color=c, label=lab)
            tag(axes[3], t[-1], r["ke"][-1], lab, c, i)

    axes[0].set_ylabel("N / N(t=0)")
    axes[0].set_title("Macroparticle number — THE boundary signature. Periodic is "
                      "exactly flat (nothing can leave); `open` must fall as the "
                      "runaway front exits.", loc="left", fontweight="bold")
    axes[0].legend(loc="lower left", ncols=2)

    axes[1].set_ylabel("f$_{abs}$")
    axes[1].set_title("Absorbed fraction — runs differing only in a boundary must AGREE "
                      "here while the plume is far from both faces", loc="left",
                      fontweight="bold")

    axes[2].set_ylabel("E$_{abs}$  [J per absent dim]")
    axes[2].set_title("Cumulative coupled energy, measured by the ray tracer "
                      "(grid-heating immune)", loc="left", fontweight="bold")

    axes[3].set_ylabel("particle KE  [J per absent dim]")
    axes[3].set_title("Total particle kinetic energy — with the panel above, this is "
                      "gate G6: the gap is the grid-heating budget", loc="left",
                      fontweight="bold")
    axes[3].set_xlabel("t  [ps]")
    for ax in axes:
        lpp.style_axes(ax)

    ids = ", ".join(r["id"] for r in runs)
    fig.text(0.005, 0.995, f"LaserProdShock comparison  |  {ids}", ha="left", va="top",
             fontsize=8, color=lpp.INK_2)
    lpp.savefig(fig, "compare.png", run_id=args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
