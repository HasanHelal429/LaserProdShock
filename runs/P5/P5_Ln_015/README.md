# P5_Ln_015 — Tier 3 regime map

**Phase.** 5, `TEST_PLAN.md` §13. **Read each Tier 3 family as a set, never one run alone.**
**Question.** Does absorbed energy depend on the corona scale length at fixed `ray_cfl`, and does it settle once the `1−r < 0.01` layer clears ~1 cell?
**Expected.** A threshold. `E_abs` moves systematically with `L_n` and stops moving once the layer is resolved, giving a quantitative admissibility criterion.
**Falsified by.** `E_abs` flat across `L_n` = 10 → 60 `d_e`. That would mean the operator does not care about layer resolution and the Tier 1 correlation was coincidence.

---

## What this run is

TIER 3c REGIME MAP -- corona scale length L_n = 15.0 d_e, everything else held.
    This is the ONE knob that moves critical-layer resolution on an analytic corona: for an
    exponential anchored at n_cr, L_n at the crossing IS the scale length, independent of the
    target's peak density. The 2026-08-31 Tier 1 result found that the only ladder which
    converged to the noise floor was the only one with ~1 cell across the 1-r < 0.01 layer
    (0.95 cells, L_n = 29.8 d_e = 94.5 cells), while every lifted-FLASH rung had 0.16-0.29
    cells there and drifted. At dz = 0.5 d_e this rung puts 15.0 d_e = 30 cells
    across L_n, i.e. 0.30 cells across 1-r < 0.01.
    THE QUESTION: where is the threshold? If E_abs at fixed ray_cfl is flat across L_n = 10,
    15, 29.8, 60 then the operator does not care and the Tier 1 correlation was a coincidence.
    If it moves systematically and settles once the layer clears ~1 cell, we have a
    quantitative admissibility criterion for the module -- which is the deliverable of this
    tier, and directly decides whether a LATER FLASH handoff (0.2 or 0.4 ns, whose corona has
    had longer to expand and is therefore shallower) is the strategy that makes P5 work.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 15 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

**Ran 2026-08-31/09-01 (jobs 57803769, 57804731), COMPLETED exit 0, `--verify` OK.**

The scale-length sweep at fixed `ray_cfl` moved `E_abs` **2.5×** (6.99e4 / 9.16e4 / 1.348e5
/ 1.781e5 at `L_n` = 10 / 15 / 29.8 / 60 `d_e`). **That is optical depth, not resolution** —
a longer corona holds more plasma at absorbing densities. Reading it as a resolution test is
withdrawn; see the fine rungs for what replaced it.

The isolation experiment is the drift when *only* `ray_cfl` moves: **+11.49 %** at 0.20
cells across the `1−r < 0.01` layer, **−0.51 %** at 1.20 cells. With the analytic ramp
(+3.27 % at 0.60) and the lifted table (+9.79 % at 0.16) that is a monotonic curve crossing
the 0.80 % seed floor at ~1 cell — the measurement gate **G8** is built on.

## Retracted

Nothing.
