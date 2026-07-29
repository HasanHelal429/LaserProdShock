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

Run on **GPU 1** (an RTX 4070) concurrently with `P1_vac_1d` on GPU 0 — the benchmark on
that deck gave **7.9 min on GPU against 100.6 min on 8 CPU threads (12.7×)**. Both runs use
the **same backend deliberately**: grid heating is what this control measures, and comparing
a GPU physics run against a CPU control would fold a backend difference into the G3
subtraction. See `progress.log`.

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

- `media/P1_vac_1d_off/checks.png` — initial density from the deck's own `density_function`, predicted `K(z)`/`tau(z)` at the group `T_e`, and the gate table
- `media/P1_vac_1d_off/fields_lineouts.png` — `n_e(z)` profiles at selected times
- `media/P1_vac_1d_off/fields_streak.png` — `n_e` and `E_z` as (z,t) maps, with the laser history on the same time axis
- `media/P1_vac_1d_off/gates.png` — the G1-G7 gate panel on its own
- `media/P1_vac_1d_off/laser_history.png` — empty by construction: annotated "laser off (I₀ = 0)", and `Tlocalfrac` falling to 0.000
- `media/P1_vac_1d_off/laser_profile.png` — the step-0 density profile with **zero** deposition — the visual null
- `media/P1_vac_1d_off/movie_fields.mp4` — evolving `n_e(z)` lineouts with the laser history tracking below
- `media/P1_vac_1d_off/movie_phase.mp4` — target-ion phase space over the run
- `media/P1_vac_1d_off/phase_space.png` — target-ion (z, u_z): the undriven thermal expansion a `v_p` measurement must be corrected for

## Result

Ran **102 400/102 400 steps = 10.018 ps in 8 min** on GPU 1, zero errors, `--verify` OK.

**VERDICT: grid heating is negligible. `P1_vac_1d`'s ablation is 99.93 % laser-driven.**

| | this control | `P1_vac_1d` | ratio |
|---|---|---|---|
| `E_abs` | **0 J** (all 10 240 `LASERDEP` lines report `Pabs = 0`) | 2.4626×10⁶ J | — |
| **net particle-KE gain** | **−1 696 J** | +2.4212×10⁶ J | **−0.07 %** |
| field-energy gain | 1 530 J | 23 310 J | 6.6 % |
| weight lost at the boundaries | **0.0000 %** | 0.0104 % | — |

The net particle energy change is **negative and four orders of magnitude smaller** than the
driven run's gain, despite `dz/λ_D` = 61. **Gate G2 is now bounded**, and the expectation
above holds: almost nothing happened.

**The control is not inert, and its internal motion is physical rather than numerical.**
Electrons **lost 51.4 kJ** while ions **gained 49.7 kJ** — the two nearly cancel (net
−1.7 kJ). That is ambipolar electron→ion energy transfer as an initially 51 eV corona
relaxes into vacuum, exactly the isothermal-rarefaction physics `P1_vac_1d` is driving
harder; it is *not* a grid-heating signature, which would show up as a net **gain** shared
by both species. Nothing left the box at all (0.0000 % weight loss).

**This matters for how the ion front is read.** The control's ion front (unweighted 99.9th
percentile) still runs out to **0.0091 c** by 10 ps, against the driven run's 0.0267 c — only
a 2.9× ratio. A front-based `v_p` would therefore be **~1/3 contaminated** by undriven
thermal expansion. By mass the separation is far cleaner: the weight-weighted forward-mean
ion speed is 0.00089 c here against 0.00144 c driven. **Use weighted bulk measures, not
percentile fronts, for piston speed** — and always against this control.

`Tlocalfrac` runs 0.432 → **0.000**: with no absorption the operator has no cell in which to
measure a temperature, which is the expected complement of the driven run's rise to 1.000.

### Three tooling bugs this run exposed

Every headline run in this project is *required* to have an `_off` companion, yet **no script
had ever been given one** — all Phase-0 runs were driven. `P_inc = 0` makes `f_abs` NaN and
`P_inc·t` zero, and three tools broke on it:

| tool | failure | fix |
|---|---|---|
| `laser_report.py` | `set_ylim(0, max(f))` on all-NaN → `ValueError` | filter NaN; annotate the panel "laser off" |
| `compare_runs.py` | `E/(P_inc·t)` → `ZeroDivisionError` comparing a run to its own control | skip that panel when `P_inc = 0` |
| `make_movies.py` | NaN axis limit in the tracking panel | drop the panel; **and sweep frame dirs on failure**, since the crash had stranded 81 PNGs |

The last one also violated the standing rule that frame directories clean themselves up —
`encode` only deleted them after a *successful* ffmpeg run, so a crash while building frames
leaked them. Now cleaned up on any exception. `laser_report.py`'s `f_abs` panel title was
additionally hard-coded to assert "then shuts itself off", which `P1_vac_1d` disproves; it is
now computed from the data like the `E_abs` panel already was.

## Retracted

Nothing.
