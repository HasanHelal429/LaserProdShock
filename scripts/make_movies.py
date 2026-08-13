#!/usr/bin/env python3
"""Movies of a run: evolving lineouts, ion phase space, and (in 2D) the x-z density map.

A streak shows the whole history at once but compresses each instant to a single row; a
movie does the opposite. For an ablation run the movie is what makes the *mechanism*
legible — the corona lifting off, the rarefaction fan opening, the fast tail running ahead
and then vanishing into an absorbing wall (or reappearing at the far edge, under periodic).

    /opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/<ID>
    ... scripts/make_movies.py runs/<ID> --only fields --fps 12

Writes into ``media/<ID>/``:
  ``movie_fields.mp4``  n_e(z) and B_y(z) lineouts, with the laser history tracking below
  ``movie_phase.mp4``   ion (z, u_z) phase space
  ``movie_map2d.mp4``   n_e(x, z) map (2D runs only)

**AXIS LIMITS ARE FIXED ACROSS ALL FRAMES.** Per-frame autoscaling is the single easiest
way to make a movie useless: a plume that grows by two decades looks stationary if the axis
grows with it. The limits are computed from every frame first, then held.
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


def _laser_curve(cfg, sc, rd):
    """(t_ps, f_abs) for the tracking panel, or (None, None).

    A laser-off control (gate G3) has P_inc = 0, so every f_abs is nan and the tracking
    panel's set_ylim() raises on a NaN limit. The control is a MANDATORY companion to
    every headline run, so return (None, None) and let the caller drop the panel --
    there is no absorbed fraction to track when the drive is off.
    """
    hist = lpio.laserdep_history(rd)
    if not len(hist):
        return None, None
    P = lpio.incident_power(sc, cfg)
    if not P:
        return None, None
    return np.asarray(hist.t) * 1e12, np.asarray(hist.f_abs(P))


def _one_macroparticle_density(cfg):
    """Smallest n_e/n_cr a single ion macroparticle can represent, or None.

    Particles are created down to ``density_min = 1e-4 * nt`` (see ``deck.py``), and a cell
    initialised at ion density ``n_i`` splits it into ``ppc`` particles of weight
    ``n_i dV / ppc``. One such particle alone in a cell therefore deposits an ELECTRON
    density ``Z n_i / ppc``. Using the SMALLEST birth density gives the floor below which
    no whole particle can appear.
    """
    try:
        Z = int(cfg["reference"].get("charge_state", 1))
        ppc = int((cfg["numerics"].get("ppc") or {}).get("target", 0))
        nt = float(cfg["plasma"]["target"]["density_over_ncr"])
    except (KeyError, TypeError, ValueError):
        return None
    if ppc <= 0 or nt <= 0:
        return None
    return Z * 1.0e-4 * nt / ppc


def _contiguous_front(n, z_de, floor, k=5):
    """Furthest z where the density stays above `floor` for `k` CONSECUTIVE cells.

    A density contour is the wrong front for a PIC plume. Out in the tail a single
    macroparticle alone in a cell produces the same density as a fully sampled cell, so the
    contour jumps when one particle crosses a cell boundary and stalls until the next one
    does -- an apparent front advancing in fits and starts that is pure discreteness. A real
    plume edge is CONTIGUOUS, so requiring a run of `k` cells rejects lone particles without
    hiding them or touching the density scale.
    """
    above = n > floor
    if not above.any():
        return float("nan")
    # rightmost index that begins (looking left) a run of k consecutive `above` cells
    run = np.convolve(above.astype(int), np.ones(k, dtype=int), mode="same")
    ok = run >= k
    return float(z_de[ok].max()) if ok.any() else float("nan")


def movie_fields(cfg, sc, rid, rd, fps, keep=False):
    """n_e(z) + B_y(z) lineouts, with f_abs(t) tracking underneath."""
    import matplotlib.pyplot as plt
    from plot_fields import load_series, electron_density
    from laserprod.deck import _species_table

    species = list(_species_table(cfg))
    t, z, rows = load_series(rd, "diag_fields", sc, species)
    if t is None:
        print("  (no diag_fields plotfiles)")
        return None
    z_de, t_ps = z / sc.de_ref, t * 1e12
    ne = electron_density(rows, species, sc) / sc.n_cr
    have_B = sc.B0 is not None
    b = rows["By"] / sc.B0 if have_B else None
    lt, lf = _laser_curve(cfg, sc, rd)

    # --- fixed limits from ALL frames ---
    #
    # THE LOWER LIMIT IS A PHYSICS DECISION, NOT A COSMETIC ONE. A percentile of the
    # nonzero data puts the axis floor wherever the sparsest shape-factor skirt happens to
    # land -- 1e-9 n_cr in a laser-ablation run -- and then a handful of lone macroparticles
    # flying ahead of the plume are drawn with the same visual weight as the plume itself.
    # That is how a PIC discreteness artifact gets read as a physical fast front: the
    # apparent leading edge jumps when one particle crosses into a new cell and stalls
    # between arrivals, which looks exactly like a front advancing in fits and starts.
    #
    # `n_1p` is the smallest density a WHOLE macroparticle can represent: an ion born where
    # the density function was smallest still carries w = n_i dV / ppc, so alone in a cell
    # it deposits Z n_i / ppc. Anything below that is a fraction of one particle spread by
    # the shape factor -- countable noise, not plasma.
    n_1p = _one_macroparticle_density(cfg)
    pos = ne[ne > 0]
    n_lo = max(float(np.percentile(pos, 0.5)), 1e-6)
    if n_1p is not None:
        n_lo = max(n_lo, n_1p / 3.0)      # a little headroom so the floor itself is visible
    n_hi = float(np.nanmax(ne)) * 1.6
    b_lo, b_hi = ((float(np.nanpercentile(b, 0.2)), float(np.nanpercentile(b, 99.8)))
                  if have_B else (0, 1))

    nrow = 3 if have_B else 2
    d = lpp.movie_dir(rid, "fields")
    faces = lpconfig.boundary_faces(cfg)
    ax_bc = faces[str(cfg["geometry"].get("normal_axis", "z"))]
    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    x_in = z_de[-1] if inject_hi else z_de[0]

    for i in range(len(t)):
        fig, axes = plt.subplots(nrow, 1, figsize=(9.6, 2.5 * nrow + 0.5),
                                 sharex=False)
        ax = axes[0]
        if n_1p is not None and n_1p > n_lo:
            # Everything in this band is at most one macroparticle in a cell. Shading it
            # rather than clipping keeps the data honest while removing its visual claim.
            ax.axhspan(n_lo, n_1p, color=lpp.INK, alpha=0.10, lw=0, zorder=0)
            ax.axhline(n_1p, color=lpp.INK, ls="--", lw=0.9, alpha=0.55, zorder=1)
            ax.text(0.004, n_1p, " 1 macroparticle/cell — below: PIC noise",
                    transform=ax.get_yaxis_transform(), va="top", ha="left",
                    fontsize=7, color=lpp.INK, alpha=0.8, zorder=6)
        ax.plot(z_de, ne[i], color=lpp.C_TARGET, lw=1.8)
        if n_1p is not None:
            zf = _contiguous_front(ne[i], z_de, n_1p, k=5)
            if zf == zf:
                ax.axvline(zf, color=lpp.C_LASER, ls="-.", lw=1.2, alpha=0.8, zorder=5)
                ax.text(zf, 0.97, " contiguous front ", transform=ax.get_xaxis_transform(),
                        va="top", ha="left", fontsize=7, color=lpp.C_LASER, alpha=0.9)
        ax.axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        ax.text(0.004, 1.0, " n$_{cr}$", transform=ax.get_yaxis_transform(),
                va="bottom", fontsize=8, color=lpp.INK)
        ax.set_yscale("log")
        ax.set_ylim(n_lo, n_hi)
        ax.set_ylabel("n$_e$ / n$_{cr}$")
        ax.set_title(f"t = {t_ps[i]:6.3f} ps"
                     + (f"   ({t[i]*sc.wci0:5.3f} / ω$_{{ci0}}$)" if sc.wci0 else ""),
                     loc="left", fontweight="bold")
        k = 1
        if have_B:
            axes[k].plot(z_de, b[i], color=lpp.C_AMBIENT, lw=1.8)
            axes[k].axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
            axes[k].set_ylim(b_lo, b_hi)
            axes[k].set_ylabel("B$_y$ / B$_0$")
            k += 1
        for a in axes[:k]:
            a.set_xlim(z_de[0], z_de[-1])
            a.axvline(x_in, color=lpp.C_LASER, lw=1.4, alpha=0.7)
            if "pec" in str(ax_bc):
                for edge, sgn in ((z_de[0], +1), (z_de[-1], -1)):
                    a.axvspan(edge, edge + sgn * 10.0, color=lpp.INK, alpha=0.09, lw=0)
            lpp.style_axes(a)
        axes[k - 1].set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]   "
                               f"(green = laser in; grey = pec-wall exclusion)")

        # tracking panel: the whole laser history with a moving cursor
        axl = axes[-1]
        if lt is not None:
            axl.plot(lt, lf, color=lpp.C_LASER, lw=1.0)
            axl.axvline(t_ps[i], color=lpp.INK, lw=1.4)
            axl.set_xlim(lt[0], lt[-1])
            axl.set_ylim(0, max(1.02 * float(np.nanmax(lf)), 0.05))
            axl.set_ylabel("f$_{abs}$")
        axl.set_xlabel("t  [ps]")
        lpp.style_axes(axl)

        lpp.stamp(fig, cfg, sc, extra=f"frame {i+1}/{len(t)}")
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=100,
                    bbox_inches="tight", facecolor=lpp.SURFACE)
        plt.close(fig)
    return lpp.encode(d, os.path.join(lpp.media_dir(run_id=rid), "movie_fields.mp4"),
                      fps=fps, cleanup=not keep)


def movie_phase(cfg, sc, rid, rd, fps, keep=False):
    """Ion (z, u_z) phase space, additive two-colour."""
    import matplotlib.pyplot as plt
    import yt
    from laserprod.deck import _species_table
    from phase_space import _asinh, _hex, species_uz

    ions = [s for s in _species_table(cfg) if s.endswith("ions")]
    paths = lpio.plotfiles(rd, "diag_phase")
    if not paths:
        # Fall back to the full plotfile series. `diag_phase` is a trimmed particle dump
        # written at its own cadence, but `diag1` carries position, momentum and weight
        # too, so phase space is recoverable without re-running. A hybrid deck in
        # particular has no reason to declare `phase_intervals` -- it has no electron
        # macroparticles -- yet its IONS are still particles and are exactly what a fast
        # tail would show up in.
        paths = lpio.plotfiles(rd, "diag1")
        if paths:
            print(f"  (no diag_phase; using {len(paths)} diag1 plotfiles for phase space)")
    if not paths:
        print("  (no plotfiles with particle data)")
        return None
    vunit, vname = ((sc.vA, "v$_A$") if sc.vA else (sc.Cs_targ, "C$_s$(target)"))

    # pass 1: gather everything, so the velocity axis can be fixed
    frames, vmax = [], 1.0
    for p in paths:
        ds = yt.load(p)
        axis_last = 0 if int(ds.domain_dimensions[1]) == 1 else 1
        data = {}
        for s in ions:
            z, uz, w = species_uz(ds, s, axis_last)
            if z.size:
                v = uz / sc.mi / vunit
                data[s] = (z / sc.de_ref, v, w)
                vmax = max(vmax, float(np.percentile(np.abs(v), 99.95)))
        frames.append((float(ds.current_time), data))

    z_edges = np.linspace(sc.domain_lo / sc.de_ref, sc.domain_hi / sc.de_ref, 300)
    v_edges = np.linspace(-0.5 * vmax, 1.05 * vmax, 240)
    d = lpp.movie_dir(rid, "phase")
    bc = lpconfig.boundary_faces(cfg)[str(cfg["geometry"].get("normal_axis", "z"))]

    for i, (tt, data) in enumerate(frames):
        fig, ax = plt.subplots(figsize=(9.6, 4.2))
        rgb = np.zeros((len(v_edges) - 1, len(z_edges) - 1, 3))
        for s, (z, v, w) in data.items():
            H, _, _ = np.histogram2d(z, v, bins=[z_edges, v_edges], weights=w)
            rgb += _asinh(H).T[..., None] * np.asarray(
                _hex(lpp.C_TARGET if s.startswith("targ") else lpp.C_AMBIENT))
        ax.imshow(np.clip(rgb, 0, 1), origin="lower", aspect="auto",
                  interpolation="nearest",
                  extent=[z_edges[0], z_edges[-1], v_edges[0], v_edges[-1]])
        ax.set_facecolor("#0b0b12")
        ax.axhline(0.0, color="w", ls=":", lw=0.8, alpha=0.5)
        ax.set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
        ax.set_ylabel(f"u$_z$  [{vname}]")
        ax.set_title(f"t = {tt*1e12:6.3f} ps   —   ion phase space, axis "
                     f"{bc[0]}/{bc[1]}", loc="left", fontweight="bold")
        for j, s in enumerate(dict.fromkeys(ions)):
            if s in data:
                ax.text(0.015 + 0.125 * j, 0.95, s, transform=ax.transAxes,
                        color=lpp.C_TARGET if s.startswith("targ") else lpp.C_AMBIENT,
                        fontsize=8, fontweight="bold", va="top")
        lpp.stamp(fig, cfg, sc, extra=f"frame {i+1}/{len(frames)}")
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=100,
                    bbox_inches="tight", facecolor=lpp.SURFACE)
        plt.close(fig)
    return lpp.encode(d, os.path.join(lpp.media_dir(run_id=rid), "movie_phase.mp4"),
                      fps=fps, cleanup=not keep)


def movie_map2d(cfg, sc, rid, rd, fps, keep=False):
    """n_e(x, z) map for a 2D run."""
    import matplotlib.pyplot as plt
    import yt
    from matplotlib.colors import LogNorm
    from laserprod.deck import _species_table
    from laserprod.units import QE

    species = [s for s in _species_table(cfg) if s.endswith("electrons")]
    paths = lpio.plotfiles(rd, "diag_fields")
    if not paths:
        return None
    maps, extent, vlo, vhi = [], None, np.inf, 0.0
    for p in paths:
        ds = yt.load(p)
        ds.force_periodicity()      # see plot_fields.load_series
        g = ds.covering_grid(0, left_edge=ds.domain_left_edge,
                             dims=ds.domain_dimensions)
        ne = sum(np.abs(np.asarray(g[("boxlib", f"rho_{s}")])[:, :, 0])
                 for s in species) / QE / sc.n_cr
        if extent is None:
            extent = [float(ds.domain_left_edge[0]) / sc.de_ref,
                      float(ds.domain_right_edge[0]) / sc.de_ref,
                      float(ds.domain_left_edge[1]) / sc.de_ref,
                      float(ds.domain_right_edge[1]) / sc.de_ref]
        pos = ne[ne > 0]
        if pos.size:
            vlo = min(vlo, float(np.percentile(pos, 1)))
        vhi = max(vhi, float(ne.max()))
        maps.append((float(ds.current_time), ne))
    d = lpp.movie_dir(rid, "map2d")
    norm = LogNorm(vmin=max(vlo, 1e-5), vmax=vhi)
    tbc = lpconfig.boundary_faces(cfg)["x"]
    for i, (tt, ne) in enumerate(maps):
        fig, ax = plt.subplots(figsize=(6.4, 7.2))
        im = ax.imshow(ne.T, origin="lower", aspect="auto", cmap=lpp.CMAP_DENSITY,
                       norm=norm, extent=extent)
        ax.set_xlabel(f"x  [d$_e$]   (transverse {tbc[0]}/{tbc[1]})")
        ax.set_ylabel("z  [d$_e$]")
        ax.set_title(f"t = {tt*1e12:6.3f} ps", loc="left", fontweight="bold")
        lpp.colorbar(fig, im, ax, "n$_e$ / n$_{cr}$")
        lpp.stamp(fig, cfg, sc, extra=f"frame {i+1}/{len(maps)}")
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=100,
                    bbox_inches="tight", facecolor=lpp.SURFACE)
        plt.close(fig)
    return lpp.encode(d, os.path.join(lpp.media_dir(run_id=rid), "movie_map2d.mp4"),
                      fps=fps, cleanup=not keep)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--only", choices=["fields", "phase", "map2d"], default=None)
    ap.add_argument("--keep-frames", action="store_true",
                    help="keep the per-frame PNGs after encoding (for debugging a bad "
                         "movie); by default they are deleted, since they are a build "
                         "artifact of the mp4 and much larger than it")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling scripts
    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    print(f"{rid}: making movies at {args.fps} fps")

    # Leftovers from an interrupted run would otherwise be silently spliced into a new
    # movie by ffmpeg's frame globbing, and would accumulate on disk.
    stale = lpp.cleanup_frame_dirs(rid)
    if stale:
        print(f"  removed {len(stale)} leftover frame director"
              f"{'y' if len(stale) == 1 else 'ies'} from an earlier run")

    keep = args.keep_frames
    want = {args.only} if args.only else {"fields", "phase", "map2d"}
    # `encode` only deletes frames after a SUCCESSFUL ffmpeg run (deliberately -- on an
    # ffmpeg failure the frames are the only evidence). But a crash while *building* the
    # frames left them behind too, which broke the auto-removal rule: a laser-off control
    # crashed in the tracking panel and stranded 81 PNGs. Sweep on the way out as well.
    try:
        if "fields" in want:
            movie_fields(cfg, sc, rid, rd, args.fps, keep)
        if "phase" in want:
            movie_phase(cfg, sc, rid, rd, args.fps, keep)
        if "map2d" in want and sc.dims == 2:
            movie_map2d(cfg, sc, rid, rd, args.fps, keep)
    except BaseException:
        if not keep:
            left = lpp.cleanup_frame_dirs(rid)
            if left:
                print(f"  cleaned up {len(left)} frame director"
                      f"{'y' if len(left) == 1 else 'ies'} after the failure "
                      f"(--keep-frames to retain them)")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
