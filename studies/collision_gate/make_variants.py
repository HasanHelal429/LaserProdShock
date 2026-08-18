#!/usr/bin/env python3
"""Generate the D3 collision-gate variant run dirs into ``scratch/``.

    python3 make_variants.py            # write scratch/<variant>/{config.yaml,README.md}
    python3 make_variants.py --table     # just print the matrix and the analytic rates

The matrix is Lezhnin 2025 Appendix B: n_e = {1, 0.1, 0.01} n_cr x T_i = {12, 120} eV,
T_e = 1.1 T_i, Z = 13, aluminium at the reduced mass ratio. Each point gets THREE arms:

    coll_off  collisions disabled          -- the grid-heating control
    c1        ndt_supercycle = 1           -- collisions every PIC step
    c10       ndt_supercycle = 10          -- the PRODUCTION cadence of P4_lez_kin_bg

Why an arm at 10 and an arm at 1: the paper's Fig. 11 shows the equilibration rate is
UNDERESTIMATED once nu_ei * dt_coll > 1, with nu_ei the Braginskii electron-ion collision
frequency. Our production run uses ndt_supercycle = 10 and inherits that risk unchecked;
this study measures whether it matters at our dt.

YAML is edited by ``yaml.safe_load`` -> dict assignment -> ``yaml.safe_dump``, never by
text substitution. A previous regex edit of these configs destroyed the ``numerics``
section in five of them, and the assertions below exist so that cannot recur silently.
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))

QE = 1.602176634e-19
ME = 9.1093837015e-31
EPS0 = 8.8541878128e-12
C = 2.99792458e8
FPE = 4.0 * np.pi * EPS0

LAM0 = 1.064e-6
N_CR = EPS0 * ME * (2.0 * np.pi * C / LAM0) ** 2 / QE ** 2
DE = LAM0 / (2.0 * np.pi)
ME_C2_EV = 510998.95

Z = 13.0
MASS_RATIO = 2698.0
LNL = 6.3
CFL = 0.35
DZ_OVER_DE = 0.5
DT = CFL * DZ_OVER_DE * DE / C          # 0.0989 fs

# The Appendix B matrix is an explicit LIST, not a cross product, because one corner is
# dropped: (0.01 n_cr, 120 eV). At tau = 62 ps it needs ~237 000 steps to raise T_i to 10x
# the measured noise floor, and shortening it to an affordable 24 000 steps leaves
# signal/noise ~ 1.2 -- a number that would look like a measurement and be nothing of the
# kind. It is also the least informative point: its sigma_max cap touches 0.5 % of the
# distribution, and (0.1 n_cr, 120 eV) at 1.5 % already brackets the production plume's
# 1.4 %. Recorded here rather than silently omitted.
CASES = ((1.0, 12.0), (1.0, 120.0), (0.1, 12.0), (0.1, 120.0), (0.01, 12.0))
DROPPED = ((0.01, 120.0, "tau = 62 ps: needs ~237k steps for S/N = 10; unaffordable, and "
                         "its 0.5 % cap fraction is bracketed by (0.1 n_cr, 120 eV)"),)
NE_CASES = (1.0, 0.1, 0.01)
TI_CASES = (12.0, 120.0)
ARMS = (("coll_off", False, 1), ("c1", True, 1), ("c10", True, 10))

# CONFIRMATION variants: a pinned lnLambda that WarpX would NOT compute for itself, at
# conditions where the sigma_max cap cannot bind. This is what discriminates "WarpX honours
# CoulombLog" from "WarpX silently computes its own":
#   at n_e = n_cr, T_e = 132 eV the self-consistent lnLambda is 4.06, and sigma_max/sigma_C
#   is 2.9 even at lnLambda = 20, so the cap is inactive. Pinning 20 therefore predicts
#   R_meas/R_pred(20) ~ 1 if the input is honoured, and 4.06/20 = 0.20 if it is ignored.
# (name, ne_frac, Ti, lnLambda, ndt)
CONFIRM = (("D3_confirm_lnL20_n1_Ti120_c1", 1.0, 120.0, 20.0, 1),)

MAX_STEP_CAP = 24_000                  # affordability cap; see README.
# Only the two 120 eV low-density points hit this cap. They do NOT need 2 tau: the rate is
# fitted from the initial ramp, and at 24 000 steps the T_i rise is still ~10x the measured
# noise floor. Cutting them from 120 000 to 24 000 steps is what makes the ladder affordable
# (they were 9 h each at 3-way contention), and they are the points that matter MOST for the
# production run, because their sigma_max cap fraction (1.5 % and 0.5 %) brackets the
# production plume's (1.4 % and 0.4 %). Their t_run/tau is reported in the table and their
# error bars are wider than the rest; that is stated rather than smoothed over.


def nu_eps_ei(ni, Te_eV, Ti_eV, mi):
    """Electron-side energy relaxation rate: dTe/dt = -nu (Te - Ti).  SI, T in eV.

    1/tau = (8 sqrt(2 pi)/3) ni Z^2 e^4 lnL / ((4 pi eps0)^2 me mi) (kTe/me + kTi/mi)^-3/2

    Validated two ways in RESULTS.md 2026-08-18: hydrogen at 1 keV / 1e26 m^-3 gives
    tau = 1.00e-8 s, and it reproduces (mi/2me) tau_e from the Braginskii electron
    collision time to 0.1 %.
    """
    v2 = Te_eV * QE / ME + Ti_eV * QE / mi
    return (8.0 * np.sqrt(2.0 * np.pi) / 3.0) * ni * Z ** 2 * QE ** 4 * LNL \
        / (FPE ** 2 * ME * mi) / v2 ** 1.5


def nu_ei_braginskii(ni, Te_eV):
    """Braginskii electron-ion MOMENTUM collision frequency 1/tau_e.

    This -- not the energy relaxation rate -- is the quantity the paper's validity
    criterion nu_ei * dt_coll <~ 1 refers to. The two differ by ~mi/2me = 1349, so
    conflating them would make our production cadence look 1349x safer than it is.
    """
    tau_e = 3.0 * np.sqrt(ME) * (Te_eV * QE) ** 1.5 * FPE ** 2 \
        / (4.0 * np.sqrt(2.0 * np.pi) * ni * Z ** 2 * QE ** 4 * LNL)
    return 1.0 / tau_e


def case_physics(ne_frac, Ti):
    Te = 1.1 * Ti
    ne = ne_frac * N_CR
    ni = ne / Z
    mi = MASS_RATIO * ME
    nu_e = nu_eps_ei(ni, Te, Ti, mi)        # electron-side
    nu_i = Z * nu_e                         # ion-side = Z * electron-side
    rate = (1.0 + Z) / Z * nu_i             # the exponent coefficient in Eq. (B1)
    tau = 1.0 / rate
    return dict(ne_frac=ne_frac, Ti=Ti, Te=Te, ne=ne, ni=ni,
                nu_e=nu_e, nu_i=nu_i, rate=rate, tau=tau,
                T_eq=(Z * Te + Ti) / (Z + 1.0),
                nu_brag=nu_ei_braginskii(ni, Te))


def variant_name(ne_frac, Ti, arm):
    n = {1.0: "n1", 0.1: "n0p1", 0.01: "n0p01"}[ne_frac]
    return f"D3_{n}_Ti{int(Ti)}_{arm}"


def table():
    print(f"dt = {DT:.4e} s  (cfl {CFL}, dz {DZ_OVER_DE} d_e)   "
          f"n_cr = {N_CR:.4e} m^-3   lnLambda = {LNL}")
    print(f"{'ne/ncr':>7} {'Ti':>6} {'Te':>6} {'T_eq':>8} | {'tau_B1[ps]':>11} "
          f"{'nu_brag[1/s]':>13} {'nu_brag*dt':>11} {'*dt(x10)':>10} | "
          f"{'max_step':>9} {'t_run/tau':>10}")
    for ne_frac, Ti in CASES:
        if True:
            p = case_physics(ne_frac, Ti)
            ms = min(int(round(2.0 * p["tau"] / DT)), MAX_STEP_CAP)
            ms = max(ms, 400)
            flag = "  <-- nu*dt_coll > 1 at the production cadence" \
                if p["nu_brag"] * 10 * DT > 1.0 else ""
            print(f"{ne_frac:7.2f} {Ti:6.1f} {p['Te']:6.1f} {p['T_eq']:8.3f} | "
                  f"{p['tau']*1e12:11.4f} {p['nu_brag']:13.4e} "
                  f"{p['nu_brag']*DT:11.4f} {p['nu_brag']*10*DT:10.4f} | "
                  f"{ms:9d} {ms*DT/p['tau']:10.3f}{flag}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", action="store_true", help="print the matrix and exit")
    a = ap.parse_args()
    if a.table:
        table()
        return 0

    base = yaml.safe_load(open(os.path.join(HERE, "config.base.yaml")))
    # Guard rails: the sections a bad edit would silently remove.
    for sec in ("reference", "laser", "geometry", "plasma", "numerics", "collisions",
                "diagnostics", "gates"):
        assert sec in base, f"config.base.yaml lost its {sec!r} section"
    assert base["numerics"]["cfl"] == CFL
    assert base["geometry"]["dz_over_de"] == DZ_OVER_DE
    assert base["reference"]["mass_ratio"] == MASS_RATIO
    assert base["laser"]["intervals"] == 0, "the laser must be OFF in every variant"

    n = 0
    for ne_frac, Ti in CASES:
        if True:
            p = case_physics(ne_frac, Ti)
            ms = max(min(int(round(2.0 * p["tau"] / DT)), MAX_STEP_CAP), 400)
            for arm, enabled, ndt in ARMS:
                name = variant_name(ne_frac, Ti, arm)
                d = os.path.join(HERE, "scratch", name)
                os.makedirs(d, exist_ok=True)
                cfg = yaml.safe_load(yaml.safe_dump(base))   # deep copy
                cfg["meta"]["run_id"] = name
                cfg["meta"]["deck"] = f"inputs_{name}"
                cfg["meta"]["description"] = (
                    f"D3 collision gate (Lezhnin 2025 Appendix B), variant {name}: "
                    f"uniform periodic laser-off box at n_e = {ne_frac} n_cr, "
                    f"T_i = {Ti} eV, T_e = {p['Te']} eV, "
                    + ("collisions DISABLED (grid-heating control)" if not enabled else
                       f"collisions every {ndt} PIC step(s)")
                    + ". Generated by studies/collision_gate/make_variants.py -- do not "
                      "edit by hand.")
                cfg["plasma"]["target"]["density_over_ncr"] = float(ne_frac)
                cfg["plasma"]["target"]["theta_e_init"] = float(p["Te"] / ME_C2_EV)
                cfg["plasma"]["target"]["theta_i_init"] = float(Ti / ME_C2_EV)
                cfg["numerics"]["max_step"] = int(ms)
                # diag1 is emitted unconditionally and its frame count divides by this,
                # so 0 is not "off" -- it is a ZeroDivisionError. One dump at the end is
                # what we want anyway: it lets analyze.py confirm f(v) is Maxwellian
                # rather than assuming the second moment means what we think.
                cfg["diagnostics"]["plotfile_intervals"] = int(ms)
                # Both of these are the deliberate-control acknowledgements the gates ask
                # for. The axis IS periodic (that is the point: no boundary at all), and
                # the uniform plasma DOES sit on the injection face -- harmless, because
                # laser.intervals = 0 means no ray is ever launched.
                cfg["meta"]["expect_wrap"] = True
                cfg["meta"]["expect_face_plasma"] = True
                cfg["collisions"]["enabled"] = bool(enabled)
                cfg["collisions"]["intervals"] = int(ndt)
                cfg["diagnostics"]["reduced_intervals"] = max(1, ms // 400)
                # post-write assertions: the values that define the variant
                assert cfg["numerics"]["ppc"]["target"] == 2000
                assert cfg["geometry"]["boundary"]["axis"]["lo"] == "periodic"
                assert cfg["plasma"]["target"]["scale_length_de"] == 0
                assert "ambient" not in cfg["plasma"]
                with open(os.path.join(d, "config.yaml"), "w") as fh:
                    yaml.safe_dump(cfg, fh, sort_keys=False, default_flow_style=False)
                with open(os.path.join(d, "README.md"), "w") as fh:
                    fh.write(readme(name, p, arm, enabled, ndt, ms))
                n += 1
    # --- confirmation variants -----------------------------------------------------
    for name, nf, Ti, lnL, ndt in CONFIRM:
        p = case_physics(nf, Ti)
        # tau scales as 1/lnLambda, so rescale the step budget from the pinned value
        tau = p["tau"] * LNL / lnL
        ms = max(int(round(2.0 * tau / DT)), 400)
        d = os.path.join(HERE, "scratch", name)
        os.makedirs(d, exist_ok=True)
        cfg = yaml.safe_load(yaml.safe_dump(base))
        cfg["meta"]["run_id"] = name
        cfg["meta"]["deck"] = f"inputs_{name}"
        cfg["meta"]["description"] = (
            f"D3 CONFIRMATION run: {nf} n_cr, T_i = {Ti} eV, lnLambda PINNED at {lnL} "
            f"(not 6.3). Discriminates whether WarpX honours collisions.coulomb_log or "
            f"silently computes its own -- see CONFIRM in make_variants.py.")
        cfg["meta"]["expect_wrap"] = True
        cfg["meta"]["expect_face_plasma"] = True
        cfg["plasma"]["target"]["density_over_ncr"] = float(nf)
        cfg["plasma"]["target"]["theta_e_init"] = float(p["Te"] / ME_C2_EV)
        cfg["plasma"]["target"]["theta_i_init"] = float(Ti / ME_C2_EV)
        cfg["numerics"]["max_step"] = int(ms)
        cfg["collisions"]["enabled"] = True
        cfg["collisions"]["intervals"] = int(ndt)
        cfg["collisions"]["coulomb_log"] = float(lnL)
        cfg["diagnostics"]["reduced_intervals"] = max(1, ms // 400)
        cfg["diagnostics"]["plotfile_intervals"] = int(ms)
        with open(os.path.join(d, "config.yaml"), "w") as fh:
            yaml.safe_dump(cfg, fh, sort_keys=False, default_flow_style=False)
        with open(os.path.join(d, "README.md"), "w") as fh:
            fh.write(f"""# {name} — D3 confirmation run

