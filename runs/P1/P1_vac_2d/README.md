# P1_vac_2d — the Phase-1 2D planar validation (rear-truncated, thick target)

**Phase.** 1, `TEST_PLAN.md` §7.2
**Question.** Does the operator, coupled to PIC in **2D**, reproduce the 1D ablation on axis?
A uniform beam with periodic transverse boundaries is *exactly planar*, so it must — and
`TEST_PLAN.md` §7.2 makes this **the gate on every later 2D physics claim**: "a discrepancy
here is a bug or a boundary artifact, not physics."

**Expected.**
1. **On-axis `f_abs(t)`, `E_abs(t)` and `n_e(z)` match `P1_vac_1d_thick` to within noise**,
   and the weight-weighted bulk ion speed agrees. That baseline is the comparison, **not**
   `P1_vac_1d` — see Setup for why using the 80 d_e run would confound dimensionality with
   thickness.
2. **`f_abs(0)` = 1.000**, as in 1D: `L_n` is unchanged at 60 d_e, so the absorption regime is
   the same optically-thick coronal absorber (τ to the turning point = 5.6) that
   `P1_vac_1d` established. Thickness does not touch this — absorption happens in the corona.
3. **No transverse structure.** The configuration has no transverse gradient and no
   transverse drive, so `n_e(x)` should stay uniform to shot noise. **A planar run that
   develops transverse structure is showing either an instability (a finding worth chasing)
   or a bug — and either way it must be explained before any finite-spot 2D result is
   trusted.**
4. **The rear truncation holds**: `n_e` and `T_e` at the rear boundary unchanged from their
   initial values at the end of the run.

**Falsified by.** On-axis disagreement with the 1D baseline beyond noise; `f_abs(0)` ≠ 1;
transverse structure that is not explained; or a disturbed rear boundary, which would mean
the thickness criterion below is wrong.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #################~~~~~~~                                          
      ^                                                                ^
      open                                                          open
      z = -400                                                  z = +1200

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  x  transverse     : -16 .. 16 d_e, boundaries periodic/periodic
  grid              : 64 x 3200 cells, dz = 0.5 d_e, dt = 0.06918 fs, 432000 steps = 29.88 ps
