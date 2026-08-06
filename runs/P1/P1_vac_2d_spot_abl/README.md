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
2D  |  z = propagation axis (across), x = transverse (down)  |  lengths in d_e at critical density = 0.1676 um

        x = +160   (open)
       +----------------------------------------------------------+
  +160 |##########~~~~~~~                                         |
  +140 |##########~~~~~~~                                         |
  +120 |##########~~~~~~~                                         |
  +100 |##########~~~~~~~                                         |
   +80 |##########~~~~~~~                                         |
   +60 |##########~~~~~~~                                         |
   +40 |##########~~~~~~~                                         |<
   +20 |##########~~~~~~~                                         |<===
    +0 |##########~~~~~~~                                         |<=========
   -20 |##########~~~~~~~                                         |<===
   -40 |##########~~~~~~~                                         |<
   -60 |##########~~~~~~~                                         |
   -80 |##########~~~~~~~                                         |
  -100 |##########~~~~~~~                                         |
  -120 |##########~~~~~~~                                         |
  -140 |##########~~~~~~~                                         |
  -160 |##########~~~~~~~                                         |
       +----------------------------------------------------------+
        x = -160   (open)
        ^                                                        ^
        open                                                  open
        z = -200                                         z = +1100

  #  target flat top : 1.5 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0), drawn out to 1e-3 n_cr
  ' ' vacuum        : no ambient plasma
  <  laser          : gaussian, w0 = 20 d_e (1/e radius of INTENSITY), I0 = 1e+19 W/m^2 peak, enters the hi z face
                      bar length is proportional to the LOCAL intensity, so the beam is drawn to scale against x
  grid              : 640 x 2600 cells (x by z), dz = dx = 0.5 d_e, dt = 0.06918 fs, 216000 steps = 14.94 ps
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

**3. Target 400 → 200 d_e thick, and no vacuum behind it.** Only **37 d_e of the 400 was
consumed in 27 ps** — the rest was inert mass in the particle loop, which is the observation
that prompted this run. 200 d_e still leaves 2× margin over the predicted crater, and that
margin is load-bearing: the operator's known exit-boundary overshoot deposits a full RK4 step
past the far face and reads **+24.9 %** high in the clamped final cell, so a *holed* target
would fire that bug on axis. The lo face is also pulled in to **−200 d_e, flush with the
target's rear face** — the rear-truncation CLAUDE.md validated (front-side ion count within
0.11 %, `E_abs` within 0.9 %, target `p_z` within 0.54 %). It removes 600 of 3200 axial cells
(**18.8 %**) and costs no particles, since that region held none. Two caveats carried
deliberately: truncating **costs the energy budget** (6.13 % weight loss by 30 ps vs 1.14 %
untruncated), so G6 cannot be closed tightly here; and the truncation must be validated by
**core decoupling** — the width of slab still at its initial density between the two
disturbance fronts — never by asking the boundary density to stay put, since that boundary is
a free surface and *must* rarefy.

Unchanged on purpose: `w₀` = 20 d_e, `Z_eff·lnΛ` = 5×5, `dz` = 0.5 d_e, `cfl` = 0.35, 36 ppc,
`ray_cfl` = 0.25, `L_n` = 60 d_e.

- **`L_n` = 60 d_e is what lets this run ignore the turning point.** At this scale length the
  ray is extinguished ~15 d_e *before* the critical surface and 0.000 % of `P_abs` lands at or
  below it (RESULTS 2026-07-30), so turning-point fidelity — and G4's `ray_cfl` sensitivity —
  is not what this run rests on. `τ` through the flat top is 706.
- **`refraction = 0` — straight rays, an accepted accuracy trade.** Every ray marches straight
  down the axis carrying the refraction analytically through the Snell invariant. It is *exact*
  for a plane-stratified target at any angle and 3.2× cheaper on the march. **What it costs
  here, so the figures are read correctly:** it is blind to transverse structure the *plasma*
  creates — on a deliberately 12.5 % corrugated front the total read **+8.5 %** high and the
  transverse contrast of `P_abs` collapsed 4.086 → **0.089**. Two consequences, and the
  distinction matters: **(1)** the Gaussian beam's *own* profile is untouched, because each
  column still receives its own incident intensity, so the spot stays localized and a localized
  crater still forms — that corrugated-front number is **not** the error bar on this run's
  contrast, because there *all* the transverse structure came from refraction whereas here it
  comes from the beam. **(2)** What *is* lost is rays bending into or out of the crater once it
  is deep, i.e. the crater's self-focusing feedback on its own drive. Expect the crater
  **narrower and deeper** than a refracting run would give (straight rays cannot be steered out
  of a concave surface), and treat the late-time crater *profile* as indicative rather than
  quantitative. A refracting companion on the identical crater is the clean way to bound this.
- **lnΛ held at the constant 5.0**, not switched to the physical per-cell `coulomb_log_mode = ib`
  (which would raise it to ~7.3 in a keV corona, ~1.45× in absorption). Enough already changes
  here, and `Z_eff·lnΛ` is a very strong knob to move in small steps.
- **Ray-path dump on** (`ray_intervals = 21600`, `ray_stride` 16, `ray_step_stride` 40 → ~40
  rays × 320 points ≈ 0.9 MB per dump, 11 dumps). Note it is *much less interesting* in this
  mode — a picket fence of straight lines rather than a bending bundle — so it is retained to
  document the mode, not to show refraction.

## Cost

640 × 2600 = **1.66e6 cells**, **35.2e6 macroparticles**, 216 000 steps → 14.94 ps.

