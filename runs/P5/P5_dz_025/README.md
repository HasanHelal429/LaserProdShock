# P5_dz_025 — dz ladder, rung dz = 0.25 d_e,cr (44080 cells)

**Phase.** 5, `TEST_PLAN.md` §13. **Read the three dz rungs as a set** (the dz = 0.5 rung is
`P5_raycfl_025`, already run).
**Question.** The `ray_cfl` ladder did not converge. Does refining the **grid** converge,
as the 2026-08-30 diagnosis predicts it must?
**Expected.** `E_abs` settles across dz = 0.5 → 0.25 → 0.125 while it did not across
`ray_cfl` = 0.50 → 0.025. At this rung the density scale length at the critical crossing is
**23.8 cells** (it is 11.9 at dz = 0.5).
**Falsified by.** `E_abs` continuing to climb with dz as it did with `ray_cfl`. That would
put the defect in the operator's near-critical branch rather than in the grid's ability to
represent the layer, and would make the code fix mandatory before any P5 physics.

---

## Why this is the decisive test

The diagnosis (RESULTS 2026-08-30) is that the critical layer is **sub-grid**: at
dz = 0.5 `d_e` the `1−r < 0.01` layer is 0.119 cells and no cell has `0.99 < r < 1.01`, so
refining `ray_cfl` marches ever more finely over a multilinear interpolation *between two
cells straddling critical* — a straight line the grid invented — and approaches a limit set
by the operator's `n_floor` clamp rather than by the plasma.

If that is right, the cure is cells, not steps, and this ladder converges. If it is wrong,
this ladder diverges too and the problem is in the operator.

Everything except `dz` is held: same lifted FLASH IC, same `ray_cfl` = 0.25, same physical
duration (dt scales with dz at fixed `cfl`, so `max_step` scales inversely and `t_end` is
unchanged at 2.007 ps), same diagnostics cadence in physical time.

**Cost: 4x (2x cells x 2x steps) the dz = 0.5 rung, ~25 min.**

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 44080 cells, dz = 0.25 d_e, dt = 0.04943 fs, 40600 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-08-31 as target `dzladder`)*

## Retracted

Nothing.
