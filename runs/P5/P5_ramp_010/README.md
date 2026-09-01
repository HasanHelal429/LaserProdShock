# P5_ramp_010 — analytic-ramp `ray_cfl` ladder, rung `ray_cfl` = 0.10

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

**Ran 2026-08-31, job 57797221, COMPLETED exit 0, `--verify` OK. `E_abs` = 1.3856e5 J.**

The five-rung ladder gives 1.3356 / 1.3484 / 1.3856 / 1.3730 / 1.3925 e5 — increments
+0.96 / +2.76 / −0.90 / +1.41 %, against a measured seed floor of **0.80 %**
(`P5_ramp_005r`). Three of four are 1.1–1.8× the floor and they **change sign**: that is
scatter, not drift. **Consistent with convergence to within ~1–3 %.** This ladder's
critical layer is 0.95 cells across `1−r < 0.01` (94.5 cells across `L_n`) — the only one
of the three ladders that resolves it, and the only one that sits at the floor.

## Retracted

Nothing.