**ESTIMATE ONLY — not benchmarked.** Scaled from `P1_vac_2d_spot_long` (0.1033 s/step, one
RTX 4070): cells ×1.08, particles ×1.31, and the march ×0.34 (paths 1.08× longer but
`refraction = 0` is 3.2× cheaper) ⇒ ~**0.12 s/step** ⇒ **~7.3 h**. CLAUDE.md records a **4×
error** from exactly this kind of scaling, because cell count dominates more than a
particle×step product allows for — so **benchmark a 2000-step slice before believing this**.

**Where the time actually goes, and why the two economies here are small.** Phase 1.5 already
cut the ray march to ~6 % of a driven 2D step, so `refraction = 0` removes at most **~4 %** of
the wall clock, and the rear truncation removes 18.8 % of the *cells* but no particles. The
dominant cost is the push and deposit over 35.2e6 macroparticles — 1.31× the parent — which
neither change touches. Against ~8.2 h for the untruncated refracting version, the two changes
together buy about **50 minutes**; the accuracy trade was taken for the physics question, not
for the clock.

Disk ≈ **13 GB** (diag1 3 × 2.0 GB, diag_fields 41 × 100 MB, diag_phase 9 × 57 MB, profile
11 × 167 MB), against 82 GB free — and the filesystem is at 96 %, so this is worth watching.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `ω_pe dt` at peak density | 0.152 at 1.5 n_cr, 0.214 at 2× | **PASS** (budget 1.2) |
| G2 `dz/λ_D` (target / ambient) | 61.2 target(cold) / no ambient | INFO — under-resolved by construction |
| G3 laser-off control | **none** | **WARN — deliberately open, see below** |
| G4 `ray_cfl` check | 0.25; interior critical surface exists but carries 0.000 % of `P_abs` at `L_n` = 60 | PASS |
| G5 ppc / `Tlocalfrac` | 36 ppc, `local`; bias ≲ 3.5 %; `Tlocalfrac` 0.431 at step 0 | PASS — watch the **trend**, see below |
| G6 energy closure | post-run; quote transverse+axial loss beside it | POST |

**G3 is left open as a decision, not an oversight.** A matched intensity-0 control would double
the compute for this geometry, and the primary deliverable does not need one: the crater is
predicted 96–142 cells deep against an 11.8 % per-cell shot-noise floor, so its shape is not
the marginal signal a control exists to adjudicate (that service was for the planar run's 5 %
ripple). What is therefore **not quotable from this run**: (1) any few-percent energy statement,
in particular a grid-heating-corrected `E_abs`; (2) a *decomposition* of loss through the new
open transverse faces into laser-driven and grid-driven parts — the total is measurable, the
split is not; (3) the sign-of-net-KE discriminator.

### `Tlocalfrac`: watch the trend, not the value

Corrected after launch, because the threshold first written into this README would have
condemned a healthy run. `Tlocalfrac` is the **n_e²-weighted** fraction of plasma whose `T_e`
was measured rather than floored (`w_local/w_total`, weight `n_e²`, `LaserDeposition.cpp` ~890),
so empty cells carry zero weight and vacuum *cannot* dilute it — which is exactly why a low
value looks alarming. But it is low at `t` = 0 in **every** run on disk, because the target
starts at 51 eV, i.e. at the floor, and it climbs as the target heats:

| run | first | max | ppc |
|---|---|---|---|
| `P1_vac_2d_spot_omp` | 0.432 | 0.860 | 36 |
| `P1_vac_2d_spot_long` | 0.432 | 0.954 | 36 |
| `P1_vac_2d_omp` (planar) | 0.432 | 0.998 | 36 |
| `P1_vac_1d_long` | 0.430 | 1.000 | 400 |
| `P1_vac_1d_thick` | 0.409 | 0.999 | 36 |

Note the **spot** runs plateau lower than the planar ones (0.86–0.95 vs 0.998), which is
expected rather than a defect: a spot heats only part of the target, so part of the `n_e²`
weight stays cold and floored for the whole run. The failure signature is therefore
`Tlocalfrac` **failing to rise, or falling back** — not its starting value. This run read
0.431 at step 0 and 0.423 at step 1860, on the family curve.

## Result

*Running.* Launched 2026-08-05 20:26 on two GPUs (2 MPI ranks, `-g 0,1`), queued behind the
KinShock `i0`/`i1` implicit runs by `scripts/queue_run.sh` (waited 3 h 34 m).

Measured at launch, to be replaced by the full result:

- **Decomposition worked.** `2 grids, smallest 320 x 2600, biggest 320 x 2600` — one maximal
  box per rank, split on x only. Both cards carry **9114 MiB** and, sampled over 15 s, **49 %**
  and **53 %** mean utilisation at 71–105 W. A single instantaneous sample read 0 % on device 1
  and looked like an idle card; it is a bursty workload, and only the average is meaningful.
- **0.0771 s/step** measured over a 60 s window (778 steps) ⇒ **~4.6 h**, against a ~7.2 h
  single-GPU estimate. Expect the true figure to be *longer*: cost grows during a vacuum run as
  the plume spreads over more cells (a 1D run went 526 → 10 800 occupied cells at flat particle
  count), and this window was taken at 0.13 ps.
- Neither card is saturated (~50 %, ~90 W of 200 W), consistent with the two ranks partly
  serialising on MPI synchronisation rather than overlapping — so the realised speedup is well
  under the 1.96× Amdahl ceiling, as expected.
- `f_abs` ≈ **0.42** at 0.13 ps (`Pabs` 2.5e13 W/m against 5.94e13 W/m incident).

## Retracted

Nothing yet.