**Auto-generated by `studies/collision_gate/make_variants.py`. Do not edit; regenerate.**

Not part of the Appendix B matrix. This run exists to answer one question: **does WarpX
honour `collisions.coulomb_log`, or does it compute `lnΛ` itself?**

`n_e` = {nf:g} `n_cr`, `T_e` = {p['Te']:.1f} eV, `T_i` = {Ti:.1f} eV, `lnΛ` **pinned at
{lnL:g}**, collisions every step, {ms} steps = 2 τ at that `lnΛ`.

At these conditions the self-consistent `lnΛ` is **4.06**, and the `σ_max` cross-section cap
(`ElasticCollisionPerez.H`, `sigma_max = 1/(n·r_min)`) has `σ_max/σ_C` = 2.9 even at
`lnΛ` = 20 — so the cap is **inactive** and cannot confound the answer.

| outcome | meaning |
|---|---|
| `R_meas/R_pred(20)` ≈ 1 | the pinned value is honoured |
| `R_meas/R_pred(20)` ≈ 0.20 | the input is ignored and `lnΛ` = 4.06 was used |

## Result
_To be filled in by `analyze.py`._
""")
        n += 1
    print(f"wrote {n} variants under {os.path.join(HERE, 'scratch')}")
    return 0


def readme(name, p, arm, enabled, ndt, ms):
    return f"""# {name} — D3 collision gate variant

