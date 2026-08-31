# P5_ramp_0025 — analytic-ramp `ray_cfl` ladder, rung `ray_cfl` = 0.025

**Phase.** 5, `TEST_PLAN.md` §13. **Read the five rungs as a set, never one alone.**
**Question.** Does the `ray_cfl` ladder converge on an **analytic** corona, where it did not
on the lifted FLASH table?
**Expected.** Convergence. Upstream's `run_convergence` converged, and `ACCURACY.md` says
why outright: multilinear density interpolation is **exact for a linear ramp**. The analytic
exponential corona has `L_n` = 29.8 `d_e` = **59.6 cells** at the crossing against the lifted
table's 11.9, on the same grid with the same operator.
**Falsified by.** This ladder diverging like the lifted one. That would exonerate the FLASH
table, put the defect in the near-critical branch for every profile, and make the code fix
the phase's blocking item.

---

## What this isolates

One variable: the **shape of the corona at the critical surface**. Same grid (dz = 0.5
`d_e`, 22040 cells), same duration (20300 steps = 2.007 ps, identical to every raycfl rung),
same target, same collisions, same ppc, same seed. Only `corona_profile` differs —
`exponential` here, `flash_table` there.

That makes the two ladders directly subtractable, which is the point: the lifted-IC ladder
moved `E_abs` +18.4 % over 0.50 → 0.025 and was still climbing. If this one is flat, profile
steepness is the whole story and the analytic-IC arm (`P5_full`) is usable where the lifted
arm is not — a result about **which initial condition P5 can use**, not just about numerics.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-08-31 as target `rampcfl`)*

## Retracted

Nothing.
