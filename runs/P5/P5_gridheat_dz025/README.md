# P5_gridheat_dz025 — grid-heating probe (laser off)

**Phase.** 5, `TEST_PLAN.md` §13. Read against `P5_raycfl_off`.
**Question.** Does the spurious energy gain scale with dz, as grid heating must?
**Expected.** A substantially smaller gain at dz = 0.25, since dz/lambda_D halves from 58 to 29.
**Falsified by.** A gain independent of dz. That would rule out Debye under-resolution as the mechanism and point at something else entirely — a far more serious finding.

---

## This is deliberately NOT a G3 control, and is named so

`tests/test_structures.py` requires any run whose directory ends `_off` to be a valid G3
control: identical to its `controls.physics_run` in everything but the drive. These probes
**deliberately break that** — one changes the seed, the other the grid — because their job
is to characterise the grid heating itself, not to subtract it from a physics run. Naming
them `P5_gridheat_*` and declaring no `physics_run` keeps the G3 invariant meaningful
rather than quietly weakening the test that enforces it.

## Why they exist

`P5_raycfl_off` — identical deck, `intensity = 0`, so no ray is traced and **no energy is
supplied** — nonetheless gained **+3.53e4 J** over 20 300 steps: `ΔKE` = −5.4e3 (the
particles do *not* heat) and `ΔE_field` = +4.07e4, growing **linearly** through the run.
That is 34 % of what the laser deposits into a ladder rung, and nothing bounds where it
stops. It sets a ceiling on how long any P5 leg can run before numerical heating dominates
the physics, and that ceiling is currently unmeasured.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 44080 cells, dz = 0.25 d_e, dt = 0.04943 fs, 40600 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-09-01)*

## Retracted

Nothing.
