# P5_ramp_005r — seed replicate of `P5_ramp_005`

**Phase.** 5, `TEST_PLAN.md` §13.
**Question.** How big is the run-to-run floor on `E_abs` at this deck and duration?
**Expected.** Small — `E_abs` is an integral and should be far steadier than `f_abs(0)`,
whose measured 1σ across seed alone is 10.4 %.
**Falsified by.** Nothing; it is a measurement. But if the seed-to-seed spread is
comparable to the ±1.4 % the analytic ladder scatters by, then **neither ray_cfl ladder is
resolving anything** at the fine end and both verdicts must be restated as "below the noise
floor" rather than "not converged".

---

## Why a convergence verdict needs this

A ladder is read by whether its increments shrink. That test is meaningless until the
increments are compared against the floor. The analytic-ramp ladder's increments change
sign (+0.96 / +2.76 / −0.90 / +1.41 %), which already suggests scatter rather than drift —
this run says how much scatter is available for free.

It does **not** apply to the lifted-IC ladder's +18.4 % total, which is far too large and
too systematically one-signed to be noise.

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

*(pending — submitted 2026-08-31)*

## Retracted

Nothing.
