# P1_vac_2d_spot_abl — a finite laser spot ablating a target, built so the ablation is *visible*

**Phase.** 1, `TEST_PLAN.md` §7.2 (H5)
**Question.** Does a ray-traced laser spot in this operator bore a crater with a resolvable
shape — and can a finite spot be held together long enough to watch it, which neither
`P1_vac_2d_spot` nor `P1_vac_2d_spot_long` managed?
**Expected.** An on-axis crater **48–71 d_e deep** at `t_end` = 14.94 ps (2.4–3.5 `w₀`,
96–142 cells) in a 200 d_e slab, with the transverse contrast of absorbed power *preserved for
the whole run* (`spot_isolation.py` dark/lit staying **< 0.2**, against 0.098 → **0.946** by
10 ps in the periodic predecessor). Absorption-weighted `T_e` = 0.75–1.1 keV.
**Falsified by.** dark/lit **> 0.5** at any time — open transverse faces would then fail to
hold a spot too, and a finite spot in this model is unaffordable rather than merely awkward.
Separately falsified *as an ablation run* if the crater is under ~1 `w₀` = 20 d_e deep, which
would put the `v_crit ∝ I^(1/3..1/2)` scaling wrong and mean the intensity must go up again.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
                  #########~~~~~~~
      ^                                                                ^
      open                                                          open
      z = -500                                                  z = +1100

  #  target flat top : 1.5 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  x  transverse     : -160 .. 160 d_e, boundaries open/open
  grid              : 640 x 3200 cells, dz = 0.5 d_e, dt = 0.06918 fs, 216000 steps = 14.94 ps
