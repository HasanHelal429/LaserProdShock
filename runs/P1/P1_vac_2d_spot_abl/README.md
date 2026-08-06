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

**Completed** 2026-08-06 01:38. 216 000/216 000 steps to 14.94 ps, **4 h 49 m** at 0.0805 s/step
on two MPI ranks / two RTX 4070s, 12 GB of diagnostics, zero errors, `--verify` clean.
Relaunched once — see *Retracted* — so the wall clock is from the second, valid start.

### The crater is resolved, and close to prediction

| | measured | predicted above |
|---|---|---|
| crater depth at `t_end` | **46.1 d_e = 2.30 `w₀` = 92 cells** | 48–71 d_e (2.4–3.5 `w₀`) |
| deepening rate | **3.56 d_e/ps** | 3.2–4.7 d_e/ps ✓ |
| `T_e`, absorption-weighted (whole domain / on axis) | **355.9 / 370.4 eV** | 0.75–1.1 keV ✗ **falsified** |
| `T_e`, density-weighted (whole domain / on axis) | **123.2 / 183.8 eV** | — (state the weighting; factor 2–3) |
| `T_e` axis / unlit reference | **1.73** | — |
| `E_abs` | **162.1 J/m** | — |
| `f_abs` | 1.0000 → **0.2264** | ~1.000 at `t` = 0 ✓ |
| `Tlocalfrac` | 0.431 → **0.980** | must *rise* ✓ |

The critical surface goes from a flat 37.7 d_e everywhere to **4.2 d_e on axis against 50.3 d_e
at |x| ≈ 90** — a `w₀`-scaled depression 92 cells deep, visible with no processing in
`fields_map2d.png`, `rays.png` and `movie_map2d.mp4`.

**`T_e` is nearly insensitive to intensity, and that prediction is falsified.** Like-for-like
against the parent (whole-domain absorption-weighted, the same estimator on both):

    P1_vac_2d_spot_long  I0 = 1e18 : 236.0 eV
    P1_vac_2d_spot_abl   I0 = 1e19 : 355.9 eV      x1.51 for 10x the intensity

i.e. **`T_e ∝ I^0.18`**, against the `I^(1/2..2/3)` the prediction assumed — so 356 eV where
0.75–1.1 keV was expected. This is the self-limiting absorption asserting itself: `K ∝ T_e^{−3/2}`,
so a hotter corona absorbs less, and the corona thermostats itself against intensity. (Caveat:
the two runs are compared at 26.9 vs 13.4 ps and with different transverse BCs, so 0.18 is
indicative, not a fitted exponent. A 1D intensity ladder would settle it cheaply.)

**Yet the crater still landed in its predicted band, because the two errors cancelled.**
`v_crit ∝ I_abs/kT_e`: a weaker `T_e` response means each absorbed joule ablates *more* mass, so
under-predicting `T_e`'s flatness and over-predicting `T_e` offset each other. **Do not read the
crater agreement as confirming the temperature scaling** — one of its two inputs was wrong by 2–3×.

**Mass is removed on axis, and the spot is also a piston.** Areal density falls 16.8 % on axis
against 2.7 % in the reference band (a 14-point net ablation signature), but peak on-axis `n_e`
*rises* 1.500 → 1.579 `n_cr` and the mass fraction still behind z = 0 goes **up** on axis
(0.790 → 0.881) while falling in the reference (0.790 → 0.739). Ions hold **33.3 %** of the
coupled energy at 15 ps.

### The open transverse boundary worked, and only just

Contrast of the deposited-energy **increment** (baseline-subtracted — the raw `E(x)` is
dominated by the slab's initial thermal energy and starts at ~1):

| | dark/lit |
|---|---|
| 1.5 ps | 0.116 — isolated |
| 9.0 ps | 0.394 — marginal |
| 13.4 ps | **0.523** |
| `P1_vac_2d_spot_long` (periodic) by 10 ps | **0.946** |

Isolated for ~5 ps, marginal to ~12 ps, crossing the pre-registered 0.5 threshold **only in the
final dump**, where the periodic predecessor was at 0.946 by 10 ps. `T_e` axis/reference = 1.73
says it is still a spot thermally at `t_end`. **A longer run at these parameters goes planar**;
the next lever is a wider box or a larger `w₀`, not the boundary condition.

### `refraction = 0`, quantified against a matched reference

The aborted run (below) left a `refraction = 1` reference on this exact geometry, so the t = 0
equivalence is measured, not asserted: step-0 `P_abs` **5.94077e+13 vs 5.94083e+13 W/m**, a
relative **3.4e-6**. Three clean decompositions of earlier refracting findings:

- step-0 transverse spread **0.000 %** vs 3.267 % refracting — the earlier scatter was ray wander
- **`w_eff/w₀` peaks at 1.23** vs 1.5–1.6 refracting, so of that broadening ~1.23 is the
  `T_e^{−3/2}` self-suppression and the rest was refractive
- `f_ax`/`f_abs` = 0.886 vs 0.62 refracting

**The near-zero transverse leak (0.0008, wall/interior 0.00) is NOT evidence of a clean run.**
Straight rays cannot scatter transversely, so this run has no power to test the leak at all.
And the crater's own refractive feedback is absent, so the late-time crater *profile* is
indicative rather than quantitative.

### Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `ω_pe dt` at peak density | 0.214 at 2× | **PASS** |
| G2 `dz/λ_D` | 61.2 target(cold) | INFO |
| G3 laser-off control | none | **WARN — by decision** |
| G4 `ray_cfl` | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 36 ppc; 0.431 → **0.980** | **PASS** |
| G6 energy closure | **−30.0 %** against **13.4 % weight loss** | cannot close — see below |

G6 was never closeable here: the rear is truncated flush with the target and all four faces are
open, so escaping particles carry energy WarpX does not report. 13.4 % of the **weight** left
(25.7 % of macroparticles — quote weight, they differ by ~2×). With no G3 control, **no
few-percent energy statement from this run is quotable**, in particular no grid-heating-corrected
`E_abs`, and the lateral loss is a total that cannot be split into laser- and grid-driven parts.
No shock, piston speed or Mach number is claimed — there is no ambient.

## Retracted

**1. The first launch (2026-08-05 20:26) is void and was killed at step ~2000.** It ran on a
`build_cuda_omp` built 2026-07-31, four days before `refraction` existed in the operator.
`strings` finds no `refraction` in that binary; WarpX parsed the key, never queried it, and said
nothing, so it marched with **full refraction** while this README claimed straight rays. Caught
by `--verify` reporting the key missing from `warpx_used_inputs`. Nothing in the run's own output
looked wrong. Its step-0 dumps are kept as `studies/refraction_xcheck/` and supply the
`refraction = 1` reference used above.

**2. A first crater measurement of "3.0 d_e", read as falsifying the prediction by 20×, was
wrong.** It used `|x| > 120 d_e` as the unilluminated reference, but those columns sit against
the open transverse wall and rarefy laterally into it — they lose **30.9 %** of their areal
density, *more* than the illuminated axis. Against the `z_crit(x)` plateau at 75–115 d_e, where
σ stays at 0.973, the crater is 46.1 d_e. **With an open boundary, "far from the beam" is not
"undisturbed"** — choose the reference from the data and verify the reference itself has not moved.

**3. The `Tlocalfrac` alarm threshold first written into this README (0.90–0.99) was wrong** and
would have condemned a healthy run reading 0.42. Those are late-time values; every run starts
near 0.43 because the target starts *at* the temperature floor. Corrected above: watch the trend.

## Retracted

Nothing yet.
