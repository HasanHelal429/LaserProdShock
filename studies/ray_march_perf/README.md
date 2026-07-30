# `ray_march_perf` — the Phase 1.5 acceptance and benchmark harness

**What this is for.** `TEST_PLAN.md` §7.5 optimises the eikonal ray march (O1 OMP over rays,
O2 vacuum skip, O3 the redundant sample). This directory holds the machinery that decides
whether each change was free — *before* any speedup is quoted.

**The governing rule is §2.8's.** The transverse index clamp passed all five upstream CI decks
for its entire life, because each one reduces the operator to a single number and the clamp
*relocated* energy while conserving the total to 7 digits. So Tier 1 compares the **per-cell
profile dump at every step**, not the analysis scripts' verdicts.

## Files

```
capture.sh       run the 5 upstream CI decks with a given build; capture every dump
compare.py       Tier 1: byte-compare two captures, and re-check the oblique deck's 1/8
baseline_bin/    the pre-optimisation WarpX CPU binaries, preserved (gitignored, 45 MB)
scratch/         captures (gitignored)
```

`tests/test_acceptance_harness.py` pins `compare.py`'s **sensitivity**: it must fail on one
cell perturbed by one ULP, and it must say which file. A comparator that only ever passes
certifies nothing. One of those tests asserts the opposite of what you might expect — that
the oblique deck's closed-form 1/8 check still reads `EXACT` on the perturbed capture. That
is §2.8 in miniature, and it is the whole argument for comparing dumps.

## How to use it

```bash
# 1. capture the baseline BEFORE rebuilding -- the binaries are the only record of pre-change
#    behaviour, and a rebuild overwrites them
studies/ray_march_perf/capture.sh studies/ray_march_perf/baseline_bin \
    studies/ray_march_perf/scratch/base

# 2. build the change, then capture again
studies/ray_march_perf/capture.sh /home/hhelal/warpx-cda/build/bin \
    studies/ray_march_perf/scratch/o3

# 3. Tier 1
python studies/ray_march_perf/compare.py \
    studies/ray_march_perf/scratch/{base,o3}
```

Captures run with `OMP_NUM_THREADS=1` deliberately, so that the **serial** march is the
reference and Tier 4's thread-invariance test has something unambiguous to compare against.
Everything is `nice -n 19`, because a driven physics run on this box is latency-bound on one
host thread (`CLAUDE.md`) and is easily starved.

## Status

**2026-07-29 — baseline captured; O3 written and syntax-checked; builds deferred.**

* Baseline capture: **285 files across the 5 decks** (`scratch/base`), taken with the CPU
  binaries of 10:48, preserved into `baseline_bin/`.
* **The CPU binaries do contain c817b63**, despite predating the commit *timestamp* (11:12).
  Settled by measurement rather than by `ls`: the oblique deck returns a per-column share of
  **12.5000 % in all 8 columns, max/min 1.000000**, which the clamp could not produce (it
  drove edge columns to 20–25× their neighbours, and this deck's rays drift 2.9 transverse
  domain widths). A commit timestamp is not a build timestamp — check the physics.
* O3 is written into `LaserDeposition.cpp` and passes `g++ -fsyntax-only` with the real build
  flags. **Not yet compiled or run**: `runs/P1/P1_vac_2d_spot` is mid-flight on GPU 0, a `-j8`
  build would starve it (`CLAUDE.md` documents a 1.8× slowdown on a loaded host), and
  rebuilding `build_cuda/bin/warpx.2d` would overwrite the binary it is executing.

### What O3 turned out to be

Cheaper and cleaner than §7.5.3 assumed. The RK4 stages read only `n_ref` and `grad n_ref`
from each sample — never the density — and `trace_ray` *already* holds exactly those two at
the ray's current position, because it samples there at the end of every step to test for the
turning point. RK4 stage 1 then samples the same point again. So the "cache" is data that
already existed; `rk4` just takes it as an argument. 6 samples per step → 5.

One subtlety decides whether it is bit-identical: the turning-point branch rewinds
`c = c_old` after reflecting, so the carried sample no longer describes the ray's position.
That path sets `s_valid = false` and stage 1 takes its own sample. Miss this and the change
is *nearly* exact, which is the worst outcome available.

### The O1 race audit (done; O1 not yet written)

A bare `#pragma omp parallel for` over the ray loop would be **wrong for a reason the plan had
not named**. There are three pieces of shared mutable state, not two:

| state | where | consequence of racing |
|---|---|---|
| `H_arr(...) +=` | `deposit()` | lost updates; the known one |
| `absorbed_power_total +=` | `deposit()` | a `reduction(+:)`; trivial |
| **`A_loc`** | enclosing scope, line ~716 | **corrupts the absorption coefficient** |

