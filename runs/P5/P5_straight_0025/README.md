# P5_straight_0025 — Tier 3 regime map

**Phase.** 5, `TEST_PLAN.md` §13. **Read each Tier 3 family as a set, never one run alone.**
**Question.** Does the straight-ray (analytic Snell) mode converge in `ray_cfl` where the refracting RK4 march did not?
**Expected.** If flat, the defect is in the RK4 approach to the turning surface rather than in the analytic near-critical layer, and straight-ray becomes the recommended production mode for stratified targets.
**Falsified by.** This ladder drifting like the refracting one. That would place the defect in the analytic layer itself, which both modes share.

---

## What this run is

TIER 3e -- refraction = 0 (straight rays + analytic Snell), rung ray_cfl = 0.025.
    Replaces the RK4 eikonal trace with straight rays carrying the Snell invariant
    analytically. It is exact for a plane-stratified target, much cheaper, and it is what PSC
    does -- so this both isolates the RK4 marcher and tests a cheaper production mode.
    WHY IT MIGHT MATTER HERE: the Tier 1 divergence is localised at the turning point, and the
    two modes reach the turning surface by different routes -- the refracting march integrates
    to it, the straight-ray mode places it analytically at n_m = n_cr cos^2(theta0) (= n_cr at
    normal incidence). If this mini-ladder is flat where the refracting one drifted +18.3%, the
    defect is in the RK4 approach to the surface rather than in the analytic layer itself, and
    straight-ray becomes the recommended production mode for stratified targets.
    CAUTION from CLAUDE.md: a stale `refraction` key once went unnoticed for 2000 steps, so
    --verify matters more than usual on these three.

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
