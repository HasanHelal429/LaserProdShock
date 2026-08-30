#!/usr/bin/env python3
"""Lift a WarpX initial condition STRAIGHT from a FLASH plotfile — no analytic fit.

Phase 4's initial condition is a four-parameter analytic exponential *fitted* to FLASH's
0.1 ns state. `scripts/ic_optical_depth.py` showed that fit is **1.80x too absorbing** at
matched resolution: `rms(ln n)` = 0.107 and inverse bremsstrahlung goes as `n^2`. This tool
removes the fit from the loop and carries FLASH's actual profile instead.

It writes a NODE TABLE, not a deck. `config.yaml` stays the single source of truth and the
deck stays a pure function of it: this reads FLASH once, writes `ic_flash.yaml` beside the
config (tracked, human-readable, diffable), and `deck.py`'s `flash_table` branch renders it
into WarpX parser expressions. Nothing downstream needs h5py, and re-rendering a deck a year
from now does not require the FLASH delivery to still be mounted.

All four handoff profiles are lifted -- `n_e`, `T_e`, `T_i` and `v_z` -- because lifting only
the density would leave the isothermal-corona assumption in place, and `K ~ T^(-3/2)` makes
that assumption an absorption knob in its own right.

The representation
------------------
Each profile is a piecewise-linear function of `z/d_e` on adaptively placed nodes, rendered
as a RAMP SUM rather than nested `if()`:

    f(z) = f_0 + sum_k  dm_k * max(0, z/de - z_k)      dm_k = m_k - m_(k-1)

with a closing term that cancels the last slope, so the function is flat outside the fitted
span instead of extrapolating off a cliff. amrex's parser has `max`, the sum is flat rather
than nested, and each node contributes exactly one term. Density is fitted in `ln n`, so the
rendered expression is `ncr*exp(...)` and a five-decade corona costs no accuracy at its tail.

Two departures from FLASH are kept, and both are recorded in the table's `clamp` block:

* **the 10 n_cr density cap** (concession 1, `HANDOFF.md` 2) -- the overdense interior is
  not representable on a uniform PIC grid, so `n` is clipped BEFORE fitting.
* **a solid temperature floor** -- FLASH's cold interior is Debye-unresolvable. `T_e` is
  floored at `theta_e_solid` and the tool reports what fraction of the target that binds on.

Usage
-----
    /opt/anaconda3/envs/physics/bin/python scripts/flash_ic_fit.py runs/P5/P5_flashic \
        --time 0.1 --nodes 64
    ... --time 0.4              # the handoff-time sensitivity ladder
    ... --dry                   # fit and report, write nothing
"""
import argparse
import datetime as _dt
import os
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

DE_UM = 0.169336
MEC2_EV = 510998.95