```

## Setup

Parent is [`P1_vac_2d_spot_long`](../P1_vac_2d_spot_long/README.md). Three changes, each
forced by a **measurement on that run** rather than by taste — all four numbers below come
from its `laserdep_profile` dumps (RESULTS 2026-08-05):

| measured on the parent | value |
|---|---|
| on-axis critical-surface recession `v_crit` | **1.5 d_e/ps** (37.7 → 0.3 d_e over 26.9 ps, linear) |
| absorption-weighted `T_e` | **saturates at 236 eV** from 3 ps on (52 eV at t = 0) |
| ⇒ `v_th,e` / `c_s` | 38 / 8.6 d_e/ps |
| 1e-3 n_cr on-axis front | 162 → **663 d_e** over 26.9 ps |

**1. Transverse boundaries periodic → `open`.** The one change that matters, and it replaces
a box-size fix that cannot be bought at any price. A periodic box holds a spot only while the
electron thermal excursion has not crossed half the pitch, so contrast survives to
`t ≈ (L_t/2 − 1.5w₀)/v_th,e`, while the crater deepens at `v_crit`. Wanting both gives

    L_t/2  ≳  (v_th,e / v_crit) · D  +  1.5 w₀        for a crater of depth D

and the measured ratio is **`v_th,e/|v_crit|` = 23**. Both speeds scale as `√T_e`, so *the
ratio, and hence the required box, is independent of intensity* — cranking the laser buys
depth and heat in the same proportion. A crater one waist deep already needs ±490 d_e; the
48–71 d_e wanted here needs **±1130 to ±1660 d_e**, i.e. 7–10× this run's transverse cell
count. So the boundary changes instead. With `open` (pec fields + absorbing particles, the
combination Phase 0 validated axially) the laterally streaming hot electrons *leave* rather
than accumulate, and contrast is preserved by construction.

The price is real and is quoted rather than hidden: lateral hot-electron loss to a wall is a
sink a wide real target would not have, so **this run understates retained energy where a
periodic run overstates confinement.** Opposite signs, and only this one is measurable from
inside the run.

**2. Peak intensity 1e18 → 1e19 W/m².** What buys ablation depth per unit wall clock.
`a₀ = 0.028`, so the run stays non-relativistic and inverse bremsstrahlung remains the right
absorption model. Not pushed further: at 1e20 the hot-electron preheat crosses a 200 d_e slab
in under 2 ps, which would puff the whole target and destroy the crater as a *shape*.

**3. Target 400 → 200 d_e thick.** Only **37 d_e of the 400 was consumed in 27 ps** — the rest
was inert mass in the particle loop, which is the observation that prompted this run. 200 d_e
still leaves 2× margin over the predicted crater, and that margin is load-bearing: the
operator's known exit-boundary overshoot deposits a full RK4 step past the far face and reads
**+24.9 %** high in the clamped final cell, so a *holed* target would fire that bug on axis.

Unchanged on purpose: `w₀` = 20 d_e, `Z_eff·lnΛ` = 5×5, `dz` = 0.5 d_e, `cfl` = 0.35, 36 ppc,
`ray_cfl` = 0.25, `L_n` = 60 d_e, **full refraction**.

- **`L_n` = 60 d_e is what lets this run ignore the turning point.** At this scale length the
  ray is extinguished ~15 d_e *before* the critical surface and 0.000 % of `P_abs` lands at or
  below it (RESULTS 2026-07-30), so turning-point fidelity — and G4's `ray_cfl` sensitivity —
  is not what this run rests on. `τ` through the flat top is 706.
- **Full refraction (`refraction = 1`, the default) despite the 3.2× cheaper straight-ray mode**
  added 2026-08-04. That mode is *exact* for a plane-stratified target but is blind to exactly
  what this run manufactures: on a merely **12.5 %** corrugated front it put the total **+8.5 %**
  high and collapsed the transverse contrast of `P_abs` from 4.086 to **0.089**. A laser-bored
  crater is a far steeper corrugation. (A matched `refraction = 0` companion would *measure*
  that error in a real crater instead of an artificial one — cheap, worthwhile, out of scope.)
- **lnΛ held at the constant 5.0**, not switched to the physical per-cell `coulomb_log_mode = ib`
  (which would raise it to ~7.3 in a keV corona, ~1.45× in absorption). Three things already
  change here, and `Z_eff·lnΛ` is a very strong knob to move in small steps.
- **Ray-path dump on** (`ray_intervals = 21600`, `ray_stride` 16, `ray_step_stride` 40 → ~40
  rays × 320 points ≈ 0.9 MB per dump, 11 dumps). This is the first production run to carry it:
  read with `scripts/plot_rays.py --dump` to see rays steering into the crater as it forms.

## Cost

640 × 3200 = **2.05e6 cells**, **35.2e6 macroparticles**, 216 000 steps → 14.94 ps.

**ESTIMATE ONLY — not benchmarked.** Scaled from `P1_vac_2d_spot_long` (0.1033 s/step, one
RTX 4070): cells ×1.33, particles ×1.31, ray-march steps ×1.33 ⇒ ~0.137 s/step ⇒ **~8.2 h**.
CLAUDE.md records a **4× error** from exactly this kind of scaling, because cell count
dominates more than a particle×step product allows for — so **benchmark a 2000-step slice
before believing this**. Disk ≈ **14 GB** (diag1 3 × 2.0 GB, diag_fields 41 × 124 MB,
diag_phase 9 × 57 MB, profile 11 × 206 MB), against 83 GB free.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `ω_pe dt` at peak density | 0.152 at 1.5 n_cr, 0.214 at 2× | **PASS** (budget 1.2) |
| G2 `dz/λ_D` (target / ambient) | 61.2 target(cold) / no ambient | INFO — under-resolved by construction |
| G3 laser-off control | **none** | **WARN — deliberately open, see below** |
| G4 `ray_cfl` check | 0.25; interior critical surface exists but carries 0.000 % of `P_abs` at `L_n` = 60 | PASS |
| G5 ppc / `Tlocalfrac` | 36 ppc, `local`; bias ≲ 3.5 % | PASS — watch `Tlocalfrac` |
| G6 energy closure | post-run; quote transverse+axial loss beside it | POST |

**G3 is left open as a decision, not an oversight.** A matched intensity-0 control would double
the compute for this geometry, and the primary deliverable does not need one: the crater is
predicted 96–142 cells deep against an 11.8 % per-cell shot-noise floor, so its shape is not
the marginal signal a control exists to adjudicate (that service was for the planar run's 5 %
ripple). What is therefore **not quotable from this run**: (1) any few-percent energy statement,
in particular a grid-heating-corrected `E_abs`; (2) a *decomposition* of loss through the new
open transverse faces into laser-driven and grid-driven parts — the total is measurable, the
split is not; (3) the sign-of-net-KE discriminator.

## Result

*Not yet run.*

## Retracted

Nothing yet.
