# P5_raycfl_off — G3 laser-off control for the `ray_cfl` ladder

**Phase.** 5, `TEST_PLAN.md` §13.
**Question.** Across the ladder the particles gained **1.48–2.07×** the energy the laser
deposited, at **zero** particle loss. How much of that is the known grid heating, and how
much — if any — is the operator creating energy at the unresolved critical layer?
**Expected.** With `intensity = 0` no ray is traced at all, so everything this run gains is
grid heating. Subtracting it from each rung's `ΔKE` closes G6 for the ladder for the first
time.
**Falsified by.** Nothing — this is a measurement, not a hypothesis. But if the laser-off
heating **exceeds** the rungs' excess, the excess is not operator energy creation; if it
falls well short, the operator is creating energy and the amount is now known.

---

## Why it did not exist already

The project's existing G3 controls (`P5_flashic_off`, `P5_full_off`) are the 9 139 500-step
legs — **450× longer** than a ladder rung. Grid heating accumulates with step count, so they
cannot be rescaled onto 20300 steps; a matched control has to be run at the ladder's own
duration. It costs about five minutes and nobody had done it.

`tests/test_structures.py` enforces that this deck differs from `P5_raycfl_025` in the drive
alone, which is what makes the subtraction meaningful.

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
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-08-31 as target `rampcfl`)*

## Retracted

Nothing.
