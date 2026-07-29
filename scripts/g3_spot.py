#!/usr/bin/env python3
"""Gate G3 restricted to the ILLUMINATED columns — the honest control for a finite spot.

G3 subtracts a laser-off control's particle-KE gain from the driven run's, to show that a
few-percent heating claim is not grid heating. The standard measurement uses the
`ParticleEnergy` reduced diagnostic, which is a whole-domain total — and for a **finite
spot** that is structurally unfair. `P1_vac_2d_spot` drives a `w₀` = 20 `d_e` beam inside a
±80 `d_e` box, so the illuminated fraction is ~35/160 ≈ 22 % of the transverse extent: the
driven signal is diluted by four-fifths of a box that was never lit, while grid heating —
which is a property of the grid and the ppc, not of the beam — fills all of it. The whole-box
ratio therefore overstates the control by roughly the inverse illuminated fraction.

This reads the PLOTFILES instead, so the same subtraction can be made where the light
actually went.

    python scripts/g3_spot.py <driven_run> --control <control_run> [--waists 1.0]

Reported for three regions at every matched dump:

  * **illuminated**  |x − x_c| < `waists`·`w₀`   — the number to quote
  * **dark**         |x − x_c| > 2.5·`w₀`        — a control-free grid-heating measure, since
                                                    the beam deposits 0.04 % of its power there
                                                    at `t` = 0 (`studies/spot_leak_ppc`)
  * **whole box**                                — reproduces the reduced-diagnostic G3, so the
                                                    effect of restricting is visible, not asserted

For a run with `beam.profile: uniform` the illumination is transversely uniform, so every
region must return the SAME ratio to within statistics. That is the script's own correctness
test — run it on `P1_vac_2d` / `P1_vac_2d_off` before trusting it on a spot.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod.units import C, ME           # noqa: E402


def ke_by_region(ds, species, mass, x_edges, x_axis_field, ax_field):
    """Kinetic energy (J, or J/m in 2D) per transverse region, from one plotfile.

    Relativistic on purpose: `(gamma-1)mc^2`, not `p^2/2m`. The absorbed energy goes into a
    tail as well as a bulk, and a non-relativistic sum would quietly understate the tail --
    which is the part a heating claim rests on.
    """
    out = np.zeros(len(x_edges))
    ad = ds.all_data()
    have = {f[0] for f in ds.field_list}
    need = (x_axis_field, "particle_momentum_x", "particle_momentum_y",
            "particle_momentum_z", "particle_weight")
    for name in species:
        # A missing species or field must NOT silently contribute zero: that would turn a
        # wrong-diagnostic-family mistake into a confident, fabricated G3. `diag_phase`
        # dumps carry no momenta at all, which is exactly how this was found.
        if name not in have:
            raise SystemExit(
                f"{ds.basename}: species '{name}' is not in this plotfile (it has "
                f"{sorted(have)}). A restricted G3 needs the FULL particle dump -- pass "
                f"--prefix diag1, not a phase-space or fields diagnostic.")
        missing = [f for f in need if (name, f) not in ds.field_list]
        if missing:
            raise SystemExit(f"{ds.basename}: species '{name}' lacks {missing} -- this is "
                             f"not a full particle plotfile.")
        x = np.asarray(ad[(name, x_axis_field)])
        px = np.asarray(ad[(name, "particle_momentum_x")])
        py = np.asarray(ad[(name, "particle_momentum_y")])
        pz = np.asarray(ad[(name, "particle_momentum_z")])
        w = np.asarray(ad[(name, "particle_weight")])
        if x.size == 0:
            continue
        m = mass[name]
        u2 = (px * px + py * py + pz * pz) / (m * C) ** 2
        ke = w * (np.sqrt(1.0 + u2) - 1.0) * m * C * C
        for i, sel in enumerate(x_edges):
            out[i] += float(ke[sel(x)].sum())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--control", required=True, help="the laser-off run (G3)")
    ap.add_argument("--waists", type=float, default=1.0,
                    help="illuminated region half-width in beam waists (default 1.0)")
    ap.add_argument("--dark", type=float, default=2.5,
                    help="dark region starts at this many waists (default 2.5)")
    ap.add_argument("--max-dumps", type=int, default=6)
    ap.add_argument("--prefix", default="diag1",
                    help="plotfile family (default diag1 -- the FULL particle dump). Note "
                         "lpio.plotfiles' own default, 'diag', is a prefix of diag1, "
                         "diag_fields AND diag_phase, so it silently mixes families.")
    args = ap.parse_args()

    import yt
    yt.set_log_level("error")
    from laserprod.deck import _species_table

    cfg = lpconfig.load(args.run_dir)
    ccfg = lpconfig.load(args.control)
    sc = lpconfig.derive(cfg)
    rid, crid = lpconfig.run_id(cfg), lpconfig.run_id(ccfg)
    if int(cfg["geometry"]["dims"]) < 2:
        print(f"{rid} is 1D -- there is no transverse direction to restrict. Use the "
              f"whole-domain G3 from compare_runs.py.")
        return 1

    beam = (cfg["laser"].get("beam") or {})
    prof = str(beam.get("profile", "uniform"))
    w0 = float(beam.get("waist_de", 0.0)) * sc.de_ref
    xc = float(beam.get("center_de", [0.0])[0] if isinstance(beam.get("center_de"), list)
               else beam.get("center_de", 0.0)) * sc.de_ref
    tlo = float(cfg["geometry"]["transverse"]["lo_de"]) * sc.de_ref
    thi = float(cfg["geometry"]["transverse"]["hi_de"]) * sc.de_ref
    if not w0:
        # A uniform beam has no waist; use a quarter of the transverse half-width so the
        # three regions are still distinct and the uniformity check below is meaningful.
        w0 = 0.25 * 0.5 * (thi - tlo)
        print(f"note: beam.profile = {prof} has no waist -- using {w0*1e6:.3f} um "
              f"(a quarter of the half-width) so the regions are distinct.\n"
              f"      For a uniform beam ALL regions must agree: that is the check.")

    species = list(_species_table(cfg))
    mass = {s: (ME if "electron" in s else sc.mi) for s in species}

    regions = [
        (f"illuminated |x-xc|<{args.waists:g}w0", lambda x: np.abs(x - xc) < args.waists * w0),
        (f"dark |x-xc|>{args.dark:g}w0", lambda x: np.abs(x - xc) > args.dark * w0),
        ("whole box", lambda x: np.ones_like(x, dtype=bool)),
    ]
    sels = [r[1] for r in regions]

    dpaths = lpio.plotfiles(cfg["_run_dir"], args.prefix)
    cpaths = lpio.plotfiles(ccfg["_run_dir"], args.prefix)
    if not dpaths or not cpaths:
        print(f"need '{args.prefix}' plotfiles in both runs "
              f"({len(dpaths)} driven, {len(cpaths)} control)")
        return 1
    # Match by step, not by index: a control that died early must not be silently paired
    # with the wrong time.
    dmap = {lpio._step_of(p): p for p in dpaths}
    cmap = {lpio._step_of(p): p for p in cpaths}
    steps = sorted(set(dmap) & set(cmap))
    if len(steps) < 2:
        print(f"only {len(steps)} matched step(s) between {rid} and {crid} -- need t=0 and one more")
        return 1
    if len(steps) > args.max_dumps:
        keep = np.linspace(0, len(steps) - 1, args.max_dumps).round().astype(int)
        steps = [steps[i] for i in keep]

    print(f"G3 restricted to the illuminated columns")
    print(f"  driven  {rid}")
    print(f"  control {crid}")
    print(f"  beam    profile {prof}, w0 = {w0*1e6:.3f} um = {w0/sc.de_ref:.1f} d_e, "
          f"centre {xc*1e6:+.3f} um")
    print(f"  box     transverse {tlo*1e6:+.2f} .. {thi*1e6:+.2f} um; illuminated fraction "
          f"of the transverse extent = {2*args.waists*w0/(thi-tlo)*100:.1f} %\n")

    ke0d = ke0c = None
    rows = []
    for st in steps:
        dsd, dsc = yt.load(dmap[st]), yt.load(cmap[st])
        t = float(dsd.current_time)
        kd = ke_by_region(dsd, species, mass, sels, "particle_position_x", None)
        kc = ke_by_region(dsc, species, mass, sels, "particle_position_x", None)
        if ke0d is None:
            ke0d, ke0c = kd, kc
            continue
        rows.append((t, kd - ke0d, kc - ke0c))

    hdr = f"{'t [ps]':>7} | " + " | ".join(f"{n:>34}" for n, _ in regions)
    print(hdr)
    print(f"{'':>7} | " + " | ".join(
        f"{'dKE_driven':>12} {'dKE_ctrl':>10} {'ctrl/dr':>9}" for _ in regions))
    print("-" * len(hdr))
    for t, dd, dc in rows:
        cells = []
        for i in range(len(regions)):
            r = (dc[i] / dd[i] * 100.0) if dd[i] != 0 else float("nan")
            cells.append(f"{dd[i]:12.4g} {dc[i]:10.3g} {r:8.2f}%")
        print(f"{t*1e12:7.3f} | " + " | ".join(cells))

    if rows:
        t, dd, dc = rows[-1]
        ill = dc[0] / dd[0] * 100.0 if dd[0] else float("nan")
        box = dc[2] / dd[2] * 100.0 if dd[2] else float("nan")
        print(f"\nAt t = {t*1e12:.3f} ps:")
        print(f"  G3 on the illuminated columns : {ill:+.2f} % of the driven gain")
        print(f"  G3 on the whole box (standard): {box:+.2f} %")
        if np.isfinite(ill) and np.isfinite(box) and box != 0:
            print(f"  restricting changes the verdict by x{ill/box:.2f}")
        # The whole-box column must reproduce the ParticleEnergy reduced diagnostic, which
        # is an independent measurement of the same quantity by a different code path. This
        # is what caught the diagnostic-family mix-up: the plotfile sums agreed with the
        # reduced diag's ABSOLUTE energies rather than its differences.
        try:
            td, ked = lpio.particle_energy(cfg["_run_dir"])
            tc, kec = lpio.particle_energy(ccfg["_run_dir"])
            td, ked, tc, kec = (np.asarray(a) for a in (td, ked, tc, kec))
            i = int(np.argmin(np.abs(td - t))); j = int(np.argmin(np.abs(tc - t)))
            rd_, rc_ = ked[i] - ked[0], kec[j] - kec[0]
            print(f"\n  cross-check against the ParticleEnergy reduced diagnostic at "
                  f"t = {td[i]*1e12:.3f} ps:")
            print(f"    driven  plotfile {dd[2]:+.5g}   reduced {rd_:+.5g}   "
                  f"({abs(dd[2]-rd_)/abs(rd_)*100 if rd_ else float('nan'):.3f} % apart)")
            print(f"    control plotfile {dc[2]:+.5g}   reduced {rc_:+.5g}   "
                  f"({abs(dc[2]-rc_)/abs(rc_)*100 if rc_ else float('nan'):.3f} % apart)")
            bad = [n for n, a, b in (("driven", dd[2], rd_), ("control", dc[2], rc_))
                   if b and abs(a - b) / abs(b) > 0.02]
            print(f"    {'consistent' if not bad else 'DISAGREE on ' + ', '.join(bad) + ' -- do not quote this G3'}")
        except Exception as exc:
            print(f"\n  (no reduced-diagnostic cross-check: {exc})")

        if prof == "uniform":
            spread = max(abs(dc[i] / dd[i] * 100.0 - box) for i in range(len(regions))
                         if dd[i])
            print(f"\n  UNIFORM beam self-test: regions spread {spread:.2f} percentage points "
                  f"about the whole-box value.")
            print(f"  {'PASS -- uniform illumination gives a region-independent G3, as it must.'
                    if spread < 2.0 else 'SUSPECT -- a uniform beam should give the same G3 everywhere.'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
