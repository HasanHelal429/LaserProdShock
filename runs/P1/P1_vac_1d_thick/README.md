# P1_vac_1d_thick — the 1D baseline that makes `P1_vac_2d` interpretable

**Phase.** 1, `TEST_PLAN.md` §7.2
**Question.** What does this exact ablation do in **1D**, so that `P1_vac_2d` can be checked
against it with dimensionality as the only difference?

**Why this run exists.** §7.2's planar 2D sub-case "should reproduce `P1_vac_1d` on axis to
within noise". But `P1_vac_2d` had to change the target thickness (80 → 400 d_e) to keep its
rear truncation valid, and coupling here is **drive-limited** — `E_abs` is set by the laser,
not by the target (`TEST_PLAN.md` §2.4). So a 5× thicker target spreads the same energy over
5× the mass and runs far colder: `T_e` ≈ 151 eV at 30 ps here against **548 eV** in
`P1_vac_1d_long`. Comparing 2D-at-400 d_e against 1D-at-80 d_e would confound dimensionality
with thickness and could validate nothing. This run removes that confound.

**Expected.** A colder, slower version of `P1_vac_1d`, and specifically:

- **`f_abs(0)` = 1.000 and the same ≈ 0.24 plateau.** `L_n` is unchanged at 60 d_e and
  absorption happens in the corona, so **thickness should not change the drive at all** — this
  is a direct test of that claim, and a clean prediction, since `E_abs(t)` should overlay
  `P1_vac_1d_long`'s for the first 30 ps despite 5× the target mass.
- **No `n_cr` crossing within the run.** `P1_vac_1d_long` crossed at 28.8 ps with 80 d_e; with
  5× the mass the peak should still be well above `n_cr` at 29.9 ps, so `f_abs` should still be
  on its plateau at the end. **If so, thickness buys drive DURATION** — directly relevant to
  Phase 2, which needs drive at ~38 ps.
- **A slower piston.** H3 says thickness buys momentum, not speed, so `v_p` should be *lower*
  than `P1_vac_1d_long`'s 0.0062 c at matched time — because `c_s` itself is lower.

