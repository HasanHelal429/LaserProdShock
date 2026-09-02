#!/usr/bin/env python3
"""Campaign-level figures for the Tier 1-3 operator-verification campaign.

    python scripts/tier_figures.py

Writes into ``media/P5/tiers/``. Unlike the per-run tools these summarise ACROSS runs,
because every conclusion the campaign reached is a statement about a SET of runs -- a
single ladder rung, read alone, is exactly how the 2026-08-30 non-convergence was
misread as near-convergence.

Ladder energies are recomputed from each run's own ``LASERDEP`` history rather than
hardcoded, so a re-run of any leg updates the figures. The Tier 2 comparison values are
literals: they come from upstream's analysis scripts and from ACCURACY.md, neither of
which this repo owns.

STYLE. Uses the project's validated categorical slots in their fixed assignment order
(``plotting.py`` documents the validate_palette.js run). Rules kept: no dual axis --
two measures of different scale go in stacked panels sharing an x-axis; status is never
colour alone, always glyph + word; every series is directly labelled as well as
legended, which is the required relief for the low-contrast slots.
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import matplotlib.pyplot as plt              # noqa: E402
from matplotlib.patches import Patch          # noqa: E402
from matplotlib.ticker import NullFormatter   # noqa: E402

from laserprod import config as lpconfig      # noqa: E402
from laserprod import io as lpio              # noqa: E402
from laserprod import plotting as lpp         # noqa: E402

RUNS = os.path.join(lpp.ROOT, "runs", "P5")
FLOOR = 0.80          # % -- measured seed-replicate floor on E_abs (P5_ramp_005 vs 005r)
MEDIA_ID = "P5_tiers"


def eabs(run_id):
    """Final cumulative E_abs from the operator's own tracer, or None if not run."""
    d = os.path.join(RUNS, run_id)
    if not os.path.isfile(os.path.join(d, "run.log")):
        return None
    h = lpio.laserdep_history(d)
    return float(h.Eabs_final) if len(h) else None


def _kill_minor_labels(ax):
    """A log axis keeps drawing its own minor tick labels (3x10^-1, 4x10^-1, ...) on top
    of custom major ticks, which collided illegibly in the first render of both ladder
    figures. Custom ticks mean the minor labels are never wanted."""
    ax.xaxis.set_minor_formatter(NullFormatter())


def _floor_band(ax, label_x=None):
    """The run-to-run floor, drawn as a neutral band -- never a series colour, because
    it is not a series: it is the resolution of the measurement itself."""
    ax.axhspan(-FLOOR, FLOOR, color=lpp.GRID, alpha=0.55, zorder=0, lw=0)
    if label_x is not None:
        ax.annotate(f"seed floor  ±{FLOOR:.2f}%", xy=(label_x, FLOOR), fontsize=7.5,
                    color=lpp.INK_2, va="bottom", ha="right")