```

## Setup

Parent: **`P1_vac_1d`**. Laser, `L_n`, `dz`, `cfl` and boundary *tokens* are unchanged. Four
deliberate differences:

**1. 2D XZ, uniform beam, PERIODIC transverse.** This is the planar sub-case of §7.2, not the
finite-spot physics case. Periodic transverse + a plane wave removes every transverse gradient,
so the run is a pure test of the 2D code path against 1D. The finite-Gaussian-spot run (`H5`,
lateral rarefaction, rays refracting in transverse gradients) comes *after* this passes.
Transverse extent is a modest ±16 d_e / 64 cells — enough to exercise 2D and to host
transverse modes up to 32 d_e, but no wider, because in 2D every transverse cell multiplies
both the field and the particle cost.

**2. The region behind the target is NOT simulated.** The domain is cut exactly at the target's
rear face (z = −400), with the `open` boundary that `P0_rear_open` / `P0_thick_open` validated
at 20 and 80 d_e thickness (front-side ion count within 0.11 %, total target `p_z` within
0.54 %). **This is why 2D is affordable at all**: unlike the 1D vacuum runs, where extra cells
were nearly free because `density_min` left them empty, in 2D every axial cell carries 64
transverse cells of grid and, behind the target, would carry particles too.

**3. The target is 400 d_e thick — and the number is derived, not chosen by taste.** The
truncation is only valid while the front-face disturbance has not reached the rear boundary.
That disturbance travels inward at `c_s`, and `c_s` follows from the drive-limited `E_abs(t)`
(`TEST_PLAN.md` §2.4) spread over this target's true areal mass, **1.145×10²³ m⁻²** (slab plus
Gaussian corona — note `--check` prints the slab-only figure, 1.011×10²³):

| t [ps] | energy/electron | `T_e` | `c_s` | disturbance | % of slab |
|---|---|---|---|---|---|
| 10.0 | 139 eV | 65 eV | 2.0 d_e/ps | 20 d_e | **5 %** |
| 20.0 | 265 eV | 109 eV | 2.6 d_e/ps | 52 d_e | **13 %** |
| **29.9** | 413 eV | 151 eV | 3.1 d_e/ps | **92 d_e** | **23 %** |

**23 % at the end of the run** — the same crossing fraction at which `P0_thick_open` measured
the truncation error at only **−0.54 %** on total target momentum. For contrast, 240 d_e would
have reached 62 % and 600 d_e only 17 % at 1.4× the particle cost. At 400 d_e the target is
67.0 µm, **5× the 1D reference and 2.45× the upstream `run_laser_shock` target** — thick by any
standard here. To be **checked post-run**, not assumed.

**4. ppc 36 (6×6), not 400.** 400 ppc in 2D is unaffordable. G5's absorption-bias bound rises
from 0.31 % to 3.5 %, which is the real cost of this run — but it is an order-of-magnitude
*upper* bound, and the Phase-0 2D runs held `Tlocalfrac` at 0.975–0.987 on only **16** ppc, so
the local temperature is still measured rather than floored. The 1D baseline uses the **same
36 ppc**, so ppc cannot contaminate the 1D↔2D comparison.

**Why a separate 1D baseline (`P1_vac_1d_thick`) instead of comparing to `P1_vac_1d`.** The
thickness had to change for the truncation, and coupling is **drive-limited** — `E_abs` is set
by the laser, not by the target — so a 5× thicker target spreads the same energy over 5× the
mass and runs far colder (`T_e` ~151 eV here at 30 ps against 548 eV in `P1_vac_1d_long`).
Comparing 2D-at-400 d_e against 1D-at-80 d_e would confound dimensionality with thickness and
could not validate anything. `P1_vac_1d_thick` is identical in every respect except `dims`.

## Hazards specific to this run

- **The 36 ppc reduction is the main risk**, and it is why this run has its own G3 control
  rather than inheriting the 1D bound: grid heating worsens as per-cell statistics worsen, and
  an 11× ppc cut is exactly where a bound measured at 400 ppc cannot be assumed to carry.
- **Vacuum + `open` charge imbalance**, as in the 1D runs: electrons are absorbed at the walls
  while their ions remain. Benign at 10 and 100 ps in 1D; unverified in 2D.
- **Forward domain.** `hi_de` = +1200 was sized for a *cold* (thick) target. The 1D 100 ps run
  taught that a hot target's plume edge outruns extrapolation, so **check the occupied-cell
  count against the domain** before quoting a G6 closure.

## Cost

64 × 3200 = 204 800 cells; particle-bearing region z ∈ [−400, +182] ⇒ 1 164 × 64 = 74 496
cells × 36 ppc × 2 species ≈ **5.4 M macroparticles**; 432 000 steps → 29.88 ps.

**Benchmarked** (2 000 steps, diagnostics off) on an RTX 4070 at the smaller 2 080-cell axial
size: 49.1 s ⇒ 59 min for 10 ps. Scaled to this grid (1.54× cells, 1.38× particles) ⇒
**≈ 4 h**. Run concurrently with `P1_vac_1d_thick` on the second GPU. `dt` is
`cfl·dz/(c√2)` in 2D against `cfl·dz/c` in 1D, so 2D needs √2 more steps for the same
physical time — matching `t_end` (29.88 vs 29.90 ps, 0.04 % apart), not step count, is what
makes the comparison valid.

## Gates

`make_inputs.py --check`: **4 pass, 0 warn, 0 fail**, 2 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.214 at 2× compression (0.152 initial) — lower than 1D because `dt` is √2 smaller | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — bounded by G3 |
| G3 laser-off control | `P1_vac_2d_off`, same 29.88 ps and same 36 ppc | **pass** |
| G4 `ray_cfl` check | 0.25, ladder declared | **pass** |
| G5 ppc / `Tlocalfrac` | **36 ppc**; bias bound ≤ 3.5 % (was 0.31 % at 400) — watch `Tlocalfrac` | **pass** (budget 36) |
| G6 energy closure | — | post-run; **quote the weight-loss fraction with it** |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm, as every run in this project | info |

## Media

- `media/P1/P1_vac_2d/checks.png`
- `media/P1/P1_vac_2d/fields_lineouts.png`
- `media/P1/P1_vac_2d/fields_map2d.png`
- `media/P1/P1_vac_2d/fields_streak.png`
- `media/P1/P1_vac_2d/gates.png`
- `media/P1/P1_vac_2d/laser_history.png`
- `media/P1/P1_vac_2d/laser_profile.png`
- `media/P1/P1_vac_2d/movie_fields.mp4`
- `media/P1/P1_vac_2d/movie_map2d.mp4`
- `media/P1/P1_vac_2d/movie_phase.mp4`
- `media/P1/P1_vac_2d/phase_space.png`

## Result

Ran **432 000/432 000 steps = 29.88 ps in 5 h 07 m** on GPU 0, zero errors, `--verify` OK,
gates 4 pass / 0 warn / 0 fail. Control: 1 h 57 m.

> ## ⚠️ SUPERSEDED 2026-07-29 — **the bug diagnosed below is FIXED, so this run's output is invalid.**
> The fix is `warpx-cda` **c817b63** (`TEST_PLAN.md` §2.8): periodic transverse faces now wrap and
> every other face terminates, verified on the CI oblique deck (one column's share of absorption
> **99.53 % → 12.50 %**, the exact 1/8, with the step-0 total unchanged to 7 digits). **Everything
> below is retained as the diagnosis, not as a result** — `diags/` here was produced by the buggy
> operator. `build_cuda/bin/warpx.2d` is rebuilt with the fix; re-run this run and `P1_vac_2d_off`
> against the §7 pass criterion before quoting any 2D number.

> ## VERDICT (pre-fix): the planar validation **FAILS**, and it is an **operator BUG**, located.
> Rays whose *transverse* coordinate drifts past the periodic transverse boundary are neither
> wrapped nor terminated. `deposit()` **clamps** the cell index in every dimension, and the
> domain-exit test checks **only the propagation axis** — so such a ray keeps marching outside
> the domain and dumps all its remaining energy into the edge column. By 26.9 ps **98.8 % of
> all absorption lands in 2 of 64 columns.** Net absorption is **+12 %** above matched 1D.
> **This invalidates 2D results from this operator whenever rays acquire any transverse
> deflection — i.e. always, once the plasma has structure.** Exact lines and fix in §3.

### 1. What agrees, and it is most of the budget

Normalised so the J/m² (1D) vs J/m (2D) unit difference cancels:

| quantity | 1D (`P1_vac_1d_thick`) | 2D planar | 2D/1D |
|---|---|---|---|
| **`f_abs(0)`** | 0.99999 | 0.99997 | **1.0000** |
| **total absorbed at t = 0, per unit area** | 1.0000×10¹⁸ W/m² | 9.9998×10¹⁷ W/m² | **1.0000** |
| **boundary weight lost** | 6.1334 % | 6.1459 % | **1.0020** |
| particle-KE gain / `E_abs` | 0.8730 | 0.9019 | 1.033 |
| ion share of particle KE | 38.29 % | 40.70 % | 1.063 |
| `T_e` final | 298.5 eV | 322.4 eV | 1.080 |
| G6 raw gap | −8.53 % | −8.42 % | — |

**The t = 0 agreement to 2×10⁻⁵ is the important one**: it says the 2D ray launch, the power
apportionment across 64 rays, and the deposition mapping are all correct. Weight loss matching
to 0.2 % says the truncation and the boundaries behave identically. **So this is not a 2D
plumbing bug.**

### 2. What fails: transverse uniformity (prediction 3)

Column-integrated `P_abs` across the 64 transverse columns, which for an exactly planar
configuration should be uniform to shot noise:

| t [ps] | 0 | 2.99 | 8.97 | 14.94 | 20.92 | 26.90 |
|---|---|---|---|---|---|---|
| `P_abs` column **rms/mean** | **0.021** | 4.02 | 4.17 | 4.91 | 5.09 | **5.53** |
| `n_e` transverse rms/mean (absorbing layer) | 0.0006 | 0.150 | 0.125 | 0.109 | 0.111 | 0.109 |

At 8.97 ps the columns span **0.10× to 25.2× the mean — a factor of 250.** And the deposition
non-uniformity **grows monotonically** (4.02 → 5.53) while the density noise does *not*.

### 3. The mechanism: a located bug in the operator's transverse boundary handling

**Step one — the structure is at the EDGES, not distributed.** Column-integrated `P_abs`
in units of the mean, at 8.97 ps:

| column | 0 (x = xlo) | 1 … 62 (interior) | 63 (x = xhi) |
|---|---|---|---|
| `P_abs` / mean | **23.18** | 0.10 – 0.51 | **25.24** |

| t [ps] | 0 | 2.99 | 8.97 | 26.90 |
|---|---|---|---|---|
| **share of all absorption in the 2 edge columns** | **3.2 %** | 73.0 % | 75.6 % | **98.8 %** |
| interior rms/mean (edges excluded) | 0.021 | 0.579 | 0.370 | 0.352 |

At t = 0 the edges carry **3.2 %**, which is exactly 2/64 = 3.1 % — perfectly uniform. The
pile-up appears within ~3 ps and grows to swallow essentially everything.

**Step two — the energy really goes there.** `theta_e` in the absorbing layer is 1.16–1.54×
higher in the edge columns and their density is correspondingly lower (0.675 vs 0.791 `n_cr` at
8.97 ps), so the particles respond. This is real deposition, not a diagnostic artifact.

**Step three — the cause, in `warpx-cda/Source/Particles/LaserDeposition/LaserDeposition.cpp`:**

```cpp
// deposit(), ~line 739 — clamps the cell index in EVERY dimension:
const int ii = static_cast<int>(std::floor((c[d] - plo[d]) * dxi[d]));
idx[d] = amrex::min(amrex::max(ii, lo3[d]), hi3[d]);

