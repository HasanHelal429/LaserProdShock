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

*(not generated yet)*

## Result

*(running)*

## Retracted

Nothing.
