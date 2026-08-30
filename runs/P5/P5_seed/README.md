# P5_seed — seed replicate of `P5_full` over the parent's window

**Phase.** 5, `TEST_PLAN.md` §13 — *replicates `P5_flashic` (lifted IC), not `P5_full`*
**Question.** How wide is the error band on a `T_e(τ)` trajectory when *only* the RNG seed
changes?
**Expected.** Smaller than the project's quoted 12–13.5 % noise floor. That floor was
measured across legs differing in more than the seed, so it is an upper bound of unknown
tightness; the seed-only component should be a fraction of it.
**Falsified by.** A seed-only spread at or above 13.5 %, which would mean no single-run
trajectory difference smaller than the whole 0.69 × gap can be interpreted at all.

---

## Why this run exists

Phase 5's headline is a ratio-versus-τ **curve**, and a curve needs a band. The existing
floor comes from `mr100`-class plume `T_e` appearing in `RESULTS.md` as **157.7 / 138.9 /
148.6 / 166.6 / 181.8 / 182 eV** for nominally identical physics — but those legs differ in
more than the seed, so attributing that spread to statistics is an assumption.

Deliberately a **fixed seed** rather than a plain rerun: CUDA is not run-to-run reproducible,
so "just run it twice" confounds the seed with nondeterminism and yields a number that cannot
be attributed to either. `P5_full` sets `random_seed: 20260829`; this run sets `71828183` and
changes nothing else.

## What is different from `P5_flashic`

| | `P5_full` | this run |
|---|---|---|
| `random_seed` | 20260829 | **71828183** |
| initial condition | lifted (`flash_table`) | lifted — *identical* |
| `max_step` | 9 139 500 | **2 031 000** (`τ_own` 5.391, `t_FLASH` 0.300 ns) |

The shortened duration is a cost decision, not a physics one: the band is needed over the
window where `P5_full` overlaps both its own parent and this replicate. **≈ 4.4 h.**

## Double duty

Over `τ_own` 0 → 5.39 there are now three real-mass legs on the same corona fit:

| leg | thickness | seed | what the pair isolates |
|---|---|---|---|
| `P4_lez_kin_mrreal_drift` | analytic, 4.5 `d_i0` | unset | — |
| `P5_full` (first fifth) | analytic, thickened | 20260829 | the target thickening |
| `P5_flashic` (first fifth) | **lifted from FLASH** | 20260829 | **the IC lift** |
| **`P5_seed`** | lifted from FLASH | 71828183 | **RNG alone** |

So the thickening A/B and the noise band are measured on the same window, and the thickening
result is quoted against a band rather than against an assumption.

## Geometry

Identical to `P5_flashic`; 22040 cells, 2031000 steps = 200.8 ps.

## Result
*(to be filled in after the run)*

## Retracted
nothing yet -- the run has not been launched.
