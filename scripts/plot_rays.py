#!/usr/bin/env python3
"""Ray paths: where the beam actually goes, and where it turns around.

Every other laser diagnostic here reports where energy *landed* -- `laser_report.py` the
per-cell profile, `spot_report.py` its transverse moments. None of them shows the **paths**
that carried it, which is why both operator bugs found so far (the transverse index clamp
and the exit-boundary overshoot) had to be inferred from spatial profiles rather than seen.
This traces the rays themselves: refraction through the density gradient, the turning point
at the critical surface, and the specular outbound leg.

    /opt/anaconda3/envs/physics/bin/python scripts/plot_rays.py runs/<phase>/<ID>
    ... scripts/plot_rays.py runs/<phase>/<ID> --time 5.0 --rays 40

Writes ``media/<ID>/rays.png``.

**This is an offline RECONSTRUCTION, not the operator's own output.** It re-integrates the
same eikonal equation (`d/ds(n dr/ds) = grad n`, `n = sqrt(1 - n_e/n_cr)`) with the same RK4
marcher, the same multilinear sampling, the same `n_floor` reflect threshold and the same
wrap/clamp index mapping as `Source/Particles/LaserDeposition/LaserDeposition.cpp`, on the
`n_e` a plotfile dumped. So it shows **what the equations say the rays do** on that density
field. Agreement with the operator's own ray dump is a real check on the operator; a
disagreement is a bug in one of the two, and this script is not automatically the wrong one.

**It does NOT reproduce absorption.** The IB coefficient needs the per-cell `T_e` the
operator builds from the electron momentum moments, which is not in the plotfiles, so no
optical depth is carried and no ray is extinguished. Consequences, both of which matter for
reading the figure:

- The outbound leg is drawn for every ray that turns. In an optically thick run the real ray
  is extinguished at or before the turning point and never flies it. Treat the outbound leg
  as *the path it would take*, not evidence that power came back out. `laser_report.py`'s
  `f_abs` is what says whether anything survives the turn.
- Ray termination here is geometric only: a ray ends when it leaves the domain through a
  face it does not wrap around.

Both are honest for the question this figure answers -- *where does the beam go and where
does it turn* -- and neither may be used to infer an absorbed fraction.
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

# The operator's refractive-index reflect floor (LaserDeposition.cpp: `n_floor`). A ray is
# turned when n_ref drops to it, which is the numerical stand-in for reaching critical.
N_FLOOR = 1.0e-2


class Field:
    """The gathered density field, sampled exactly as the operator samples it.

    Multilinear interpolation of `n_e` at cell centres, with the gradient taken from the
    same weights (not a separate finite difference), and `map_index`'s wrap-or-clamp at the
    edges. `n_ref = sqrt(max(1 - n_e/n_cr, n_floor^2))` and
    `grad n_ref = -grad n_e / (2 n_cr n_ref)`.
    """

    def __init__(self, ne, plo, phi, dx, wrap, n_cr):
        self.ne = np.asarray(ne, dtype=float)      # (n0, n1), index order = plotfile order
        self.plo = np.asarray(plo, dtype=float)
        self.phi = np.asarray(phi, dtype=float)
        self.dx = np.asarray(dx, dtype=float)
        self.dxi = 1.0 / self.dx
        self.wrap = list(wrap)
        self.n_cr = float(n_cr)
        self.n = np.array(self.ne.shape, dtype=int)

    def _map(self, ii, d):
        if self.wrap[d]:
            return np.mod(ii, self.n[d])
        return np.clip(ii, 0, self.n[d] - 1)

    def sample(self, c):
        """(n_e, n_ref, grad n_ref) at positions `c`, shape (N, 2)."""
        g = (c - self.plo) * self.dxi - 0.5
        i0 = np.floor(g).astype(int)
        fr = g - i0
        N = c.shape[0]
        ne = np.zeros(N)
        gne = np.zeros((N, 2))
        for corner in range(4):
            bits = [(corner >> d) & 1 for d in range(2)]
            idx = [self._map(i0[:, d] + bits[d], d) for d in range(2)]
            val = self.ne[idx[0], idx[1]]
            w = np.ones(N)
            for d in range(2):
                w *= fr[:, d] if bits[d] else (1.0 - fr[:, d])
            ne += val * w
            for d in range(2):
                wd = np.ones(N)
                for e in range(2):
                    if e == d:
                        continue
                    wd *= fr[:, e] if bits[e] else (1.0 - fr[:, e])
                gne[:, d] += val * wd * (self.dxi[d] if bits[d] else -self.dxi[d])
        r = ne / self.n_cr
        n_ref = np.sqrt(np.maximum(1.0 - r, N_FLOOR * N_FLOOR))
        grad = -gne / (2.0 * self.n_cr * n_ref)[:, None]
        return ne, n_ref, grad


def _rk4(field, c, T, h):
    """One RK4 step of the eikonal system, as the operator's `rk4` lambda does it."""
    _, nref, g = field.sample(c)
    dc1, dT1 = T / nref[:, None], g
    ct, Tt = c + 0.5 * h * dc1, T + 0.5 * h * dT1
    _, nref, g = field.sample(ct)
    dc2, dT2 = Tt / nref[:, None], g
    ct, Tt = c + 0.5 * h * dc2, T + 0.5 * h * dT2
    _, nref, g = field.sample(ct)
    dc3, dT3 = Tt / nref[:, None], g
    ct, Tt = c + h * dc3, T + h * dT3
    _, nref, g = field.sample(ct)
    dc4, dT4 = Tt / nref[:, None], g
    c = c + (h / 6.0) * (dc1 + 2 * dc2 + 2 * dc3 + dc4)
    T = T + (h / 6.0) * (dT1 + 2 * dT2 + 2 * dT3 + dT4)
    return c, T