**Falsified by.** `E_abs(t)` differing materially from `P1_vac_1d_long` over the same window
(which would mean coupling is not drive-limited after all, contradicting §2.4).

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #################~~~~~~~                                          
      ^                                                                ^
      open                                                          open
      z = -400                                                  z = +1200

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 3200 cells, dz = 0.5 d_e, dt = 0.09783 fs, 305600 steps = 29.9 ps
```

## Setup

`P1_vac_2d` with **`dims: 2 → 1`**. Everything else is deliberately identical: the 400 d_e
target, `L_n` = 60, the rear truncation at z = −400, the +1200 forward domain, `dz` = 0.5,
`cfl` = 0.35, `open`/`open`, and — importantly — **the same 36 ppc**, not the 400 the other
1D runs use, so ppc cannot contaminate the comparison.

**`max_step` is 305 600, not 432 000, and that is required rather than sloppy.** `dt` is
`cfl·dz/c` in 1D but `cfl·dz/(c√2)` in 2D, so the same physical time needs √2 fewer 1D steps.
**Matching `t_end` (29.90 ps here vs 29.88 in 2D, 0.04 % apart), not step count, is what makes
the comparison valid.** Diagnostics intervals are scaled by the same ratio so both runs produce
the same number of dumps.

Verified by diffing the two generated decks: they differ only in the `dims`-dependent lines
(`geometry.dims`, `prob_lo/hi`, `n_cell`, the boundary token lists, `num_particles_per_cell`
`36` vs `6 6`, the diagnostic intervals, and `Ey` vs `Ex` in `fields_to_plot`).

## Cost

3 200 cells, 1 164 particle-bearing × 36 ppc × 2 species ≈ **84 000 macroparticles**,
305 600 steps → 29.90 ps. Far cheaper than its 2D partner (no transverse dimension, and 36 ppc
rather than the 400 the earlier 1D runs used) — **well under an hour** on one GPU. Run
concurrently with `P1_vac_2d`.

## Gates

`make_inputs.py --check`: 3 pass, **1 warn**, 0 fail, 2 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info |
| G3 laser-off control | **none declared — warn, deliberately** | see below |
| G4 `ray_cfl` check | 0.25, ladder declared | **pass** |
| G5 ppc / `Tlocalfrac` | 36 ppc; bias bound ≤ 3.5 % | **pass** |
| G6 energy closure | — | post-run |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm | info |

**On the G3 warn.** This run has no laser-off control of its own, and that is a considered
choice rather than an oversight: its purpose is to be *differenced against `P1_vac_2d`*, and
grid heating at 36 ppc is bounded by `P1_vac_2d_off`, which runs the same ppc, the same
duration and the same target. Adding a fourth run would buy a number we already have. If any
Phase-1 *claim* ends up resting on this run's absolute energetics rather than on the 1D↔2D
comparison, the control becomes mandatory — record that here if it happens.

## Media

- `media/P1/P1_vac_1d_thick/checks.png`
- `media/P1/P1_vac_1d_thick/fields_lineouts.png`
- `media/P1/P1_vac_1d_thick/fields_streak.png`
- `media/P1/P1_vac_1d_thick/gates.png`
- `media/P1/P1_vac_1d_thick/laser_history.png`
- `media/P1/P1_vac_1d_thick/laser_profile.png`
- `media/P1/P1_vac_1d_thick/phase_space.png`

## Result

Ran **305 600/305 600 steps = 29.90 ps in 21 min** on GPU 1, zero errors, `--verify` OK.

It was meant to be a passive baseline. It produced two results of its own — one **falsifies my
own prediction**, the other **falsifies H3's thickness clause**.

### 1. The drive onset is thickness-independent, as predicted

`f_abs(0)` = **1.0000**, identical to `P1_vac_1d` and `P1_vac_1d_long`. Absorption happens in
the corona and `L_n` was unchanged, so a 5× thicker slab does not change the onset. ✔

### 2. But coupled energy is NOT thickness-independent — my prediction was wrong

I predicted `E_abs(t)` would overlay `P1_vac_1d_long`'s, since coupling is drive-limited. It
does not — the thicker target couples **46 % more** over the same window:

| | `P1_vac_1d_long` (80 d_e) | **this run (400 d_e)** |
|---|---|---|
| `f_abs` plateau, 5–25 ps | 0.2117 | **0.2597** (+23 %) |
| `E_abs` at 29.9 ps | 7.574×10⁶ J/m² | **1.109×10⁷ J/m²** (+46 %) |

**Mechanism, from physics already established:** `K ∝ n_e² T_e^{−3/2}`, and 5× the mass for the
same drive means the target stays **colder** — which makes `K` *larger* and absorption *better*.
Coupling is drive-limited in that no capacity ceiling stops it, but the **plateau level depends
on the target's thermal state**, hence on thickness.

**Honest confound:** ppc differs from `P1_vac_1d_long` (36 vs 400), and G5 notes per-cell noise
biases `K` **high**. That bound is ≤ 3.5 % at 36 ppc against a +23 % plateau shift, so ppc
explains at most a sixth of it. `Tlocalfrac` here is mean 0.904, final 0.995 — the temperature
is measured, not floored.

### 3. Thickness buys drive DURATION — the result that matters for Phase 2

**The peak density never falls below `n_cr`. It rises:**

| t [ps] | 0 | 4.9 | 10.1 | 20.2 | 29.5 |
|---|---|---|---|---|---|
| peak `n_e`/`n_cr` | 1.500 | 1.741 | 1.756 | **1.915** | 1.821 |

`P1_vac_1d_long` crossed `n_cr` at **28.8 ps** and lost its plateau there. This target has not
begun to. **A thicker target extends the drive past the `5 ω_ci0⁻¹` ≈ 38 ps that formation
needs** — so the "thin margin" Phase 1 reported is a *thickness* problem, and it is fixable.

The rise to 1.92 `n_cr` is **ablation-pressure compression**, precisely what gate G1 exists to
watch. At 1.92 `n_cr`, `ω_pe dt` = 0.242 — far under the limit of 2 (G1 budget 1.2), so no
stability concern.

### 4. H3's thickness clause is FALSIFIED

H3 says `v_p` is "roughly independent of … target thickness (thickness raises `E_abs` and the
mass in step, so `v = √(2E/m)` is unchanged)". **That assumed `E_abs ∝ w_t`, which §2.4
disproved** — `E_abs` rose only 46 % for 5× the mass. So `v = √(2E/m)` must *fall*:

| | `P1_vac_1d_long` @ 25 ps | **this run @ 29.9 ps** |
|---|---|---|
| `T_e` | 494 eV | **299 eV** |
| `c_s` | 0.00311 c | **0.00242 c** |
| bulk `v_p` (fwd, weighted) | 0.00353 c | **0.00223 c** |
| **α = `v_p`/`c_s`** | 1.13 | **0.92** (rms 1.25) |

`v_p` is **0.63×** the thin target's, against **0.54×** predicted by `√(E_abs ratio / mass
ratio)` = `√(1.46/5)`. The scaling is real and roughly as the corrected energy argument requires.
**α ≈ 1 survives** — that is the part of H3 that holds.

**Phase-2 consequence: a genuine trade-off, not a free win.** Thickness buys drive *duration*
but costs piston *speed* as √(E/m). Since `M_A ∝ v_p` and formation needs both a supercritical
`v_p` **and** ≳ 1 `ω_ci0⁻¹` of drive, **there is an optimum thickness** — a second sweep axis
alongside `I₀`, which belongs in `TEST_PLAN.md` §9.2.

### 5. The truncation holds — but my original check was the wrong test

**The check I wrote into the config was ill-posed.** It asked whether `n_e` at the rear boundary
stays unchanged. It does not (1.441 → 0.915 `n_cr`, −37 %) — and that is *not* a failure: the
rear face **is a free surface** and must rarefy, in the truncated and untruncated problem alike.
Asking it to stay put was simply the wrong question.

**The right test is whether the two disturbance fronts meet** — the decoupling argument
`P0_thick_open` actually validated:

| t [ps] | disturbed from the laser face | disturbed from the rear face | **undisturbed core** |
|---|---|---|---|
| 10.1 | 1 d_e | 38 d_e | 361 d_e |
| 20.2 | 32 d_e | 48 d_e | 320 d_e |
| **29.5** | **55 d_e** | **76 d_e** | **269 of 400 d_e** |

**67 % of the slab is still at its initial density at the end**, so the faces never couple and
the truncation sits in the regime Phase 0 measured at −0.54 % error. My `c_s`-based estimate of
92 d_e for the front-side disturbance was conservative by 1.7×, in the safe direction.
**Use core decoupling as the criterion in future, not boundary-density invariance.**

### 6. Gate G6, and the real price of truncating

| | value |
|---|---|
| `E_abs` | 1.109×10⁷ J/m² |
| particle-KE + field gain | 1.015×10⁷ J/m² |
| raw gap | **−8.53 %** |
| **boundary weight loss** | **6.13 %** |

**6.13 % weight loss at only 30 ps**, against 1.14 % at 100 ps in the untruncated
`P1_vac_1d_long`. Expected rather than wrong: material expanding out of the rear free surface
genuinely leaves, and with the boundary *on* that surface it leaves at once instead of first
crossing a vacuum cushion. The gap sign is right (particles+field hold less than `E_abs`; WarpX
does not report energy carried out by absorbed particles).

**So truncation trades cells for a weaker energy budget** — the right trade in 2D, where cells
are expensive, but it means **G6 cannot be closed tightly on any truncated run**, and strict
energy-closure claims must come from the untruncated `P1_vac_1d`/`_long`. Ion share of particle
KE is 38.3 % (electrons 7.714×10⁶ J, ions 4.787×10⁶ J).

## Retracted

Nothing measured. But two *predictions* stated in this README's own Expected section are now
known wrong, and are corrected above rather than quietly dropped:

1. "`E_abs(t)` should overlay `P1_vac_1d_long`'s … thickness should not change the drive at
   all" — **wrong**; it couples 46 % more, because a colder target absorbs better.
2. The `thickness_criterion` note in `config.yaml` proposed checking the truncation by
   confirming rear-boundary `n_e` is "unchanged from initial" — **an ill-posed test**, since a
   free surface must rarefy. Replaced by the core-decoupling check in §5.
