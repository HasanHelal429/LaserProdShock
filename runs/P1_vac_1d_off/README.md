# P1_vac_1d_off — the laser-off control for `P1_vac_1d` (gate G3)

**Phase.** 1, `TEST_PLAN.md` §7.1 and §6 (gate G3)
**Question.** How much of `P1_vac_1d`'s target heating and expansion is the **laser**, and
how much is the **grid**?

**Why this is mandatory, not optional.** The cold near-critical target is
Debye-under-resolved *by construction*: `dz/λ_D` = 61 (gate G2). One uniform grid cannot
resolve λ_D in a 1.5 n_cr, 51 eV target and also span the plume, so finite-grid heating is
present at some level in every run in this project. G2 is therefore recorded as a
**measurement, not a pass/fail** — and the only thing that converts it into a bound is an
otherwise identical run with the drive switched off. Anything `P1_vac_1d` reports as
"absorbed energy became target heat" is worth exactly as much as this subtraction.

**Expected.** Almost nothing should happen. With no drive the target sits at its initial
51 eV, so `c_s` = 0.001 c = 1.8 d_e/ps and the corona should expand ~**18 d_e in 10 ps** —
against the hundreds of d_e expected of the driven plume. Concretely:

- **no piston**: no directed ion population above the initial thermal spread
  (`θ_i` = 1e-6 ⇒ `u_i` ~ 0.001 c);
- total particle energy gain **small compared with `P1_vac_1d`'s `E_abs`** — this gain *is*
  the grid-heating budget;
- `LASERDEP` reports `Pabs = 0` for all 10 240 lines (a direct check that
  `laser_deposition.intensity = 0.` really disables deposition rather than merely scaling it).

**Falsified by.** A particle-energy gain comparable to `P1_vac_1d`'s `E_abs`, or an ion
population that looks like a piston. Either would mean **the Phase-1 ablation is a numerical
artifact**, and every ablation number in this campaign would have to be withdrawn — which is
precisely the failure mode that produced the retracted upstream shock claim.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                    x  LASER OFF (I = 0)
                    #######~~~~~~~~~~                                   
      ^                                                                ^
      open                                                          open
      z = -300                                                  z = +700

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 2000 cells, dz = 0.5 d_e, dt = 0.09783 fs, 102400 steps = 10.02 ps
```

## Setup

`P1_vac_1d` with `laser.intensity: 1.0e18 → 0.0`. **Nothing else.**

That is verified rather than asserted — `diff` of the two generated decks returns exactly
two hunks: the header comment block, and

```
< laser_deposition.intensity            = 1e18      (P1_vac_1d)
> laser_deposition.intensity            = 0.        (this run)
```

Same 2000 cells, same 102 400 steps, same 400 ppc, same seed-free RNG path, same
diagnostics and intervals, same `open`/`open` boundaries. Identical duration matters as much
as identical geometry: grid heating accumulates with step count, so a shorter control would
under-report it.

`controls.ray_cfl_ladder` is declared here only to keep the two configs identical in every
respect the gates can see — with no beam, `ray_cfl` is moot.

## Cost

Same grid and particle count as `P1_vac_1d` — 2000 cells (525 particle-bearing) × 400 ppc
× 2 species = 420 000 macroparticles, 102 400 steps → 10.018 ps. Slightly *cheaper* in
practice, since the ray trace and the per-cell temperature reduction do not run.
Estimate **~25 min at 8 CPU threads**; to be replaced from `progress.log`.

## Gates

`make_inputs.py --check`: **3 pass, 0 warn, 0 fail**, 3 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial) | **pass** (budget 1.2) |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — **this run is what makes G2 interpretable** |
| G3 laser-off control | *this run IS the control* (`intensity = 0`) | info |
| G4 `ray_cfl` check | 0.25 — moot, no beam | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc, `local` mode; bias bound ≤ 0.31 % | **pass** |
| G6 energy closure | — | post-run: with `E_abs` ≡ 0, the **entire** particle-energy gain is the grid-heating budget |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm | info |

## Media

- `media/P1_vac_1d_off/checks.png` — pre-run: initial density from the deck's own `density_function`, predicted `K(z)` and `tau(z)` at the group `T_e`, and the gate table.

## Result

*(not run yet — awaiting approval)*

## Retracted

Nothing.