def trace(field, c0, u0, h, max_steps):
    """March the bundle. Returns (paths (S, N, 2), turn_step per ray, n_turns per ray).

    Mirrors `trace_ray`: turn when `n_ref <= n_floor` *and* the ray is still climbing
    (`drds > 0`, which is what stops it being re-trapped on the outbound leg), specular
    reflection about `grad n_ref`, rewind to the pre-step position, and terminate on leaving
    the domain through any non-wrapping face.
    """
    N = c0.shape[0]
    c = c0.copy()
    _, nref0, _ = field.sample(c)
    T = nref0[:, None] * u0

    paths = np.full((max_steps + 1, N, 2), np.nan)
    paths[0] = c
    turns = [[] for _ in range(N)]
    active = np.ones(N, dtype=bool)
    r_prev = field.sample(c)[0] / field.n_cr

    for istep in range(max_steps):
        if not active.any():
            break
        c_old = c.copy()
        idx = np.flatnonzero(active)
        cn, Tn = _rk4(field, c[idx], T[idx], h)
        c[idx], T[idx] = cn, Tn

        ne, nref, g = field.sample(c)
        r_cur = ne / field.n_cr
        drds = (r_cur - r_prev) / h

        hit = active & (nref <= N_FLOOR) & (drds > 0.0)
        if hit.any():
            hi = np.flatnonzero(hit)
            gm2 = (g[hi] ** 2).sum(axis=1)
            Tdg = (T[hi] * g[hi]).sum(axis=1)
            ok = gm2 > 0.0
            f = np.where(ok, 2.0 * Tdg / np.where(ok, gm2, 1.0), 0.0)
            T[hi] = np.where(ok[:, None], T[hi] - f[:, None] * g[hi], -T[hi])
            # Nudge back into the underdense region, as the operator does.
            c[hi] = c_old[hi]
            for j in hi:
                turns[j].append(istep)

        upd = ne > 0.0
        r_prev = np.where(upd, r_cur, r_prev)

        paths[istep + 1] = np.where(active[:, None], c, np.nan)

        escaped = np.zeros(N, dtype=bool)
        for d in range(2):
            if field.wrap[d]:
                continue
            escaped |= (c[:, d] < field.plo[d]) | (c[:, d] > field.phi[d])
        active &= ~escaped

    return paths, turns


