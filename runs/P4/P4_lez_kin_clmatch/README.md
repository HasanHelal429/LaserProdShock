# P4_lez_kin_clmatch — WarpX at PSC's absorbed fraction, so only the ion mass is left

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** With `f_abs` matched to PSC by construction rather than corrected for, is the
remaining WarpX↔PSC temperature gap exactly `µ^(1/3)`?
**Expected.** `<f_abs>` = 0.583 ± 0.03 (PSC `run_ourflash_511keV`'s time-integrated value),
and plume `T_e` = **192 eV** — PSC's 508.8 eV divided by `µ^(1/3)` = 2.645.
**Falsified by.** `T_e` outside 192 ± 26 eV (the 13.5 % measured noise floor) once `<f_abs>`
is within 5 % of 0.583. That would mean `µ^(1/3)` is not the whole difference and something
beyond the ion mass separates the codes.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 110592 steps = 10.93 ps
```

## Setup
Parent: **`P4_lez_kin_cl_ctrl`**, which is itself `P4_lez_kin_mr100` with
`laser.coulomb_log_mode: constant`. The only key that moves from the parent is
**`laser.coulomb_log` 4.75 → 11.2**. `collisions.coulomb_log` stays at 6.3, the mass ratio
stays 2698, the IC, target, grid and duration are untouched.

**Why this is a legitimate knob and not a fudge.** `A ∝ lnΛ` enters the IB coefficient
*linearly* and the ray path depends only on `n_e/n_cr`, so scaling `laser.coulomb_log` is
mathematically identical to scaling every path element — the mechanism established by
`cl_psc` (RESULTS 2026-08-23). Here it is used purely to land the absorbed fraction on PSC's,
so that the comparison no longer has to carry `f_abs^(2/3)`.

**Why removing `f_abs` from the comparison matters.** The cross-code tables reduce each leg
by `T_ss = 823·µ^(1/3)·f_abs^(2/3)`. That correction does not hold up: applied to the µ-sweep
it gives 1529 / 838 / 495 eV for mr25 / mr100 / mr400, a 3.1× spread where a valid reduction
would give one constant. `f_abs` is a violently spiky instantaneous diagnostic and the
`^(2/3)` amplifies it. Matching `f_abs` experimentally removes that term entirely and leaves
`µ^(1/3)`, which the µ-sweep *did* confirm to 2.3 % over {100, 400}.

**The 11.2 is an estimate and may need one iteration.** Interpolating optical depth
`τ = −ln(1−<f_abs>)/2` between `cl_ctrl` (lnΛ 4.75, `<f_abs>` 0.4074) and `cl_psc`
(lnΛ 20.35, `<f_abs>` 0.7455) puts the target at lnΛ ≈ 11.2. If the measured `<f_abs>` misses
0.583 by more than 5 %, re-solve on the three points and rerun — the leg is ~6 minutes.

**Convention, stated because the project has mixed them.** `<f_abs>` here is the
TIME-INTEGRATED fraction, `xcode_compare.absorbed()['f_mean']`, not the final instantaneous
`f_end` the older RESULTS tables quote. See GOTCHAS "Cross-code comparison".

## Cost
5000 cells × 500 ppc × 110592 steps. Parent measured 345 s (TinyProfiler) on one RTX 4070;
this leg is identical in size, so **~6 min**.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 (limit 2, budget 1.2) | PASS |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO — identical to parent |
| G3 laser-off control | `P4_lez_kin_ic6_off` | PASS |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
<pending>

## Retracted
nothing
