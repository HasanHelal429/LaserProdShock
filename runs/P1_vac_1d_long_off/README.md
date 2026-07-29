# P1_vac_1d_long_off — the laser-off control for `P1_vac_1d_long` (gate G3, 100 ps)

**Phase.** 1, `TEST_PLAN.md` §7.1 and §6 (gate G3)
**Question.** Does grid heating stay negligible over **1.024 million steps**?

**Why the 10 ps control cannot be reused.** Finite-grid heating accumulates with *step count*,
so a bound measured over 102 400 steps says nothing about a run that is 10× longer. That is
also why this deck keeps the physics run's exact duration rather than being a shorter, cheaper
stand-in — the whole value of a G3 control is that the only difference is the drive.

At `dz/λ_D` = 61 the target is Debye-under-resolved by construction (gate G2), and this run is
the only thing that converts G2 from a number into a bound. **This is a considerably sharper
test than the 10 ps control was**, and if it fails, `P1_vac_1d_long`'s ablation numbers go with
it.

**Expected.** Essentially a repeat of `P1_vac_1d_off`, scaled:

- **net particle-KE change ≈ 0**, and in particular *not* a net gain. The 10 ps control read
  **−1 696 J** (−0.07 % of the driven gain) and it should stay small in *relative* terms.
- the same **electron→ion ambipolar split** rather than a heating signature: at 10 ps electrons
  lost 51.4 kJ while ions gained 49.7 kJ, cancelling to ≈ 0. Grid heating would instead appear
  as a net **gain shared by both species** — that is the discriminator to look for, not the
  magnitude alone.
- `LASERDEP` reports `Pabs = 0` on all 102 400 lines.
- essentially no boundary loss (the 10 ps control lost 0.0000 % of the weight), though over
  100 ps its own slow thermal expansion will start to reach the walls.