# --------------------------------------------------------------------------- #
def fig_drift_vs_resolution():
    """THE headline. Drift is E_abs moving when ONLY ray_cfl changes, so the physics is
    held exactly fixed and what is left is numerics."""
    pairs = [
        ("P5_Ln_010",  "P5_Ln_010_fine",  0.20, "analytic", "$L_n$ = 10 $d_e$"),
        ("P5_ramp_025","P5_ramp_0025",    0.60, "analytic", "$L_n$ = 29.8 $d_e$"),
        ("P5_Ln_060",  "P5_Ln_060_fine",  1.20, "analytic", "$L_n$ = 60 $d_e$"),
        ("P5_raycfl_025","P5_raycfl_0025",0.16, "lifted",   "lifted FLASH"),
    ]
    pts = []
    for coarse, fine, cells, kind, lab in pairs:
        a, b = eabs(coarse), eabs(fine)
        if a and b:
            pts.append((cells, 100 * (b - a) / a, kind, lab))
    if not pts:
        return None
    pts.sort()

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    lpp.style_axes(ax)
    _floor_band(ax, label_x=3.15)

    ax.axvline(1.0, color=lpp.INK_MUTED, lw=1.4, ls=(0, (5, 3)), zorder=1)
    ax.annotate("gate G8\n1 cell", xy=(1.0, -2.6), xytext=(0.93, -2.6),
                fontsize=7.5, color=lpp.INK_2, va="center", ha="right")

    an = [p for p in pts if p[2] == "analytic"]
    li = [p for p in pts if p[2] == "lifted"]
    ax.plot([p[0] for p in an], [p[1] for p in an], "-o", color=lpp.C_LASER,
            markersize=8, markeredgecolor=lpp.SURFACE, markeredgewidth=2, zorder=3,
            label="analytic corona (scale length varied)")
    ax.plot([p[0] for p in li], [p[1] for p in li], "D", color=lpp.C_TARGET,
            markersize=9, markeredgecolor=lpp.SURFACE, markeredgewidth=2, zorder=4,
            label="lifted FLASH table (the P5 spine's IC)")

    for cells, d, kind, lab in pts:
        col = lpp.C_LASER if kind == "analytic" else lpp.C_TARGET
        # the 1.20-cell point sits inside the floor band, where a label centred on the
        # marker would land on the band's own caption -- push that one below instead
        if cells > 1.0:
            va, off, ha = "top", -1.1, "center"
        elif kind == "analytic":
            va, off, ha = "bottom", 0.7, "center"
        else:
            va, off, ha = "top", -0.9, "center"
        ax.annotate(f"{lab}\n{d:+.2f}%", xy=(cells, d), xytext=(cells, d + off),
                    fontsize=7.5, color=col, ha=ha, va=va, fontweight="bold")

    ax.axhline(0, color=lpp.INK_MUTED, lw=0.9, zorder=1)
    ax.set_xscale("log")
    ax.set_xticks([0.16, 0.2, 0.6, 1.2, 3.0])
    ax.set_xticklabels(["0.16", "0.20", "0.60", "1.20", "3.0"])
    _kill_minor_labels(ax)
    ax.set_xlim(0.12, 3.4)
    ax.set_ylim(-5.0, 14.5)
    ax.set_xlabel("cells across the singular layer  (1 − n/n$_{cr}$ < 0.01)")
    ax.set_ylabel("drift in E$_{abs}$ when only ray_cfl changes  [%]\n0.25 → 0.025")
    ax.set_title("Absorbed energy converges only once the grid resolves the critical layer",
                 loc="left", fontweight="bold", color=lpp.INK)
    ax.legend(loc="upper right", fontsize=7.5)
    fig.text(0.005, -0.055,
             "Physics held exactly fixed: within each pair only the arc-length step changes. "
             "Below ~1 cell the march\ndiverges and refining it makes matters worse; at ≳1 cell "
             "it sits in the run-to-run floor. An underdense target,\nwith no critical surface at "
             "all, gives +0.00% — identical to five significant figures.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier3_drift_vs_layer_resolution.png", run_id=MEDIA_ID)


