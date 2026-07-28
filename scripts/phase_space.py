#!/usr/bin/env python3
"""Ion phase space (z, u_z) — THE ARBITER, and the clearest view of a boundary.

`CLAUDE.md` rule three: density and B streaks of a *decaying magnetosonic pulse* look
shock-like, so no run may be called a shock without this diagnostic. Two questions it
answers that nothing else does:

* **Is there ion reflection?** A shock reflects ambient ions back upstream, producing a
  population at ``u_z > v_sh`` that is absent from a mere compression.
* **Is the piston faster than the wave it launched?** A piston slower than its own
  compression is not driving it — the exact reading that retracted the upstream
  "marginally supercritical shock".

For Phase 0 it also shows the boundary behaviour directly: the runaway ablation front
appears as a fast tail, and with periodic boundaries that tail **reappears at the
opposite edge** having wrapped, which is visible here and in no integrated quantity.

    /opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/<ID>
    ... scripts/phase_space.py runs/<ID> --frames 0 0.5 1.2 2.3

Writes ``media/<ID>/phase_space.png``: one (z, u_z) panel per selected time, target and
ambient ions overlaid as an additive two-colour distribution (warm = target, cool =
ambient) so overlap is visible instead of one species hiding the other.
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


def _asinh(H, softclip=0.03):
    """asinh stretch so a dense core and a sparse fast tail are visible at once."""
    hmax = float(H.max()) if H.size else 0.0
    if hmax <= 0:
        return H
    a = softclip * hmax
    return np.arcsinh(H / a) / np.arcsinh(hmax / a)


def species_uz(ds, name, axis_last):
    """(z, u_z, weight) for one species from a plotfile, or empty arrays."""
    try:
        ad = ds.all_data()
        z = np.asarray(ad[(name, "particle_position_x" if axis_last == 0
                           else "particle_position_y")])
        uz = np.asarray(ad[(name, "particle_momentum_z")])
        w = np.asarray(ad[(name, "particle_weight")])
    except Exception:
        return np.array([]), np.array([]), np.array([])
    return z, uz, w


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--frames", type=float, nargs="*", default=None,
                    help="times in ps (default: 4 evenly spaced)")
    args = ap.parse_args()

    import matplotlib.pyplot as plt
    import yt

    from laserprod.deck import _species_table
    from laserprod.units import ME

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    ions = [s for s in _species_table(cfg) if s.endswith("ions")]

    paths = lpio.plotfiles(rd, "diag_phase") or lpio.plotfiles(rd, "diag1")
    if not paths:
        print(f"no particle plotfiles in {rd}/diags (need diag_phase or diag1)")
        return 1

    times = []
    for p in paths:
        try:
            times.append(float(yt.load(p).current_time))
        except Exception:
            times.append(np.nan)
    times = np.asarray(times)
    if args.frames:
        idx = [int(np.nanargmin(np.abs(times * 1e12 - v))) for v in args.frames]
    else:
        idx = list(np.linspace(0, len(paths) - 1, 4).astype(int))

    # velocity unit: v_A when there is a field, else the target sound speed
    if sc.vA:
        vunit, vname = sc.vA, "v$_A$"
    else:
        vunit, vname = sc.Cs_targ, "C$_s$(target)"

    fig, axes = plt.subplots(len(idx), 1, figsize=(11.0, 2.9 * len(idx) + 0.8),
                             sharex=True)
    axes = np.atleast_1d(axes)

    zlo, zhi = sc.domain_lo / sc.de_ref, sc.domain_hi / sc.de_ref
    z_edges = np.linspace(zlo, zhi, 320)
    stats = []
    vmax_seen = 1.0
    per_frame = []
    for i in idx:
        ds = yt.load(paths[i])
        axis_last = 0 if int(ds.domain_dimensions[1]) == 1 else 1
        data = {}
        for s in ions:
            z, uz, w = species_uz(ds, s, axis_last)
            if z.size == 0:
                continue
            # particle_momentum_z is gamma*m*v [kg m/s]; per ion mass -> u = gamma v
            v = uz / sc.mi
            data[s] = (z / sc.de_ref, v / vunit, w)
            vmax_seen = max(vmax_seen, float(np.percentile(np.abs(v / vunit), 99.9)))
        per_frame.append((float(ds.current_time), data))

    v_edges = np.linspace(-0.35 * vmax_seen, vmax_seen, 260)
    for ax, (tt, data) in zip(axes, per_frame):
        rgb = np.zeros((len(v_edges) - 1, len(z_edges) - 1, 3))
        for s, (z, v, w) in data.items():
            H, _, _ = np.histogram2d(z, v, bins=[z_edges, v_edges], weights=w)
            tint = np.asarray(_hex(lpp.C_TARGET if s.startswith("targ")
                                   else lpp.C_AMBIENT))
            rgb += _asinh(H).T[..., None] * tint
        ax.imshow(np.clip(rgb, 0, 1), origin="lower", aspect="auto",
                  interpolation="nearest",
                  extent=[z_edges[0], z_edges[-1], v_edges[0], v_edges[-1]])
        ax.set_facecolor("#0b0b12")
        ax.axhline(0.0, color="w", ls=":", lw=0.8, alpha=0.5)
        ax.set_ylabel(f"u$_z$  [{vname}]")
        ax.set_title(f"t = {tt*1e12:.3f} ps", loc="left", fontweight="bold")
        # one label per DISTINCT species (a vacuum run has only the target)
        for j, s in enumerate(dict.fromkeys(ions)):
            if s in data:
                col = lpp.C_TARGET if s.startswith("targ") else lpp.C_AMBIENT
                ax.text(0.015 + 0.115 * j, 0.94, s, transform=ax.transAxes,
                        color=col, fontsize=8, fontweight="bold", va="top")
        # fastest 0.1% of target ions = the runaway front
        if ions[0] in data:
            z0, v0, _ = data[ions[0]]
            if v0.size:
                vf = float(np.percentile(v0, 99.9))
                ax.axhline(vf, color="w", ls="--", lw=0.8, alpha=0.6)
                ax.text(0.985, vf, f"front (99.9th pct) {vf:.2f} {vname} ",
                        transform=ax.get_yaxis_transform(), ha="right", va="bottom",
                        fontsize=7, color="w", alpha=0.85)
                stats.append((tt, vf, float(v0.max())))

    axes[-1].set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
    faces = lpconfig.boundary_faces(cfg)
    bc = faces[str(cfg["geometry"].get("normal_axis", "z"))]
    note = ("PERIODIC boundaries: a fast tail that leaves one edge REAPPEARS at the "
            "other — look for target ions (warm) at the far end."
            if "periodic" in bc else
            "OPEN boundaries: the fast tail is absorbed at the edge and does not "
            "reappear.")
    lpp.stamp(fig, cfg, sc, extra=f"axis {bc[0]}/{bc[1]}")
    fig.text(0.005, 0.978, note, ha="left", va="top", fontsize=8, color=lpp.INK_2)
    lpp.savefig(fig, "phase_space.png", run_id=rid)

    print(f"{rid}: ion phase space, axis BC {bc[0]}/{bc[1]}, u in {vname}")
    for tt, vf, vm in stats:
        print(f"  t = {tt*1e12:6.3f} ps   target-ion front (99.9th pct) "
              f"{vf:7.3f} {vname} = {vf*vunit/2.998e8:.4f} c   max {vm:7.3f}")
    return 0


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


if __name__ == "__main__":
    raise SystemExit(main())
