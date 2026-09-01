# P5_under_025 — Tier 3 regime map

**Phase.** 5, `TEST_PLAN.md` §13. **Read each Tier 3 family as a set, never one run alone.**
**Question.** With **no interior critical surface at all**, is the operator convergent in `ray_cfl`?
**Expected.** Flat to the 0.80 % seed floor. Upstream states uniform slabs are exact at any `ray_cfl` because no ray turns.
**Falsified by.** Any drift above the seed floor. That would mean the problem is broader than the turning point and the whole absorption model is in question — a far more serious finding than Tier 1's.

---

## What this run is

TIER 3f -- THE CLEAN CONTROL: an UNDERDENSE target, so no ray ever turns. ray_cfl = 0.25.
    Target and corona both capped below n_cr, so there is no interior critical surface, no
    1/sqrt(1-n/n_cr) singularity anywhere along the ray, and nothing for the analytic
    near-critical layer to do. Upstream states that uniform slabs are exact at any ray_cfl for
    exactly this reason, and that is why the defect hid for so long: the existing
    studies/exit_overshoot ladder ran 1.5 n_cr with no turning point.
    THE POINT: if this mini-ladder is flat to the 0.80% seed floor while the 10 n_cr lifted
    ladder drifted +18.3%, then the operator is sound everywhere EXCEPT the turning point and
    the defect is pinned to the near-critical branch -- which is the single cleanest statement
    this campaign can make about the module. If it ALSO drifts, the problem is broader than the
    turning point and the whole absorption model is in question.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 0.5 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

**Ran 2026-08-31 (job 57808833), COMPLETED exit 0, `--verify` OK.**

**`E_abs` = 2.0067e5 at `ray_cfl` = 0.25, 0.05 AND 0.025 — identical to five significant
figures.** Not "within the seed floor"; identical. A 10× change in arc-length step changes
absorbed energy not at all. Per-cell differences exist at the 2e14 level but cancel to a net
−3.9e12 (0.002 %) — PIC-noise redistribution with no net effect.

This is the cleanest statement the campaign makes about the module: **with no critical
surface to cross, the ray march is exactly convergent.** Combined with Tier 2 (K correct
term by term, Beer–Lambert residual 0.000 %), every failure measured is localised to the
near-critical branch.

## Retracted

Nothing.