def greedy_nodes(x, y, nmax, tol):
    """Piecewise-linear node placement by greedy max-error insertion.

    Start with the endpoints, then repeatedly insert the abscissa where the current
    interpolant is worst. Places nodes where curvature demands them -- dense through the
    critical surface, sparse in the exponential tail -- which is the whole point: a uniform
    grid would spend its budget on the tail and under-resolve the turning point, and the
    turning point is where 41 % of the optical depth lives.
    """
    idx = [0, len(x) - 1]
    for _ in range(nmax - 2):
        yi = np.interp(x, x[idx], y[idx])
        err = np.abs(yi - y)
        j = int(np.argmax(err))
        if err[j] <= tol or j in idx:
            break
        idx = sorted(idx + [j])
    yi = np.interp(x, x[idx], y[idx])
    return np.array(idx), float(np.sqrt(np.mean((yi - y) ** 2))), float(np.max(np.abs(yi - y)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--time", type=float, default=0.1, help="FLASH handoff time [ns]")
    ap.add_argument("--nodes", type=int, default=64, help="max nodes per profile")
    ap.add_argument("--tol-ln-n", type=float, default=0.01,
                    help="stop refining density below this max |d ln n| (default 0.01, "
                         "vs the analytic fit's rms of 0.107)")
    ap.add_argument("--n-min", type=float, default=1.0e-4, help="n/n_cr floor for the fit")
    ap.add_argument("--rad", action="store_true", help="use the radiation-ON FLASH run")
    ap.add_argument("--out", default="ic_flash.yaml")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    cfg_path = os.path.join(a.run_dir, "config.yaml")
    cfg = yaml.safe_load(open(cfg_path))
    tgt = cfg["plasma"]["target"]
    n_cap = float(tgt["density_over_ncr"])
    th_solid = tgt.get("theta_e_solid")
    T_floor = float(th_solid) * MEC2_EV if th_solid is not None else 0.0

    from xcode_compare import flash_series, FLASH_DIR, FLASH_RAD, DI0_F, CS0_F
    src = FLASH_RAD if a.rad else FLASH_DIR
    base = "lez1drad" if a.rad else "lez1d"
    S = flash_series(src, base)
    s = min(S, key=lambda q: abs(q["t"] - a.time * 1e-9))
    t_ns = s["t"] * 1e9

    # FLASH's zeta is (x - interface)/d_i0; the config works in d_e with the face at 0.
    z_de = s["zeta"] * DI0_F * 1e6 / DE_UM
    n = np.array(s["ne"], float)
    Te = np.array(s["Te"], float)
    Ti = np.array(s["Ti"], float)
    # THE UNIT TRAP, and it is the same one HANDOFF.md 6 records costing a 4.05x error in
    # L_n. `flash_series` returns velocity normalised to C_S0, NOT to c -- it is built for
    # the comparison axes, where every speed is in C_S0. WarpX's uz_mean is u = gamma*v/c.
    # Writing v/C_S0 into a field the deck renders as u/c overstates the drift by
    # c/C_S0 = 1533x and injects a SUPERLUMINAL initial condition (measured 4.01 c before
    # this line existed). Convert here, once, at the only place that knows both units.
    C = 299792458.0
    vz = np.array(s["v"], float) * CS0_F / C

    o = np.argsort(z_de)
    z_de, n, Te, Ti, vz = z_de[o], n[o], Te[o], Ti[o], vz[o]

    # THE ION-TEMPERATURE VACUUM ARTIFACT (DELIVERY.md 3). At t <= 0.4 ns FLASH's chamber
    # gas reads 78-208 keV in undisturbed 1e-10 g/cm^3 vapour far ahead of the plume,
    # carrying ~5e-10 of the mass. Lifting that verbatim would import a keV ion population
    # into the PIC leg. Masking on density is the documented fix.
    keep = np.isfinite(n) & (n >= a.n_min) & np.isfinite(Te) & np.isfinite(Ti)
    n_dropped = int((~keep).sum())
    z_de, n, Te, Ti, vz = z_de[keep], n[keep], Te[keep], Ti[keep], vz[keep]
    if z_de.size < 16:
        sys.exit(f"only {z_de.size} cells above n/n_cr = {a.n_min} -- nothing to fit")

    n_clipped = np.minimum(n, n_cap)
    frac_capped = float((n > n_cap).mean())
    Te_f = np.maximum(Te, T_floor)
    frac_floored = float((Te < T_floor).mean())

    # A hard guard, not a comment. This is the one quantity in the handoff whose units
    # cannot be checked by looking at the number: 0.5 is a plausible v/C_S0 and an
    # implausible v/c, and nothing downstream would flag it.
    if not np.all(np.abs(vz) < 0.2):
        sys.exit(f"REFUSING: |v_z|/c reaches {np.abs(vz).max():.3f}. That is either a unit "
                 f"error or a genuinely relativistic handoff; neither belongs in this deck "
                 f"unchecked.")

    profiles = {}
    report = []
    for key, y, tol, unit in (("ln_n_over_ncr", np.log(n_clipped), a.tol_ln_n, "ln(n/ncr)"),
                              ("Te_eV", Te_f, 0.01 * np.nanmax(Te_f), "eV"),
                              ("Ti_eV", Ti, 0.01 * np.nanmax(Ti), "eV"),
                              ("vz_over_c", vz, 1e-6, "v/c")):
        idx, rms, mx = greedy_nodes(z_de, y, a.nodes, tol)
        profiles[key] = dict(z_de=[float(q) for q in z_de[idx]],
                             value=[float(q) for q in y[idx]])
        report.append((key, len(idx), rms, mx, unit))

    print(f"FLASH {'rad-ON' if a.rad else 'rad-OFF'} at t = {t_ns:.4f} ns "
          f"(asked {a.time:.3f})")
    print(f"  {z_de.size} cells above n/n_cr = {a.n_min:g}; "
          f"{n_dropped} dropped (incl. the T_i vacuum artifact)")
    print(f"  density capped at {n_cap:g} n_cr on {100*frac_capped:.1f}% of the cells")
    print(f"  T_e floored at {T_floor:.3f} eV on {100*frac_floored:.1f}% of the cells")
    print(f"  span z = {z_de.min():.2f} .. {z_de.max():.2f} d_e\n")
    print(f"  {'profile':16s} {'nodes':>6s} {'rms':>12s} {'max |err|':>12s}  unit")
    print("  " + "-" * 62)
    for key, k, rms, mx, unit in report:
        print(f"  {key:16s} {k:6d} {rms:12.4e} {mx:12.4e}  {unit}")
    print(f"\n  for reference, the ANALYTIC fit this replaces has rms(ln n) = 0.107")

    # Representative corona values, for the DERIVED SCALES and the numerical gates only
    # (units.derive needs one theta per species to compute lambda_D, omega_pe*dt, C_S...).
    # Density-weighted over the plume band 0.05 < n/n_cr < 1, the same band every plume
    # scalar in this project is measured on. Written HERE rather than duplicated into
    # config.yaml so there is exactly one source of truth for the initial condition.
    band = (n_clipped >= 0.05) & (n_clipped <= 1.0)
    if band.sum() >= 2:
        wgt = n_clipped[band]
        Te_rep = float(np.average(Te_f[band], weights=wgt))
        Ti_rep = float(np.average(Ti[band], weights=wgt))
    else:
        Te_rep, Ti_rep = float(np.nanmax(Te_f)), float(np.nanmax(Ti))
    print(f"\n  plume-band representative (for gates/scales only): "
          f"T_e = {Te_rep:.1f} eV, T_i = {Ti_rep:.1f} eV")

    doc = dict(
        meta=dict(
            source=os.path.join(src, f"{base}_hdf5_plt_cnt_*"),
            radiation="on" if a.rad else "off",
            time_ns=float(t_ns), requested_time_ns=float(a.time),
            generated=_dt.date.today().isoformat(),
            tool="scripts/flash_ic_fit.py",
            note=("Piecewise-linear nodes in z/d_e, face at z = 0. Rendered by deck.py's "
                  "flash_table branch as a ramp sum; see that branch for the exact form."),
            fit=dict((k, dict(nodes=int(kk), rms=float(r), max_abs_err=float(m)))
                     for k, kk, r, m, _ in report)),
        clamp=dict(n_max_over_ncr=n_cap, n_min_over_ncr=float(a.n_min),
                   Te_floor_eV=float(T_floor),
                   frac_cells_density_capped=frac_capped,
                   frac_cells_Te_floored=frac_floored),
        derived=dict(
            note=("Representative plume-band (0.05-1 n_cr, density-weighted) values. Used "
                  "ONLY for the derived scales and the numerical gates; the initial "
                  "condition itself is `profiles`, never these."),
            theta_e_init=Te_rep / MEC2_EV, theta_i_init=Ti_rep / MEC2_EV,
            Te_rep_eV=Te_rep, Ti_rep_eV=Ti_rep),
        profiles=profiles)

    if a.dry:
        print("\n  --dry: nothing written")
        return
    out = os.path.join(a.run_dir, a.out)
    with open(out, "w") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False, default_flow_style=False, width=96)
    print(f"\n  wrote {out}")
    print(f"  now set in {cfg_path}:  plasma.target.corona_profile: flash_table")
    print(f"                          plasma.target.ic_table: {a.out}")


if __name__ == "__main__":
    main()
