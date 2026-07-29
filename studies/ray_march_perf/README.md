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

### Still to do

* build and run Tier 1 for O3; then O1, then O2, re-running Tier 1 after each
* Tiers 2–4 (§7.5.4), including thread invariance across `OMP_NUM_THREADS` 1/2/4/8/12
* the benchmark ladder itself — threads × O1/O2/O3 on/off — which needs an **idle** box to
  mean anything, so it waits for the GPU run to land
