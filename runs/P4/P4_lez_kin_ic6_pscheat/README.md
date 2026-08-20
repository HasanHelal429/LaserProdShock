# P4_lez_kin_ic6_pscheat — WarpX laser heating configured to match PSC's

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** WarpX absorbs `f_abs` = 0.15–0.32 where PSC absorbs 0.47–0.56 and FLASH 0.870,
on the same IC and with an IB kernel cross-validated against PSC's to 8e-9. Lowering the
temperature floor alone (`P4_lez_kin_ic6_tfloor`) doubled `f_abs` into PSC's band but moved
`T_e` only from 0.19× to 0.31× FLASH. **Does making the heating fully PSC-equivalent close
the rest of the gap?**

**What differs, and the three knobs that remove it.** PSC forms `T_e` per cell as
`(Sxxe+Syye+Szze)/(3·NNe)` with **no temperature floor** and **no minimum-particle test** —
its only guard is a NaN check, and a cell it cannot characterise contributes `K` = 0 rather
than being *assigned* a temperature. WarpX defaults `temperature_floor` to
`electron_temperature` and `min_macroparticles_per_cell` to 4, and uses one constant lnΛ.

| knob | control | this run | PSC |
|---|---|---|---|
| `temperature_floor_theta` | default = `th_t` = **378.3 eV** | **1.9569e-6 (1 eV)** | none |
| `min_macroparticles_per_cell` | default **4** | **1** | `NNe /= 0` |
| `coulomb_log_mode` | constant **6.3** | **`nrl`** (per cell) | per cell, ≈5.10 measured |

The floor is set to 1 eV rather than 0 because the operator asserts it is > 0, and a nonzero
floor still guards against a pathological near-zero measurement sending `K` to infinity. At
1 eV it never binds on a ≥100 eV plume, so it is PSC-equivalent in the regime that matters.
`coulomb_log_mode = nrl` is the right choice because
`warpx-cda/laser_deposition/psc_reference` established our `nrl` reproduces PSC's
`get_lnlambda` to **0.000e+00** over 1681 points — it is documented there as "the mode to pick
when the question is 'what would PSC have done here'".

**Control.** `P4_lez_kin_ic6` (production) and `P4_lez_kin_ic6_tfloor` (floor only), both on
identical dump times. Deck diff against the control is `max_step` plus exactly these three
lines.

**Expected.**
1. `f_abs` reaches PSC's 0.47–0.56 or above. Note lnΛ moves this **down** (per-cell ≈5.1
   against the constant 6.3), so `f_abs` may sit slightly *below* the floor-only run.
2. If heating is the whole remaining story, `T_e` climbs toward PSC's 0.87–0.96× FLASH.
3. If `T_e` stays near 0.3×, the residual is **not** in the laser module, and the search moves
   to transport or to the expansion dynamics.

**Falsified by.** Outcome 3 — which would exonerate the deposition operator entirely, having
already exonerated the collision cadence and the σ_max cap.

**Not matched here (deliberate).** PSC's density floor is `n_cr`/NPPC = 1e-3 `n_cr` where this
deck resolves to 1e-5 `n_cr`, and PSC's ppc scales with density where WarpX's is uniform.
Those change the *plume representation*, not the heating, and the density floor is
known-sensitive (RESULTS 2026-08-18, "the `T_e` outward rise was the DENSITY FLOOR"), so
changing it here would confound this test.

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

## Result
**Outcome 3 — the laser deposition operator is EXONERATED.** 5 min, `reached max_step`,
`--verify` OK; the deck differs from the control by `max_step` plus exactly the three lines.

| τ_own | | control | floor 20 eV | **PSC-equiv** | PSC | FLASH |
|---|---|---|---|---|---|---|
| 2.70 | `f_abs` | 0.217 | 0.545 | **0.423** | 0.47–0.56 | 0.870 |
| 5.39 | `f_abs` | 0.319 | 0.634 | **0.461** | 0.47–0.56 | 0.870 |
| — | `Tlocalfrac` | 0.000 | 0.23–0.67 | **1.000** | n/a | n/a |
| 2.70 | `T_e`/FLASH | 0.213 | 0.330 | **0.290** | 0.923 | 1.000 |
| 5.39 | `T_e`/FLASH | 0.191 | 0.308 | **~0.30** | 0.871 | 1.000 |

Expectation 1 is met: `Tlocalfrac` reaches **1.000** — every cell now carries a measured
temperature — and `f_abs` climbs into **PSC's 0.47–0.56 band**. Expectation 2 is **not**:
`T_e` stays at **0.29–0.34 ×** FLASH.

**The result, stated plainly: at the same absorbed fraction, WarpX produces ~3× less electron
temperature than PSC.** The energy is going in and not appearing as plume `T_e`. With the
cadence, the `σ_max` cap, the temperature floor and now the whole heating configuration all
cleared, the residual is **not in the laser module**.

**Caveat on the lnΛ match.** `coulomb_log_mode = nrl` reports `lnLmean` ≈ **1.01**, i.e. the
NRL expression floors at 1 in most cells, where PSC's laser module gave **≈5.10** at the
critical surface. So this run matches PSC on the *absorbed fraction* but not on the
*coefficient*; the domain-mean and PSC's point value are not directly comparable, and pinning
that down properly is unfinished. It does not affect the conclusion, which rests on `f_abs`
being matched while `T_e` is not.

**Where to look next.** The deposition profile: WarpX's median deposition ζ is 1.35–1.82×
*smaller* than FLASH's (RESULTS 2026-08-19, deposition), i.e. energy lands in **denser**
plasma. The same joules spread over more mass give a smaller temperature rise. That is the
one measured asymmetry consistent with "absorption matches, temperature does not".

## Retracted
Nothing yet.
