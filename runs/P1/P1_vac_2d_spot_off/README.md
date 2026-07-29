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

## Result

(pending)

## Retracted

Nothing.
