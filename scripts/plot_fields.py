#!/usr/bin/env python3
"""Spatial picture of a run: (z,t) streaks, lineouts, and (in 2D) snapshot maps.

The reduced diagnostics say *how much* energy went in and *whether* particles left; this
says **where things are and what they are doing** — the plume expanding, the front
reaching a boundary, a magnetic cavity opening, and (with periodic boundaries) plasma
reappearing at the far end after wrapping.

    python scripts/plot_fields.py runs/<ID>
    python scripts/plot_fields.py runs/<ID> --lineout-times 0 0.5 1.0 2.3

MUST be run with the environment that has yt:

    /opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/<ID>

Writes ``media/<ID>/fields_streak.png`` (n_e, B_y, E_z as (z,t) maps plus the laser's
absorbed-power history on the same time axis) and ``media/<ID>/fields_lineouts.png``
(n_e and B_y profiles at selected times). In 2D it also writes
``media/<ID>/fields_map2d.png``, a snapshot in the x-z plane.

Colour follows the job: density is **sequential** (one hue, light to dark), while
``B_y/B_0`` is **diverging** with a neutral grey midpoint, because it genuinely changes
sign inside a diamagnetic cavity and a sequential map would hide the reversal.
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


def load_series(run_dir, prefix, sc, species):
    """(t[s], z[m], {field: 2D array (nt, nz)}) from a plotfile series.

    In 2D every field is averaged over the transverse axis, so the streak is the on-axis
    (strictly, transversely-averaged) behaviour and 1D/2D streaks are directly comparable.
    """
    import yt

    paths = lpio.plotfiles(run_dir, prefix)
    if not paths:
        return None, None, {}
    want = ["By", "Bx", "Ez", "jz"] + [f"rho_{s}" for s in species]
    t, rows = [], {k: [] for k in want}
    z = None
    for p in paths:
        try:
            ds = yt.load(p)
        except Exception:
            continue
        have = {f[1] for f in ds.field_list}
        # yt refuses a covering_grid flush against a NON-periodic domain edge when the
        # right edge rounds a float ULP outside it. force_periodicity only affects how yt
        # would fetch ghost cells, which a full-domain covering_grid never needs.
        ds.force_periodicity()
        g = ds.covering_grid(0, left_edge=ds.domain_left_edge,
                            dims=ds.domain_dimensions)
        if z is None:
            n = ds.domain_dimensions
            lo, hi = float(ds.domain_left_edge[-1]), float(ds.domain_right_edge[-1])
            # WarpX 1D puts z on axis 0; 2D XZ puts z on axis 1
            nz = int(n[0]) if int(n[1]) == 1 else int(n[1])
            lo = float(ds.domain_left_edge[0]) if int(n[1]) == 1 else \
                float(ds.domain_left_edge[1])
            hi = float(ds.domain_right_edge[0]) if int(n[1]) == 1 else \
                float(ds.domain_right_edge[1])
            z = lo + (np.arange(nz) + 0.5) * (hi - lo) / nz
        t.append(float(ds.current_time))
        for k in want:
            if k not in have:
                rows[k].append(np.zeros_like(z))
                continue
            a = np.asarray(g[("boxlib", k)])
            a = a[:, 0, 0] if a.shape[1] == 1 else a.mean(axis=0)[:, 0]
            rows[k].append(a)
    if not t:
        return None, None, {}
    order = np.argsort(t)
    t = np.asarray(t)[order]
    return t, z, {k: np.asarray(v)[order] for k, v in rows.items() if len(v)}


def electron_density(rows, species, sc):
    """Total electron number density [m^-3] from the per-species charge densities."""
    tot = None
    for s in species:
        if not s.endswith("electrons"):
            continue
        a = rows.get(f"rho_{s}")
        if a is None:
            continue
        n = np.abs(a) / lpp_qe()
        tot = n if tot is None else tot + n
    return tot


def lpp_qe():
    from laserprod.units import QE
    return QE


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--lineout-times", type=float, nargs="*", default=None,
                    help="times in ps for the lineout panel (default: 5 evenly spaced)")
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    from laserprod.deck import _species_table
    species = list(_species_table(cfg))

    t, z, rows = load_series(rd, "diag_fields", sc, species)
    if t is None:
        t, z, rows = load_series(rd, "diag1", sc, species)
    if t is None:
        print(f"no readable plotfiles in {rd}/diags")
        return 1
    z_de = z / sc.de_ref
    t_ps = t * 1e12
    print(f"{rid}: {len(t)} frames, t = {t_ps[0]:.4g}..{t_ps[-1]:.4g} ps, "
          f"{len(z)} cells")

    ne = electron_density(rows, species, sc)
    n_over_ncr = ne / sc.n_cr

    # --- streaks -----------------------------------------------------------
    have_B = sc.B0 is not None
    nrow = 3 if have_B else 2
    fig, axes = plt.subplots(nrow, 1, figsize=(11.5, 3.0 * nrow + 0.8), sharex=True)
    axes = np.atleast_1d(axes)

    im = lpp.streak(axes[0], n_over_ncr, z_de, t_ps, lpp.CMAP_DENSITY,
                    "Electron density — the ablation plume expanding back up the beam",
                    log=True)
    lpp.colorbar(fig, im, axes[0], "n$_e$ / n$_{cr}$")

    k = 1
    if have_B:
        b = rows["By"] / sc.B0
        # Diverging map CENTRED ON 1.0 (undisturbed field), not on the data midpoint:
        # grey = B_0, blue = cavity, orange = compression.
        im = lpp.streak(axes[k], b, z_de, t_ps, lpp.CMAP_DIVERGING,
                        "B$_y$ / B$_0$ — grey is the undisturbed field; BLUE is a "
                        "diamagnetic cavity, ORANGE a compression", center=1.0,
                        clip_pct=99.5)
        lpp.colorbar(fig, im, axes[k], "B$_y$ / B$_0$")
        k += 1

    # E_z is NOT usefully resolved raw: at dz/lambda_D = 61 the grid noise has an rms of
    # ~4e9 V/m, comparable to or above the ambipolar field itself, so an unsmoothed map
    # is a picture of the noise. Boxcar-smooth over NSM cells and say so on the panel.
    NSM = 9
    ez_raw = rows["Ez"]
    ker = np.ones(NSM) / NSM
    ez = np.vstack([np.convolve(row, ker, mode="same") for row in ez_raw])
    rms = float(np.std(ez_raw))
    im = lpp.streak(axes[k], ez, z_de, t_ps, lpp.CMAP_DIVERGING,
                    f"E$_z$ — the ambipolar field, boxcar-smoothed over {NSM} cells. "
                    f"RAW rms is {rms:.2g} V/m at dz/λ$_D$ = "
                    f"{sc.dz_over_lD_targ:.0f}, so the unsmoothed field is mostly grid "
                    f"noise.", symmetric=True, clip_pct=99.5)
    lpp.colorbar(fig, im, axes[k], "E$_z$  [V/m]")

    faces = lpconfig.boundary_faces(cfg)
    ax_bc = faces[str(cfg["geometry"].get("normal_axis", "z"))]
    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    # The pec wall builds a B pile-up that GROWS in time and reaches ~10 d_e in, so mark
    # the near-wall exclusion zone rather than leaving a reader to trust the edges
    # (measured: |B/B0 - 1| up to 2.4 by 2.35 ps, penetrating 6-9 d_e -- RESULTS
    # 2026-07-28).
    WALL_DE = 10.0
    for ax in axes:
        ax.axvline(z_de[-1] if inject_hi else z_de[0], color=lpp.C_LASER, lw=1.6,
                   alpha=0.75)
        if "pec" in str(ax_bc):
            for edge, sgn in ((z_de[0], +1), (z_de[-1], -1)):
                ax.axvspan(edge, edge + sgn * WALL_DE, color=lpp.INK, alpha=0.10,
                           lw=0)
    axes[0].text(z_de[0] + 1.0, 0.97, "pec wall\nexclusion", fontsize=6.5,
                 color=lpp.INK_2, va="top",
                 transform=axes[0].get_xaxis_transform())
    axes[-1].set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]"
                        f"      boundaries: lo={ax_bc[0]}, hi={ax_bc[1]}"
                        f"      green line = laser injection face")
    lpp.stamp(fig, cfg, sc, extra=f"{len(t)} field frames")
    lpp.savefig(fig, "fields_streak.png", run_id=rid)

    # --- lineouts ----------------------------------------------------------
    times = args.lineout_times
    if not times:
        idx = np.linspace(0, len(t) - 1, 5).astype(int)
    else:
        idx = [int(np.argmin(np.abs(t_ps - v))) for v in times]
    nrow2 = 2 if have_B else 1
    fig2, ax2 = plt.subplots(nrow2, 1, figsize=(11.5, 3.4 * nrow2 + 0.6), sharex=True)
    ax2 = np.atleast_1d(ax2)
    # a single-hue sequence encodes TIME (ordered data), not identity
    shades = [lpp.CMAP_LASER(0.25 + 0.7 * j / max(len(idx) - 1, 1))
              for j in range(len(idx))]
    for j, i in enumerate(idx):
        ax2[0].plot(z_de, n_over_ncr[i], color=shades[j], lw=1.6,
                    label=f"{t_ps[i]:.2f} ps")
    ax2[0].axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
    ax2[0].text(0.004, 1.0, " n$_{cr}$", transform=ax2[0].get_yaxis_transform(),
                va="bottom", fontsize=8, color=lpp.INK)
    ax2[0].set_yscale("log")
    ax2[0].set_ylabel("n$_e$ / n$_{cr}$")
    ax2[0].set_title("Electron density lineouts — darker = later", loc="left",
                     fontweight="bold")
    ax2[0].legend(loc="upper left", ncols=len(idx), fontsize=7.5)
    lpp.style_axes(ax2[0])
    if have_B:
        for j, i in enumerate(idx):
            ax2[1].plot(z_de, rows["By"][i] / sc.B0, color=shades[j], lw=1.6)
        ax2[1].axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        ax2[1].text(0.004, 1.0, " B$_0$", transform=ax2[1].get_yaxis_transform(),
                    va="bottom", fontsize=8, color=lpp.INK)
        ax2[1].set_ylabel("B$_y$ / B$_0$")
        ax2[1].set_title("Magnetic field lineouts — below 1 is a cavity, above 1 a "
                         "compression", loc="left", fontweight="bold")
        lpp.style_axes(ax2[1])
    ax2[-1].set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
    lpp.stamp(fig2, cfg, sc)
    lpp.savefig(fig2, "fields_lineouts.png", run_id=rid)

    # --- 2D snapshot map ---------------------------------------------------
    if sc.dims == 2:
        import yt
        paths = lpio.plotfiles(rd, "diag_fields")
        pick = paths[len(paths) // 2], paths[-1]
        fig3, ax3 = plt.subplots(1, 2, figsize=(12.0, 4.4))
        for a, p in zip(ax3, pick):
            ds = yt.load(p)
            g = ds.covering_grid(0, left_edge=ds.domain_left_edge,
                                 dims=ds.domain_dimensions)
            ne2 = sum(np.abs(np.asarray(g[("boxlib", f"rho_{s}")])[:, :, 0])
                      for s in species if s.endswith("electrons")) / lpp_qe()
            xlo, zlo = float(ds.domain_left_edge[0]), float(ds.domain_left_edge[1])
            xhi, zhi = float(ds.domain_right_edge[0]), float(ds.domain_right_edge[1])
            from matplotlib.colors import LogNorm
            pos = ne2[ne2 > 0]
            im = a.imshow((ne2 / sc.n_cr).T, origin="lower", aspect="auto",
                          cmap=lpp.CMAP_DENSITY,
                          norm=LogNorm(vmin=max(pos.min() / sc.n_cr, 1e-5),
                                       vmax=ne2.max() / sc.n_cr),
                          extent=[xlo / sc.de_ref, xhi / sc.de_ref,
                                  zlo / sc.de_ref, zhi / sc.de_ref])
            a.set_xlabel("x  [d$_e$]")
            a.set_ylabel("z  [d$_e$]")
            a.set_title(f"n$_e$/n$_{{cr}}$ at t = {float(ds.current_time)*1e12:.3f} ps",
                        loc="left", fontweight="bold")
            lpp.colorbar(fig3, im, a, "n$_e$ / n$_{cr}$")
        # The caption has to follow the BEAM, not the geometry. For a uniform beam any x
        # dependence is numerical and the reader should distrust it; for a finite spot the
        # x dependence IS the physics and the same words would be actively misleading --
        # which is how a figure caption turns into a retraction.
        beam = (cfg["laser"].get("beam") or {})
        prof = str(beam.get("profile", "uniform"))
        if prof == "uniform":
            cap = ("Transverse structure: a uniform beam on a planar target with periodic "
                   "transverse boundaries should show NONE — any x dependence here is "
                   "numerical.")
        else:
            w0 = float(beam.get("waist_de", 0.0))
            cap = (f"Transverse structure is EXPECTED here: {prof} beam, w$_0$ = {w0:g} "
                   f"d$_e$. The x dependence is the physics — see spot_report.py for the "
                   f"quantitative version, and note the drive is periodic in x with pitch "
                   f"{float(cfg['geometry']['transverse']['hi_de']) - float(cfg['geometry']['transverse']['lo_de']):g} d$_e$.")
        fig3.text(0.005, 0.995, cap, ha="left", va="top", fontsize=8, color=lpp.INK_2)
        lpp.savefig(fig3, "fields_map2d.png", run_id=rid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