**Falsified by.** A net particle-KE **gain** growing with step count, or an ion population that
looks like a piston. Either would mean `P1_vac_1d_long`'s ablation is partly numerical, and
every number from it — including the `E_abs` history that Phase 2's drive budget rests on —
would have to be withdrawn.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                    x  LASER OFF (I = 0)
                                         ##~~                           
      ^                                                                ^
      open                                                          open
      z = -3000                                                  z = +2400

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 10800 cells, dz = 0.5 d_e, dt = 0.09783 fs, 1024000 steps = 100.2 ps
```

## Setup

`P1_vac_1d_long` with `laser.intensity: 1.0e18 → 0.0`. **Nothing else** — verified rather than
asserted: stripping comments, the two generated decks differ in exactly one line,

```
< laser_deposition.intensity            = 1e18      (P1_vac_1d_long)
> laser_deposition.intensity            = 0.        (this run)
```

and `tests/test_structures.py` enforces that invariant for every `_off` run in the repo.

Same 10 800 cells, same 1 024 000 steps, same 400 ppc, same domain, same `open`/`open`
boundaries, same diagnostics. `controls.ray_cfl_ladder` is declared only so the two configs are
indistinguishable to the gates; with no beam, `ray_cfl` is moot.

## Cost

Same grid and particle count as `P1_vac_1d_long` — 10 800 cells, 420 000 macroparticles,
1 024 000 steps → 100.18 ps. Slightly cheaper in practice, since the ray trace and the per-cell
temperature reduction never run. Benchmarked at ~123 min; **actual 3 h 10 m** on GPU 1,
concurrently with the physics run on GPU 0 (3 h 45 m). Both overran the benchmark because the
host was CPU-saturated by unrelated jobs — a CUDA run is latency-bound on one host thread, so
GPU utilisation fell to ~53 %. See `P1_vac_1d_long`'s Cost section for the full breakdown; this
run was the cleaner measurement of the *other* cause, since **it slows down too with no laser
at all** (`warpx_rate` 0.0062 → 0.0111 s/step), which is how plume-spreading was separated from
host contention.

Both use the **same backend deliberately**: CPU and GPU agree on integrated `E_abs` only to
~2.5 % (different `ParallelForRNG` streams), and comparing a GPU physics run to a CPU control
would fold that into the G3 subtraction.

## Gates

`make_inputs.py --check`: **3 pass, 0 warn, 0 fail**, 3 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — **this run is what bounds it** |
| G3 laser-off control | *this run IS the control* (`intensity = 0`) | info |
| G4 `ray_cfl` check | 0.25 — moot, no beam | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc; bias bound ≤ 0.31 % | **pass** |
| G6 energy closure | — | post-run: with `E_abs` ≡ 0, the **entire** particle-energy gain is the grid-heating budget |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm | info |

## Media

- `media/P1_vac_1d_long_off/checks.png` — initial density from the deck's own `density_function`, predicted `K(z)`/`tau(z)`, and the gate table
- `media/P1_vac_1d_long_off/fields_lineouts.png` — `n_e(z)` profiles at selected times
- `media/P1_vac_1d_long_off/fields_streak.png` — `n_e` and `E_z` as (z,t) maps over 100 ps
- `media/P1_vac_1d_long_off/gates.png` — the G1-G7 gate panel on its own
- `media/P1_vac_1d_long_off/laser_history.png` — empty by construction — annotated "laser off"; `Tlocalfrac` falls to 0.001
- `media/P1_vac_1d_long_off/laser_profile.png` — the step-0 density profile with zero deposition — the visual null
- `media/P1_vac_1d_long_off/movie_fields.mp4` — evolving `n_e(z)` lineouts
- `media/P1_vac_1d_long_off/movie_phase.mp4` — target-ion phase space over the full 100 ps
- `media/P1_vac_1d_long_off/phase_space.png` — target-ion (z, u_z): the undriven expansion that must be subtracted

## Result

Ran **1 024 000/1 024 000 steps = 100.18 ps in 3 h 10 m** on GPU 1, zero errors, `--verify` OK.

**VERDICT: grid heating does NOT accumulate. It is −0.066 % of the driven gain over 1.024
million steps — statistically the same as the −0.07 % the 10 ps control measured.**

| | this control | 10 ps control | `P1_vac_1d_long` |
|---|---|---|---|
| steps | 1 024 000 | 102 400 | 1 024 000 |
| net particle-KE gain | **−7 962 J** | −1 696 J | **+1.1975×10⁷ J** |
| as a share of the driven gain | **−0.066 %** | −0.07 % | — |
| electrons / ions | −221.8 kJ / +213.9 kJ | −51.4 / +49.7 kJ | +3.97×10⁶ / +8.42×10⁶ J |
| field-energy gain | 6 129 J | 1 530 J | 2.21×10⁵ J |
| weight lost | **0.0014 %** | 0.0000 % | 1.1405 % |

**This was the run's whole point and it answers cleanly.** The concern was that finite-grid
heating at `dz/λ_D` = 61 might creep in over ten times the step count. It does not: the
absolute number grew ~4.7× (−1.7 → −8.0 kJ) while the *driven* gain grew ~4.9× (2.42×10⁶ →
1.20×10⁷ J), so the **ratio is unchanged**. Gate G2 is bounded for the 100 ps run exactly as
well as for the 10 ps one.

**And the sign is the discriminator, not the magnitude.** The change is still **negative**, and
still the ambipolar electron→ion split: electrons lost 221.8 kJ while ions gained 213.9 kJ,
cancelling to −8.0 kJ. Grid heating would appear as a net **gain shared by both species**. What
this run shows is a 51 eV corona relaxing into vacuum for 100 ps — real physics, no drive.

**The undriven expansion is not negligible and must be subtracted.** Weight-weighted forward
bulk ion speed reaches 0.00124 c (0.17 `c_s`) against the driven run's 0.00622 c, so the
control accounts for **20 %** of the driven bulk velocity. That is why the H3 numbers in
`P1_vac_1d_long` quote a control-subtracted α (1.52) alongside the raw one (1.90). By the
percentile front the contamination is far worse — the control's front reaches 0.0178 c at
30 ps — which is the second confirmation of the rule that **piston speed comes from a
weight-weighted bulk, never a percentile front**.

`Tlocalfrac` runs 0.430 → **0.001**: with no absorption the operator has essentially no cell
in which to measure a temperature, the complement of the driven run's saturation at 1.000.

Boundary loss stayed at **0.0014 %** — a factor 800 below the driven run's 1.14 %. The
driven plume is what reaches the walls; the undriven one barely moves. So the domain was
oversized for *this* run and undersized for its partner, which is itself a useful calibration:
**the domain requirement is set by the drive, not by the geometry.**

## Retracted

Nothing.