`A_loc` is the interpolated IB coefficient at the most recent `sample()`, kept as a side channel
in the enclosing scope *because* the RK4 stages call `sample` without needing it. Threaded, every
thread overwrites it five times per step and then reads someone else's value. That is not a
rounding perturbation — it changes the physics, silently, with no crash and no conservation
violation. Fix by making it an out-parameter so it is never shared, which also retires the
"read it immediately after the sample you mean" ordering contract.

Everything else is safe, and the compiler says so: `n_arr`/`A_arr` are `const_array(mfi)`, the
geometry is `const`, and all of `trace_ray`'s march state is invocation-local — including O3's
`s_valid`, which is why it was written inside `trace_ray` rather than beside `rk4`. The `MFIter`
walks the gathered full-domain box, so there is exactly one iteration and the ray loop is the
unambiguous parallel region.

Accumulator memory, to budget before an H5-scale run: `N_ACC × n_cells × 8 B`. The spot box
(320×2200) is 5.6 MB per buffer — 45 MB at `N_ACC` = 8. A 3424-column H5-scale spot is 60 MB per
buffer, i.e. **482 MB at 8**, so `N_ACC` wants to be a runtime parameter that gets logged.

### O2's payoff, measured — and the plan's estimate was wrong by 4.5×

`vacuum_fraction.py` reads `n_e` from dumps that already exist, so O2's benefit is known before
it is written. Figure: `media/ray_march_perf/o2_vacuum_fraction.png`.

The plan estimated "~9× on `P1_vac_2d`" from that run's 89 %-vacuum **geometry**. Measured, the
answer differs in kind, because `f_vac` is a function of **time**:

| run | `f_vac`(0) | speedup | `f_vac`(`t_end`) | speedup |
|---|---|---|---|---|
| `P1_vac_1d_thick` | 0.636 | 2.75× | 0.011 @ 26.9 ps | **1.01×** |
| `P1_vac_2d` | 0.636 | 2.75× | 0.010 @ 26.9 ps | **1.01×** |
| `P1_vac_2d_spot` | 0.471 | 1.89× | 0.360 @ 8.0 ps | **1.56×** |

**The vacuum is eaten by the fast-electron halo, not the plume.** At the measured coronal
`T_e` ≈ 300 eV, `v_th,e` = 43 `d_e`/ps = **10× `c_s`**, so the `10⁻⁴ n_cr` contour crosses a
1200 `d_e` forward gap in ~28 ps — which is exactly when `P1_vac_2d`'s `f_vac` reaches 0.01. Size
a vacuum gap's *ray-trace* lifetime from `v_th,e`; sizing it from `c_s` overestimates by 10×.

The model `(L_vac(0) − v_th,e t)/L_tot` tracks `P1_vac_2d` closely and over-predicts the spot's
decay, so it is a mechanism and a timescale, not a fit. **A tempting explanation for the spot was
tested and falsified**: it is *not* that only the illuminated columns develop a halo. Dark columns
retain **1.01×** the vacuum of lit ones — the halo crosses the 160 `d_e` transverse box in ~4 ps
and fills it. Recorded because a plausible unfalsified story is worse than none.

**`n_th` chosen from the trade-off** (`--sweep`), on the spot at 8 ps: 10⁻⁴ → 1.56× at
`τ_disc` = 3×10⁻¹⁰; **3×10⁻² → 2.00× at `τ_disc` = 3.5×10⁻⁴**, still 300× under the 10.4 % 1σ seed
spread; 10⁻¹ → 2.10× but 17× the error. Take **3×10⁻² `n_cr`** — the knee. The plan's 10⁻⁴ was
over-conservative by 0.44× in speedup for no measurable accuracy gain.

**Consequence for the phase:** combined best case falls from ~15× to **~10×**, and to ~7× on a
long run. §7.5.2, §7.5.4 and §7.5.5 corrected accordingly — the old Tier-2 criterion ("O2's win
must appear as ~9×") would have **failed a correct implementation**, which is worse than having no
criterion. It now demands agreement with `1/(1−f_vac)` measured on the same dump.

### Still to do

* build and run Tier 1 for O3; then O1, then O2, re-running Tier 1 after each
* Tiers 2–4 (§7.5.4), including thread invariance across `OMP_NUM_THREADS` 1/2/4/8/12
* the benchmark ladder itself — threads × O1/O2/O3 on/off — which needs an **idle** box to
  mean anything, so it waits for the GPU run to land
