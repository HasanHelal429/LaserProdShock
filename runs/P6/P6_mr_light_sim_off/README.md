# P6_mr_light_sim_off — G3 laser-off control for `P6_mr_light_sim`

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** How much of `P6_mr_light_sim`'s heating is the grid rather than the laser?
**Expected.** A background specific to this leg's grid -- it does not share one with any other leg.
**Falsified by.** A background identical to its parent leg's control despite the changed grid.

---

## What this run is

Identical to `P6_mr_light_sim` except `laser.intensity = 0`. Each P6 leg carries its own control because
the legs do not share a grid-heating background (`dz/lambda_D` differs between them).

## Geometry

Identical to `P6_mr_light_sim`.

## Result

NOT YET RUN.

## Retracted

Nothing yet.
