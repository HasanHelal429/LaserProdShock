# P1_vac_2d_spot_off — the gate-G3 laser-off control for the finite-spot run

**Phase.** 1, `TEST_PLAN.md` §7.2, gate **G3** (§6)
**Question.** How much of `P1_vac_2d_spot`'s particle-energy gain and transverse structure would
have happened with **no laser at all**, on that run's exact grid and ppc?
**Expected.** A net particle-KE change that is small and **negative**, as every control in this
campaign has been — the signature of ambipolar electron→ion transfer that cancels, not of grid
heating (which would be a net *gain* shared by both species). The planar 2D control at this same
36 ppc gave **−3.09 %** of its driven gain (against −0.066 % at 400 ppc in 1D), so a few-percent
excursion is expected here and is the error bar on any few-percent claim from the driven run.
**Falsified by.** A net **positive** particle-KE gain shared by both species — that is grid heating,
and it would mean gate G2 (`dz/λ_D` = 61.2, the unavoidable cold-target value) is not bounded at
2D-affordable ppc, invalidating the driven run's energetics rather than merely widening its error
bar.

## Geometry

Identical to `P1_vac_2d_spot` — 320 × 2200 cells, `z` ∈ [−400, +700] `d_e,cr` with `open` faces,
`x` ∈ [−80, +80] periodic, 36 ppc, 144 000 steps = 9.961 ps. The only difference in the rendered
deck is `laser_deposition.intensity = 0`.

## Setup

**Why it cannot be inherited from `P1_vac_2d_off`.** That control has 64 transverse columns and a
+1200 `d_e` axial face; grid heating depends on the grid and on the macroparticle statistics, and
this box has 5× the columns, so it needs its own control. `tests/test_structures.py` renders both
decks and diffs them line by line, which is why the `beam_profile = gaussian` / `beam_waist = 20 d_e`
lines are still present here: at `intensity = 0` every ray has `P0_ray = 0` and no ray is traced at
all, so the profile is inert, but the *deck* must differ in exactly one line or the G3 subtraction is
not controlled.

**Its second job is the transverse noise floor.** With 36 ppc split over two species, the per-cell
shot-noise floor on `n_e` is `1/√72` = 11.8 %. A Gaussian spot is *supposed* to imprint transverse
structure, so the only way to say which part of the driven run's structure is laser-driven is to
measure what this run produces with no beam — exactly the service `P1_vac_2d_off` performed for the
planar run, where it proved a 5 % ripple was shot noise rather than filamentation.

## Cost

Benchmarked on the driven deck at 0.142 s/step; with no ray march the cost is the non-laser part of
that, ~0.059 s/step, so ~2.4 h on one RTX 4070 against the driven run's ~5.7 h. The ratio is the
measured cost of the serial host-side ray march for 320 rays.

| | value |
|---|---|
| cells | 320 × 2200 = 704 000 |
| macroparticles | (fill in from `PN.txt`) |
| wall time | (fill in from `progress.log`) |

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.214 | pass |
| G2 `dz/lambda_D` (target) | 61.2 | this run is the test |
| G3 net particle-KE change | | post-run |
| G6 energy closure / weight lost | | post-run |

## Cost (measured)

144 000 steps in **2 h 48 m** on one RTX 4070 at 0.0702 s/step, against the driven run's
0.140 s/step. The ratio is the measurement: **50 % of a driven 2D step is the serial host-side
eikonal ray march** for 320 rays, and it is the reason a finite-spot run costs what it does.
26 823 000 macroparticles (5.0x `P1_vac_2d_off`), 320 x 2200 = 704 000 cells.

## Result

`--verify` OK. Zero errors, all 144 000 steps, t = 9.961 ps.

### 1. G3 passes: the net particle-KE change is NEGATIVE, as in every control here

| | value |
|---|---|
| net particle KE | **−3.325 J/m** (75.416 -> 72.091) |
| target electrons / ions | **−2.542 / −0.783 J/m** |
| electron *mean* KE | −4.8 % (1.22798e−17 -> 1.16953e−17 J) |
| ion *mean* KE | **−1.6e−5 %** (1.22746e−17 -> 1.22744e−17 J) |
| weight lost | 2.077 % |
| macroparticles lost | 3.816 % |

Negative and carried almost entirely by the electrons, so this is the ambipolar/expansion
signature again, **not grid heating** — which would be a net gain shared by both species. G2
(`dz/λ_D` = 61.2) therefore stays bounded at this box size, at 36 ppc, for 144 000 steps.

Note the weight/macroparticle split (2.08 % vs 3.82 %, a factor 1.8): the escapers are the
tenuous corona tail, as in `P1_vac_1d`, so quote the **weight**.

### 2. The number that matters for the finite-spot run: THE RIPPLE IS SHOT NOISE

This is what the control was really for. The transverse `n_e` ripple, with **no beam at all**:

| t [ps] | 0 | 1.0 | 2.0 | 3.0 | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| at the critical surface | 0.07 % | 8.15 | 8.39 | 8.31 | 10.15 | 9.86 | 9.84 | 10.80 | 10.28 | 10.16 |
| at z = 50 `d_e` | 0.07 % | 9.42 | 9.08 | 9.26 | 10.11 | 10.94 | 9.83 | 10.31 | 10.23 | 10.83 |

The driven run measures **9.43 %** at the critical surface at 1 ps. The control gives 8.15 % with
no laser. So the ripple is **laser-independent macroparticle shot noise** — 36 electrons per cell
is a 16.7 % floor, smoothed by `particle_shape = 2`, and `NUniformPerCell` starts on a quiet
sub-cell lattice (0.07 %) and fills in to Poisson within a plasma period.

That matters because `n_ref = √(1 − n_e/n_cr)` → 0 at the critical surface, so the eikonal ray
equation amplifies a transverse density gradient by `1/n_ref`: this noise is what refracts light
out of the finite spot (the 7 % pedestal in `P1_vac_2d_spot`). The control turns "the ripple looks
like the shot-noise floor" into a measurement — exactly the service `P1_vac_2d_off` performed when
it proved the planar run's 5 % ripple was noise rather than filamentation.

### 3. A finite spot makes G3's subtraction relatively worse, and the fix is spatial

−3.325 J/m has to be set against the driven run's gain, and the **drive only covers ~35 `d_e` of
a 160 `d_e` box** while this ambipolar excursion covers all of it. Against the whole box the
control is a much larger fraction of the driven gain than the planar run's −3.09 % was, for a
reason that has nothing to do with the drive. **G3 for a finite spot must be evaluated on the
illuminated columns**, from the plotfiles, not on the box-total `EP` reduced diagnostic — see the
driven run's README.

## Retracted

Nothing.