**Auto-generated by `studies/collision_gate/make_variants.py`. Do not edit; regenerate.**
Parent study: `studies/collision_gate/` (see its README for the hypothesis and method).

## What this run is
One point of the Lezhnin 2025 Appendix B electron–ion thermalisation test, at the
**production** mass ratio, charge state, `lnΛ`, `dz` and `cfl` of `runs/P4/P4_lez_kin_bg`.

## Geometry
1D, `z` only. Domain **−10 → +10 `d_e`** (20 `d_e` = 2 `d_i0`, with `d_i0` = 10 `d_e` the
proton skin depth at `n_cr`), **40 cells** at `dz` = 0.5 `d_e`. **Periodic** on both faces.
A single uniform plasma fills the entire box (flat top of thickness 20 `d_e` centred at 0,
no corona), so there is no spatial structure and no boundary of any kind. No ambient
species. **The laser never fires** (`laser.intervals = 0`).

## Physics
| | |
|---|---|
| `n_e` | {p['ne_frac']:g} `n_cr` = {p['ne']:.4e} m⁻³ |
| `n_i` | {p['ni']:.4e} m⁻³  (`Z` = 13) |
| `T_e`(0) | {p['Te']:.1f} eV |
| `T_i`(0) | {p['Ti']:.1f} eV  (`T_e` = 1.1 `T_i`) |
| `m_i` | 2698 `m_e` = 1.4801 amu (aluminium at the paper's reduced `m_p/m_e` = 100) |
| `lnΛ` | 6.3, pinned |
| collisions | {'DISABLED — grid-heating control' if not enabled else f'every {ndt} PIC step(s) (`ndt_supercycle = {ndt}`)'} |

## Prediction
Both species must relax to `T_eq` = (Z·T_e0 + T_i0)/(Z+1) = **{p['T_eq']:.3f} eV**, with
`T_i` rising {p['T_eq']-p['Ti']:.3f} eV (9.29 % of `T_i0`), following Eq. (B1):

    T_i(t) = T_i0 + [Z(T_e0 − T_i0)/(Z+1)] · [1 − exp(−((1+Z)/Z)·ν_ie·t)]

with an e-folding time **τ = {p['tau']*1e12:.4f} ps**. This run is {ms} steps
= {ms*DT*1e12:.4f} ps = **{ms*DT/p['tau']:.3f} τ**.

The `coll_off` arm predicts **no** relative change between the species beyond numerical
grid heating, which raises *both*. `dz/λ_D` is under-resolved here, so that heating is
expected and is exactly what this arm measures.

Braginskii `ν_ei` = {p['nu_brag']:.4e} s⁻¹, so `ν_ei·dt` = {p['nu_brag']*DT:.4f} and
`ν_ei·dt_coll` at the production cadence (×10) = **{p['nu_brag']*10*DT:.4f}**
{'— **above 1, the regime the paper reports underestimates the rate**' if p['nu_brag']*10*DT > 1 else '— below 1, so the cadence should be adequate'}.

## Result
_To be filled in by `studies/collision_gate/analyze.py`._
"""


if __name__ == "__main__":
    raise SystemExit(main())