# --------------------------------------------------------------------------- #
def fig_ladders():
    """Four ray_cfl ladders on one frame. Normalised to each ladder's own coarsest rung
    because the absolute E_abs differs by 50% between ICs -- the question is the SHAPE."""
    ladders = [
        ("lifted FLASH, 10 n$_{cr}$", lpp.C_TARGET,
         [("P5_raycfl_050", .50), ("P5_raycfl_025", .25), ("P5_raycfl_010", .10),
          ("P5_raycfl_005", .05), ("P5_raycfl_0025", .025)]),
        ("analytic ramp", lpp.C_AMBIENT,
         [("P5_ramp_050", .50), ("P5_ramp_025", .25), ("P5_ramp_010", .10),
          ("P5_ramp_005", .05), ("P5_ramp_0025", .025)]),
        ("straight rays (refraction = 0)", lpp.C_FOURTH,
         [("P5_straight_025", .25), ("P5_straight_005", .05), ("P5_straight_0025", .025)]),
        ("underdense — no turning point", lpp.C_LASER,
         [("P5_under_025", .25), ("P5_under_005", .05), ("P5_under_0025", .025)]),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    lpp.style_axes(ax)
    _floor_band(ax, label_x=0.30)
    ax.axhline(0, color=lpp.INK_MUTED, lw=0.9, zorder=1)

    for name, col, rungs in ladders:
        xs, ys = [], []
        base = None
        for rid, cfl in rungs:
            E = eabs(rid)
            if E is None:
                continue
            if base is None:
                base = E
            xs.append(cfl); ys.append(100 * (E - base) / base)
        if not xs:
            continue
        ax.plot(xs, ys, "-o", color=col, markersize=6.5, zorder=3,
                markeredgecolor=lpp.SURFACE, markeredgewidth=1.6, label=name)
        # the straight-ray and underdense ladders both end near 0%; nudge them apart
        dy = {"straight rays (refraction = 0)": 0.85,
              "underdense — no turning point": -0.85}.get(name, 0.0)
        lpp.label_line(ax, xs[-1], ys[-1], f" {ys[-1]:+.1f}%", col, dy=dy, ha="left")

    ax.set_xscale("log")
    ax.invert_xaxis()
    ax.set_xticks([.5, .25, .1, .05, .025])
    ax.set_xticklabels(["0.50", "0.25", "0.10", "0.05", "0.025"])
    _kill_minor_labels(ax)
    ax.set_xlim(0.62, 0.0155)
    ax.set_xlabel("ray_cfl        →  finer arc-length step  →")
    ax.set_ylabel("E$_{abs}$ relative to that ladder's coarsest rung  [%]")
    ax.set_title("The same refinement that should converge the march makes it diverge —\n"
                 "but only when a ray has to cross a critical surface",
                 loc="left", fontweight="bold", color=lpp.INK)
    ax.legend(loc="upper left", fontsize=7.5)
    fig.text(0.005, -0.045,
             "A converging ladder flattens to the right. Only the lifted FLASH table runs away "
             "(+18.3%); the underdense\ncontrol is exactly flat (+0.00%, identical to five "
             "significant figures) and the straight-ray mode stays in the floor.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier1_three_ladders.png", run_id=MEDIA_ID)


# --------------------------------------------------------------------------- #
def fig_admissibility():
    """G8 over (FLASH handoff time x dz). Derivable pre-launch, so this whole map costs
    nothing to compute -- which is the point of having the gate at all."""
    handoffs = [("0.1 ns", "P5_flashic"), ("0.2 ns", "P5_flashic_t02"),
                ("0.4 ns", "P5_flashic_t04")]
    dzs = [0.5, 0.25, 0.125]
    M, Ln = np.zeros((len(handoffs), len(dzs))), []
    for i, (_, rid) in enumerate(handoffs):
        cfg = lpconfig.load(os.path.join(RUNS, rid))
        L = lpconfig.critical_scale_length_de(cfg)
        Ln.append(L)
        for j, dz in enumerate(dzs):
            M[i, j] = 0.01 * L / dz

    fig, ax = plt.subplots(figsize=(5.9, 3.3))
    # SEQUENTIAL, one hue light->dark: this is magnitude, not identity.
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=2.2, aspect="auto")
    ax.set_xticks(range(len(dzs)));
    ax.set_xticklabels([f"{d:g}" for d in dzs])
    ax.set_yticks(range(len(handoffs)))
    ax.set_yticklabels([f"{h}\nL$_n$ = {l:.1f} d$_e$" for (h, _), l in zip(handoffs, Ln)])
    for i in range(len(handoffs)):
        for j in range(len(dzs)):
            v = M[i, j]
            ok = v >= 1.0
            # status is never colour alone: glyph + word travel with it
            txt = f"{v:.2f}\n{'✓ PASS' if ok else '✗ sub-grid'}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8.5,
                    fontweight="bold" if ok else "normal",
                    color=lpp.SURFACE if v > 1.15 else lpp.INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("dz  [d$_e$]")
    ax.set_title("Which P5 configurations the ray tracer can actually integrate\n"
                 "cells across the 1 − n/n$_{cr}$ < 0.01 layer  (gate G8)",
                 loc="left", fontweight="bold", color=lpp.INK)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("cells across the layer", fontsize=8)
    cb.ax.tick_params(labelsize=7.5)
    cb.outline.set_visible(False)
    fig.text(0.005, -0.10,
             "A later handoff flattens the corona (~51 d$_e$/ns) but never clears the gate alone: "
             "1 cell at dz = 0.5 needs\nt ≈ 0.87 ns, the end of FLASH's flat top. The two passing "
             "cells cost 145 h and 773 h on one A100,\nagainst a 48 h queue limit — so no converged "
             "full-pulse spine fits in a single job.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier3_admissibility_map.png", run_id=MEDIA_ID)


