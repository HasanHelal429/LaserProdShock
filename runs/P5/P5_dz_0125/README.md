# P5_dz_0125 — dz ladder, rung dz = 0.125 d_e,cr (88160 cells)

**Phase.** 5, `TEST_PLAN.md` §13. **Read the three dz rungs as a set** (the dz = 0.5 rung is
`P5_raycfl_025`, already run).
**Question.** The `ray_cfl` ladder did not converge. Does refining the **grid** converge,
as the 2026-08-30 diagnosis predicts it must?
**Expected.** `E_abs` settles across dz = 0.5 → 0.25 → 0.125 while it did not across
`ray_cfl` = 0.50 → 0.025. At this rung the density scale length at the critical crossing is
**47.6 cells** (it is 11.9 at dz = 0.5).
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

**Cost: 16x the dz = 0.5 rung, ~95 min.**

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
  grid              : 88160 cells, dz = 0.125 d_e, dt = 0.02471 fs, 81200 steps = 2.007 ps
```

## Result

**Ran 2026-08-31, job 57795781, COMPLETED exit 0, `--verify` OK. `E_abs` = 9.9956e4 J.**

**The prediction in this README failed.** dz = 0.5 → 0.25 → 0.125 gives 9.5601 / 9.6534 /
9.9956 e4, increments **+0.98 % then +3.55 %** — the increment *grows*, which is this
run's own stated falsification criterion.

The reason is instructive rather than fatal: refining dz did **not** buy proportional layer
resolution. `L_n` at the crossing went 16.2 → 16.6 → 28.9 cells for a **4×** finer grid, so
`1−r < 0.01` stayed at 0.16 → 0.17 → 0.29 cells and **no rung ever had a single cell in
`0.99 < r < 1.01`**. The lifted FLASH profile's critical region sharpens as it is resolved.
Reaching the ~1-cell criterion would need dz ≈ 0.08 `d_e` (137 750 cells, ~10 h for 2 ps);
the `n_floor` clamp region would need dz ~ 1.4e-10 m. **Grid refinement is not a lever on
this initial condition.**

## Retracted

Nothing.