// the ray march's exit test, line 893 — checks ONLY the propagation axis:
if (c[m_axis] < plo[m_axis] || c[m_axis] > phi[m_axis]) { break; }
```

A ray that acquires transverse deflection and wanders past `xlo`/`xhi` is therefore **neither
wrapped periodically nor terminated**. It continues marching with its transverse coordinate
outside the domain, and every subsequent `deposit` is **clamped into the edge column**, where it
unloads the rest of its power.

**Why this matches every observation.** At t = 0 rays are exactly normal-incidence with no
transverse velocity, so nothing drifts and the profile is uniform. The G3 control shows a ~5 %
transverse density ripple develops from ordinary PIC shot noise within ~3 ps **with no beam at
all** (corona rms/mean 0.040 → 0.044, versus 0.056 → 0.063 driven; the start is quiet —
`NUniformPerCell` gives 0.06 % initial variation). Those gradients deflect rays; the deflected
ones hit the transverse boundary and are pinned. More of them do so as time passes and paths
lengthen, hence 3.2 % → 73 % → 98.8 %.

**So the seed is benign shot noise and the amplifier is a boundary bug** — not physics, and not
the refractive channelling I first assumed (see Retracted).

**The fix**, upstream: wrap the index for periodic dimensions using `geom.periodicity()` instead
of clamping, and extend the exit test to terminate on non-periodic transverse faces. Until then
`rays_per_cell`, ppc and smoothing are all irrelevant — **the artifact is not statistical and
will not converge away.**

### 4. Consequence: 2D absorbs 12 % more, and the excess is not uniform in time

| t-bin [ps] | 0–3 | 6–9 | 12–15 | 18–21 | 24–27 | 27–30 |
|---|---|---|---|---|---|---|
| `dE/dt` ratio 2D/1D | 1.21 | 1.11 | 1.20 | 1.15 | 1.12 | 1.06 |

Run-integrated: `E_abs/(P_inc·t_end)` = 0.3710 (1D) vs 0.4169 (2D), i.e. **+12.4 %**.

**A caution on how not to measure this.** The *median* `f_abs` over 5–25 ps differs by **48 %**
(0.2597 vs 0.3853), which badly overstates it. 2D sums 64 rays, so its `f_abs` distribution is
much smoother and its median sits close to its mean, while 1D's single ray is spiky and its
median falls well below its mean. **Compare energy-integrated `E_abs`, or the mean — never the
median — across runs of different dimensionality.**

### 5. The rear truncation held, as designed

Checked by **core decoupling** (the criterion `P1_vac_1d_thick` established, not
boundary-density invariance): the slab retains a large undisturbed core, and boundary weight
loss matched the 1D run to 0.2 % (6.146 % vs 6.133 %). The 400 d_e thickness and the
"don't simulate the far side" instruction were both sound — **this run's failure is unrelated
to the geometry it was asked to use.**

### 6. Gate G3 in 2D at 36 ppc — passes, with a caveat worth stating

| | value |
|---|---|
| driven particle-KE gain | +60.258 J/m |
| **laser-off gain** | **−1.8615 J/m = −3.09 % of driven** |
| control electrons / ions | −1.495 / −0.3666 J/m |
| control weight lost | 6.030 % |

Still **negative**, so not grid heating — but −3.09 % against the 1D runs' −0.066 % at 400 ppc,
a **47× larger** relative excursion. That is the honest price of 36 ppc, and it is the same
low-ppc statistics that seed §3's artifact. It does not invalidate the run's energetics, but a
2D result at the few-percent level cannot be quoted without this term.

### 7. What has to happen before any 2D physics claim

1. **Fix the transverse boundary handling upstream** (§3). This is a code fix, not a
   convergence study — the artifact is deterministic, so **no amount of ppc, `rays_per_cell` or
   field smoothing will remove it.** Wrap periodic dimensions in `deposit()` instead of
   clamping, and make the exit test terminate on non-periodic transverse faces.
2. **Re-run this exact pair afterwards.** It is now a regression test with a sharp pass
   criterion: the 2 edge columns must carry ~3.1 % of the absorption (2/64), not 98.8 %, and
   `E_abs` must match `P1_vac_1d_thick` rather than exceeding it by 12 %.
3. Only then the finite-Gaussian-spot run (H5) — a real transverse intensity profile cannot be
   separated from an edge pile-up of this size.

**None of this is a reason to distrust the 1D results** — 1D has no transverse dimension for
rays to refract into, which is precisely why the 1D↔2D comparison isolates the effect.

## Retracted

**A wrong mechanism I asserted during this analysis, before finding the bug.** My first reading of
the factor-250 deposition non-uniformity was that *"the ray tracer amplifies a 5 % density ripple
into 500 % because `n_ref = √(1 − n_e/n_cr)` bends rays away from density maxima, channelling them
into density valleys over hundreds of `d_e` of path"* — i.e. a physics-like refractive
self-channelling, to be tackled with a ppc convergence study and density smoothing.

**That was wrong, and it was wrong in a way that would have wasted real GPU time** on a
convergence study of a deterministic bug. What disproved it was looking at the *pattern* rather
than its variance: the non-uniformity is not distributed across columns as channelling would give,
it is confined to **the two edge columns**, which is a boundary signature. That led to
`deposit()`'s index clamp and the axis-only exit test (§3). Recorded because the summary statistic
(rms/mean = 4.17) was equally consistent with both stories and only the spatial pattern
distinguished them.

**Also corrected**: prediction 3 said "no transverse structure … `n_e(x)` should stay uniform to
shot noise". The density *is* uniform to shot noise (~5 %, and the same with the laser off) — that
part held. What I did not anticipate was that a benign 5 % ripple would be enough to push rays
into a boundary bug.

## Retracted

Nothing.