# --------------------------------------------------------------------------- #
def fig_upstream_agreement():
    """Tier 2: this build against ACCURACY.md, as measured/documented ratios."""
    rows = [
        ("K exponent  n$_e$",              2.0184, 2.0184),
        ("K exponent  Z$_{eff}$",          0.9999, 0.9999),
        ("K exponent  lnΛ",                0.9999, 0.9999),
        ("K exponent  θ$_e$",             -1.4999, -1.4999),
        ("K exponent  λ$_0$",              2.0276, 2.0276),
        ("frozen-K over-absorb  10$^{20}$", 1.33, 1.30),
        ("frozen-K over-absorb  10$^{21}$", 2.84, 2.80),
        ("frozen-K over-absorb  10$^{22}$", 8.54, 8.50),
        ("3D slab circularity",            1.000002, 1.000001),
        ("turning depth @60°  [cells]",    1.40, 1.40),
        ("absorbed fraction @30°",         0.641, 1.0),
        ("absorbed fraction @45°",         0.574, 1.0),
        ("absorbed fraction @60°",         0.630, 1.0),
    ]
    labs = [r[0] for r in rows]
    ratio = [abs(r[1] / r[2]) for r in rows]
    y = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    lpp.style_axes(ax, grid_axis="x")
    ax.axvline(1.0, color=lpp.INK_MUTED, lw=1.4, zorder=1)
    ax.axvspan(0.95, 1.05, color=lpp.GRID, alpha=0.55, zorder=0, lw=0)

    for yy, lab, r in zip(y, labs, ratio):
        agree = 0.95 <= r <= 1.05
        col = lpp.C_AMBIENT if agree else lpp.C_TARGET
        ax.plot([1.0, r], [yy, yy], color=col, lw=2.0, alpha=0.55, zorder=2,
                solid_capstyle="round")
        ax.plot([r], [yy], "o", color=col, markersize=8, zorder=3,
                markeredgecolor=lpp.SURFACE, markeredgewidth=2)
        if not agree:
            ax.annotate(f"  {r:.3f}  ✗ does not reproduce", xy=(r, yy), fontsize=7.5,
                        color=col, va="center", ha="left", fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8)
    ax.set_xlim(0.45, 1.55)
    ax.set_xlabel("measured on this build  ÷  ACCURACY.md baseline")
    ax.set_title("The operator reproduces its own accuracy baselines on Perlmutter CUDA —\n"
                 "except oblique absorption",
                 loc="left", fontweight="bold", color=lpp.INK)
    ax.legend(handles=[Patch(facecolor=lpp.C_AMBIENT, label="reproduces (within 5%)"),
                       Patch(facecolor=lpp.C_TARGET, label="does not reproduce")],
              loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=7.5)
    fig.text(0.005, -0.055,
             "Turning DEPTH is exact to 1.4 cells at 60°, so the geometry is right; the absorbed "
             "FRACTION is 36–43% low\nat every oblique angle while normal incidence agrees to 0.8%. "
             "Not yet called a regression — the baseline may\nhave been taken with refraction = 0. "
             "No P5 leg is oblique; Phase 1's 2D finite-spot legs are.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier2_upstream_agreement.png", run_id=MEDIA_ID)


