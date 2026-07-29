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

*(not generated yet)*

## Result

*(running)*

## Retracted

Nothing.