def read_dump(path):
    """Parse a `laserdep_rays_<step>.txt` written by the operator itself.

    Columns are `iray istep x z P ne turned` in 2D (the header names them). Returns
    `{iray: (M, 5) array of x, z, P, ne, turned}` with rows in march order, which is the
    order the file is written in.
    """
    rows = np.loadtxt(path, comments="#")
    if rows.ndim == 1:
        rows = rows[None, :]
    out = {}
    for r in np.unique(rows[:, 0]).astype(int):
        sel = rows[rows[:, 0] == r]
        out[int(r)] = sel[:, 2:]
    return out


def turning_points(tracks, axis=1):
    """Indices where each ray reverses along the axis — the real turning points.

    NOT the same thing as the operator's explicit near-critical branch, and this distinction
    caught a wrong figure while this script was being written. That branch fires only at
    `n_ref <= n_floor`, i.e. within 1e-4 of critical; at normal incidence a ray decelerating
    in the density gradient is turned by ordinary refraction *before* it gets that close (in
    `P1_vac_2d_spot_omp` it reverses at 0.98 n_cr and never enters the branch at all).
    Counting only the branch reports "1 of 25 rays turned" for a bundle in which almost every
    ray turns. A sign change in the axial direction is what a reader means by a turn.
    """
    out = []
    for k in range(tracks.shape[1]):
        z = tracks[:, k, axis]
        good = np.flatnonzero(~np.isnan(z))
        if good.size < 3:
            out.append([])
            continue
        zz = z[good]
        dz = np.diff(zz)
        sign = np.sign(dz)
        nz = sign != 0
        if not nz.any():
            out.append([])
            continue
        s = sign[nz]
        idx = good[:-1][nz]
        flips = np.flatnonzero(s[1:] * s[:-1] < 0)
        out.append([int(idx[i + 1]) for i in flips])
    return out