# --------------------------------------------------------------------------- #
def fig_where_it_breaks():
    """Per-cell deposition difference between the coarsest and finest lifted rungs,
    against local density. Locates the defect rather than merely sizing it."""
    def prof(rid, step="012180"):
        p = os.path.join(RUNS, rid, "diags", f"laserdep_profile_{step}.txt")
        return np.loadtxt(p) if os.path.isfile(p) else None
    A, B = prof("P5_raycfl_025"), prof("P5_raycfl_0025")
    if A is None or B is None:
        return None
    ncr = lpconfig.derive(lpconfig.load(os.path.join(RUNS, "P5_raycfl_025"))).n_cr
    z, ne = A[:, 0], A[:, 1]
    dz = z[1] - z[0]
    d = (B[:, 3] - A[:, 3]) * dz
    r = ne / ncr
    m = (r > 1e-3) & (np.abs(d) > 0)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    lpp.style_axes(ax)
    ax.axhline(0, color=lpp.INK_MUTED, lw=0.9, zorder=1)
    ax.axvline(1.0, color=lpp.INK_MUTED, lw=1.4, ls=(0, (5, 3)), zorder=1)
    ax.annotate("critical surface\nn = n$_{cr}$", xy=(1.0, 0), xytext=(1.35, 5.2e15),
                fontsize=7.5, color=lpp.INK_2, ha="left", va="center")
    ax.scatter(r[m], d[m], s=16, color=lpp.C_TARGET, alpha=0.65, zorder=3,
               edgecolors="none")
    ax.set_xscale("log")
    ax.set_xlabel("local density  n$_e$ / n$_{cr}$")
    ax.set_ylabel("difference in deposited energy\nper cell  [J], finest − coarsest")
    ax.set_title("The disagreement between ladder rungs lives at the turning point,\n"
                 "not at the domain edges",
                 loc="left", fontweight="bold", color=lpp.INK)
    fig.text(0.005, -0.06,
             "Lifted FLASH ladder, ray_cfl 0.25 vs 0.025, at a common dump. A single cell at "
             "n/n$_{cr}$ = 1.03 carries 75% of\nthe whole difference; the first and last five "
             "cells of the domain contribute ~0, which rules out upstream's\nknown "
             "exit-boundary overshoot (Finding 1) as the cause.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier1_where_it_breaks.png", run_id=MEDIA_ID)


# --------------------------------------------------------------------------- #
def fig_energy_closure():
    """The laser-off control. Stacked panels sharing x -- NEVER a dual axis."""
    d = os.path.join(RUNS, "P5_raycfl_off", "diags", "reducedfiles")
    if not os.path.isdir(d):
        return None
    fe = np.loadtxt(os.path.join(d, "FE.txt"), skiprows=1)
    ep = np.loadtxt(os.path.join(d, "EP.txt"), skiprows=1)
    t = fe[:, 1] * 1e12
    F = fe[:, 2:].sum(axis=1)
    K = ep[:, 2:].sum(axis=1)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.3, 4.6), sharex=True,
                                   gridspec_kw={"hspace": 0.16})
    for a in (ax1, ax2):
        lpp.style_axes(a)
    ax1.plot(t, F, color=lpp.C_FOURTH, zorder=3)
    lpp.label_line(ax1, t[-1], F[-1], f"  +{F[-1]:.2e} J", lpp.C_FOURTH)
    ax1.set_ylabel("field energy  [J]")
    ax1.set_title("With the laser off, the field energy grows linearly from zero —\n"
                  "the particles do not heat at all",
                  loc="left", fontweight="bold", color=lpp.INK)

    ax2.plot(t, K - K[0], color=lpp.C_AMBIENT, zorder=3)
    lpp.label_line(ax2, t[-1], K[-1] - K[0], f"  {K[-1]-K[0]:+.2e} J", lpp.C_AMBIENT)
    ax2.axhline(0, color=lpp.INK_MUTED, lw=0.9)
    ax2.set_ylabel("change in kinetic\nenergy  [J]")
    ax2.set_xlabel("time  [ps]")
    for a in (ax1, ax2):                 # room for the direct end labels
        a.set_xlim(t[0], t[-1] * 1.13)
    fig.text(0.005, -0.05,
             "P5_raycfl_off: identical to P5_raycfl_025 but intensity = 0, so no ray is traced and "
             "no energy is supplied.\nIt still gains +3.53e4 J — 34% of what the laser deposits in a "
             "ladder rung — entirely into the FIELD. The long-\nstanding description of this as "
             "particle grid heating had the channel wrong.",
             fontsize=7.2, color=lpp.INK_2, va="top")
    return lpp.savefig(fig, "tier1_energy_closure_control.png", run_id=MEDIA_ID)


def main():
    print("campaign figures -> media/P5/P5_tiers/")
    for fn in (fig_drift_vs_resolution, fig_ladders, fig_admissibility,
               fig_upstream_agreement, fig_where_it_breaks, fig_energy_closure):
        try:
            if fn() is None:
                print(f"  (skipped {fn.__name__}: inputs missing)")
        except Exception as exc:                      # a broken panel must not kill the set
            print(f"  FAILED {fn.__name__}: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