def wrap_for_plot(track, lo, hi):
    """Wrap a periodic coordinate into [lo, hi) and break the line where it jumps.

    The march keeps `c` continuous and wraps only its field *indices*, so a ray that crosses
    a periodic transverse face keeps running off in a straight line. Drawing that literally
    puts rays outside the box; drawing it wrapped without a break draws a spurious horizontal
    line across the figure. Break it.
    """
    span = hi - lo
    w = lo + np.mod(track - lo, span)
    jump = np.abs(np.diff(w, axis=0)) > 0.5 * span
    w = w.copy()
    w[:-1][jump] = np.nan
    return w


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--time", type=float, nargs="*", default=None,
                    help="times in ps to trace (default: the middle and last dumps)")
    ap.add_argument("--rays", type=int, default=25,
                    help="rays to draw, spread over the launch face (0 = every ray)")
    ap.add_argument("--max-steps", type=int, default=0,
                    help="cap the march (0 = the operator's own 6*L/h + 100)")
    ap.add_argument("--dump", default=None,
                    help="a laserdep_rays_<step>.txt written by the operator "
                         "(laser_deposition.ray_intervals): overlay it on the "
                         "reconstruction and report where the two disagree")
    args = ap.parse_args()

    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    import yt

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    if sc.dims != 2:
        print(f"{rid}: plot_rays needs a 2D run (this one is {sc.dims}D); in 1D the ray "
              f"path is the z axis and laser_report.py already shows the profile.")
        return 1

    from laserprod.deck import _species_table
    species = [s for s in _species_table(cfg) if s.endswith("electrons")]

    paths_avail = lpio.plotfiles(rd, "diag_fields")
    if not paths_avail:
        print(f"no diag_fields plotfiles in {rd}/diags")
        return 1

    las = cfg["laser"]
    beam = (las.get("beam") or {})
    inject_hi = str(las.get("inject_side", "lo")) == "hi"
    ang = np.radians(float(las.get("incidence_angle_deg", 0.0)))
    ray_cfl = float(las.get("ray_cfl", 0.25))
    rpc = int(beam.get("rays_per_cell", 1) or 1)
    profile = str(beam.get("profile", "uniform"))
    w0_de = float(beam.get("waist_de", 0.0) or 0.0)

    faces = lpconfig.boundary_faces(cfg)
    tname = [k for k in faces if k != str(cfg["geometry"].get("normal_axis", "z"))]
    t_periodic = bool(tname) and "periodic" in str(faces[tname[0]])

    # pick dumps
    times = [float(yt.load(p).current_time) * 1e12 for p in paths_avail]
    if args.time:
        pick = [int(np.argmin(np.abs(np.asarray(times) - v))) for v in args.time]
    else:
        pick = [len(paths_avail) // 2, len(paths_avail) - 1]
    pick = sorted(set(pick))

    fig, axes = plt.subplots(1, len(pick), figsize=(6.2 * len(pick), 5.0), squeeze=False)
    axes = axes[0]

    for ax, ip in zip(axes, pick):
        ds = yt.load(paths_avail[ip])
        ds.force_periodicity()
        grid = ds.covering_grid(0, left_edge=ds.domain_left_edge,
                                dims=ds.domain_dimensions)
        from laserprod.units import QE
        ne = sum(np.abs(np.asarray(grid[("boxlib", f"rho_{s}")])[:, :, 0])
                 for s in species) / QE            # (nx, nz)

        plo = np.array([float(ds.domain_left_edge[0]), float(ds.domain_left_edge[1])])
        phi = np.array([float(ds.domain_right_edge[0]), float(ds.domain_right_edge[1])])
        nx, nz = ne.shape
        dx = np.array([(phi[0] - plo[0]) / nx, (phi[1] - plo[1]) / nz])
        # dim 0 = transverse (x, may be periodic), dim 1 = axis (z, never wraps)
        field = Field(ne, plo, phi, dx, [t_periodic, False], sc.n_cr)

        h = ray_cfl * float(dx.min())
        max_steps = args.max_steps or int(6.0 * float((phi - plo).sum()) / h) + 100

        # Launch face and bundle, as the operator lays it out: one ray per transverse cell,
        # subdivided rays_per_cell times, at the sub-cell centre.
        n_launch = nx * rpc
        j = np.arange(n_launch)
        xs = plo[0] + (j // rpc + ((j % rpc) + 0.5) / rpc) * dx[0]
        if args.rays and args.rays < n_launch:
            sel = np.unique(np.linspace(0, n_launch - 1, args.rays).astype(int))
            xs = xs[sel]
        c0 = np.stack([xs, np.full_like(xs, phi[1] if inject_hi else plo[1])], axis=1)
        u0 = np.zeros_like(c0)
        u0[:, 1] = (-1.0 if inject_hi else 1.0) * np.cos(ang)
        u0[:, 0] = np.sin(ang)

        tracks, turns = trace(field, c0, u0, h, max_steps)

        # background density
        pos = ne[ne > 0]
        im = ax.imshow((ne / sc.n_cr).T, origin="lower", aspect="auto",
                       cmap=lpp.CMAP_DENSITY,
                       norm=LogNorm(vmin=max(pos.min() / sc.n_cr, 1e-5) if pos.size else 1e-5,
                                    vmax=(ne.max() / sc.n_cr) if ne.size else 1.0),
                       extent=[plo[0] / sc.de_ref, phi[0] / sc.de_ref,
                               plo[1] / sc.de_ref, phi[1] / sc.de_ref])
        lpp.colorbar(fig, im, ax, "n$_e$ / n$_{cr}$")

        # the critical surface the rays actually turn on
        xc = plo[0] + (np.arange(nx) + 0.5) * dx[0]
        zc = plo[1] + (np.arange(nz) + 0.5) * dx[1]
        n_m = sc.n_cr * np.cos(ang) ** 2
        if ne.max() > n_m:
            ax.contour(xc / sc.de_ref, zc / sc.de_ref, (ne / n_m).T, levels=[1.0],
                       colors=[lpp.INK], linewidths=1.2, linestyles="--")

        # Ray paths, split at the first turning point. Inbound and outbound have to be
        # visually separable or the bundle is just a thicket of green: the whole point of
        # the figure is telling the leg that carries power in from the leg that comes back.
        geo_all = turning_points(tracks)
        X = tracks[:, :, 0] / sc.de_ref
        Z = tracks[:, :, 1] / sc.de_ref
        if t_periodic:
            X = wrap_for_plot(X, plo[0] / sc.de_ref, phi[0] / sc.de_ref)
        for k in range(tracks.shape[1]):
            s0 = geo_all[k][0] if geo_all[k] else None
            if s0 is None:
                ax.plot(X[:, k], Z[:, k], color=lpp.C_LASER, lw=0.8, alpha=0.7)
            else:
                ax.plot(X[:s0 + 1, k], Z[:s0 + 1, k],
                        color=lpp.C_LASER, lw=0.8, alpha=0.7)
                ax.plot(X[s0:, k], Z[s0:, k], color=lpp.C_AMBIENT, lw=0.7,
                        alpha=0.55, ls="--")
        from matplotlib.lines import Line2D
        leg_handles = [
            Line2D([], [], color=lpp.C_LASER, lw=1.4, label="inbound"),
            Line2D([], [], color=lpp.C_AMBIENT, lw=1.4, ls="--", label="outbound"),
        ]

        # Turning points: the geometric reversal, plus the operator's explicit
        # near-critical specular branch reported separately (they are not the same event).
        geo = geo_all
        tx, tz = [], []
        for k, steps in enumerate(geo):
            for s in steps:
                tx.append(tracks[s, k, 0] / sc.de_ref)
                tz.append(tracks[s, k, 1] / sc.de_ref)
        if tx:
            txp = np.asarray(tx)
            if t_periodic:
                span = (phi[0] - plo[0]) / sc.de_ref
                txp = plo[0] / sc.de_ref + np.mod(txp - plo[0] / sc.de_ref, span)
            ax.scatter(txp, tz, s=16, color=lpp.INK, zorder=5, marker="o",
                       edgecolors="none")
            leg_handles.append(Line2D([], [], color=lpp.INK, marker="o", ls="none",
                                      ms=4, label=f"turning point ({len(tx)})"))

        # The operator's own paths, if we were given them. This is the whole point of
        # having both: the reconstruction says what the equations imply on this density
        # field, the dump says what the march actually did, and a gap between them is a
        # bug in one of the two.
        if args.dump:
            dump = read_dump(args.dump)
            dxs, dzs = [], []
            for r, arr in dump.items():
                xr = arr[:, 0] / sc.de_ref
                zr = arr[:, 1] / sc.de_ref
                if t_periodic:
                    xr = wrap_for_plot(xr[:, None], plo[0] / sc.de_ref,
                                       phi[0] / sc.de_ref)[:, 0]
                ax.plot(xr, zr, color="#b5179e", lw=0.9, alpha=0.8, zorder=4)
                dzs.append(np.nanmin(zr))
                dxs.append(xr[0])
            leg_handles.append(Line2D([], [], color="#b5179e", lw=1.4,
                                      label=f"operator dump ({len(dump)})"))
            # Compare the one number both sides agree on the meaning of: how deep each
            # ray got. Match by launch position, which is where the bundles coincide.
            rec_deep = {float(c0[k, 0] / sc.de_ref): np.nanmin(Z[:, k])
                        for k in range(tracks.shape[1])}
            if rec_deep and dzs:
                keys = np.array(list(rec_deep.keys()))
                dev = []
                for x0, zd in zip(dxs, dzs):
                    kk = keys[np.argmin(np.abs(keys - x0))]
                    dev.append(abs(rec_deep[kk] - zd))
                print(f"    vs operator dump: {len(dump)} rays, deepest-z "
                      f"|reconstruction - operator| max {max(dev):.3g} d_e, "
                      f"median {np.median(dev):.3g} d_e")

        n_turned = sum(1 for s in geo if s)
        n_spec = sum(1 for s in turns if s)

        # How deep the bundle gets, in the units that decide the physics.
        pen = []
        for k in range(tracks.shape[1]):
            pts = tracks[~np.isnan(tracks[:, k, 0]), k, :]
            if pts.size:
                pen.append(field.sample(pts)[0].max() / sc.n_cr)
        pen_max = max(pen) if pen else float("nan")
        ax.axhline(phi[1] / sc.de_ref if inject_hi else plo[1] / sc.de_ref,
                   color=lpp.C_LASER, lw=2.0, alpha=0.85)
        # Crop to the interaction region. Most of this domain is opaque target below and
        # empty vacuum above, and showing all 1100 d_e of it squeezes the corona -- where
        # every ray actually bends -- into a few pixels.
        zc_de = zc / sc.de_ref
        lit = np.flatnonzero(ne.max(axis=0) > 1e-4 * sc.n_cr)
        z_top = zc_de[lit].max() if lit.size else phi[1] / sc.de_ref
        z_bot = min(tz) if tz else (zc_de[lit].min() if lit.size else plo[1] / sc.de_ref)
        pad = max(0.12 * (z_top - z_bot), 25.0)
        ax.set_xlim(plo[0] / sc.de_ref, phi[0] / sc.de_ref)
        ax.set_ylim(max(z_bot - pad, plo[1] / sc.de_ref),
                    min(z_top + pad, phi[1] / sc.de_ref))
        ax.set_xlabel("x  [d$_e$]")
        ax.set_ylabel("z  [d$_e$]      (cropped to the interaction region)")
        ax.set_title(f"t = {times[ip]:.3f} ps — {len(xs)} rays, {n_turned} turn back; "
                     f"deepest reaches {pen_max:.3f} n$_{{cr}}$",
                     loc="left", fontweight="bold")
        ax.legend(handles=leg_handles, loc="upper left", fontsize=7.5, framealpha=0.9)
        lpp.style_axes(ax)

        print(f"  t = {times[ip]:8.3f} ps   rays {len(xs):4d}   turned {n_turned:4d}   "
              f"specular-branch {n_spec:4d}   deepest {pen_max:.4f} n_cr   "
              f"h = {h / sc.de_ref:.4g} d_e")

    beam_bit = (f"  Beam: {profile}, w$_0$ = {w0_de:g} d$_e$."
                if profile != "uniform" else "")
    cap = (
        "Ray paths RECONSTRUCTED OFFLINE from the dumped n$_e$, using the operator's own "
        "eikonal march, multilinear sampling and wrap/clamp index mapping — not the "
        "operator's output.\n"
        "Dashed black = the critical surface the rays turn on. NO absorption is carried "
        "here: the outbound leg is the path a ray WOULD fly, and in an optically thick run "
        "it is extinguished at or before the turn.\n"
        "Do not read an absorbed fraction off this figure — laser_report.py is what says "
        "whether anything survives the turn." + beam_bit)
    fig.tight_layout(rect=[0.0, 0.15, 1.0, 0.94])
    fig.text(0.005, 0.005, cap, ha="left", va="bottom", fontsize=7.5, color=lpp.INK_2)
    lpp.stamp(fig, cfg, sc, extra=f"ray_cfl = {ray_cfl:g}")
    lpp.savefig(fig, "rays.png", run_id=rid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
