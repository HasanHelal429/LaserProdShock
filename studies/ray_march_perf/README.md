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
bench.sh         the benchmark ladder: march cost per application, from the TinyProfiler
baseline_bin/    the pre-optimisation WarpX CPU binaries, preserved (gitignored, 45 MB)
scratch/         captures (gitignored)
```

`capture.sh` takes ParmParse overrides after the output directory and honours `THREADS`, which
is what Tier 1's exact mode (`laser_deposition.n_accumulators=1`) and Tier 4's thread ladder
use.

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

**2026-07-30 — O1 + O2 + O3 built, accepted and measured. The march is 11.9× faster and it
threads; the operator is no longer march-dominated on CPU.**

Acceptance (all on the CPU build, `nice`-d, box otherwise loaded at ~18):

| test | result |
|---|---|
| Tier 1, exact mode (`n_accumulators=1`) | **285/285 files bit-identical** to the pre-change binary, all five decks; oblique still exactly 1/8 |
| Tier 1, production defaults (`n_accumulators=16`) | every per-cell profile dump bit-identical; **only `EP.txt` on the oblique deck moves, by 1.3×10⁻¹⁵** — the accumulator reordering, 6 ULP |
| Tier 2, `P1_vac_2d_spot` step-0 dump | **byte-identical**, with O2 active (`Vskip 0.47`); `Pabs` 5.94085×10¹² unchanged |
| Tier 4, thread invariance 1/2/4/8/12 | every `LASERDEP` line **byte-identical**; every profile dump bit-identical |

The one caveat, stated because it looks like a failure and is not: at 2/4/8/12 threads `EP.txt`
differs from the 1-thread capture by 2–5×10⁻¹⁵ on the three 2D decks. **The pre-change binary
produces the identical differences** (1.946, 3.918, 4.628 ×10⁻¹⁵ — the same numbers), so this is
WarpX's own OMP particle path, not O1. It is also why Tier 4's criterion is the operator's
output, not the particle energy: `EP` cannot resolve a thread-invariance claim about the march.

### The benchmark ladder

`bench.sh`, on the real `P1_vac_2d_spot` geometry (320 rays, 704 k cells, the t = 0 vacuum gap)
with `ppc = 1` so that the particle push does not swamp the timer. Numbers are
`LaserDeposition::applyDeposition` per application, and the **march** column subtracts the
measured non-march floor (see below).

| build | threads | per application | march only | march speedup |
|---|---|---|---|---|
| pre-change | 1 | 0.912 s | 0.678 s | 1.00× |
| O3 | 1 | 0.788 s | 0.538 s | **1.26×** |
| O3 + O2 | 1 | 0.602 s | 0.351 s | **1.93×** |
| O3 + O2 + O1 | 2 | 0.452 s | 0.201 s | 3.37× |
| O3 + O2 + O1 | 4 | 0.360 s | 0.110 s | 6.16× |
| O3 + O2 + O1 | 8 | 0.312 s | 0.062 s | 10.9× |
| O3 + O2 + O1 | 12 | 0.307 s | 0.057 s | **11.9×** |

O3 measured 1.26× against 1.17× predicted; O1 6.2× on top, inside the predicted 6–8×; O2 1.53×
against the 1.89× its `f_vac` = 0.47 would give if a vacuum step were free. It is not free — it
keeps its RK4 arithmetic, its midpoint construction and its escape test — and back-solving
`1/((1−f) + fφ) = 1.53` puts a vacuum step at **φ = 0.26** of a full one. That is the price of
being bit-identical instead of jumping, and it is worth paying (below).

### The new bottleneck: the march is no longer the cost

Measured by running the same benchmark with `laser_deposition.intensity=0`, which executes the
whole operator except the ray march: **0.250 s per application, and it does not thread at all**
(0.248 s at 12 threads). So of the 0.307 s an application now costs, **81 % is not the march**.
Decomposed the same way: the 16 accumulators cost 17 ms, the per-cell `A_host` build with its
`pow(kT, 1.5)` costs 14 ms, and the remaining ~0.22 s is the grid machinery — the 6-component
`n_meas` allocation and `SumBoundary`, the `ParallelCopy` onto a single full-domain box, the
pinned-host copies, and the redistribute back.

Two caveats before anyone optimises that: it was measured at **ppc = 1**, so the particle CIC
and the kicks are at their cheapest here and will grow with ppc; and most of it is device work
on a CUDA build, where this profile does not apply. It is recorded because it is what the next
person will hit, not because it is in scope for Phase 1.5.

### O2's threshold: PROPOSED 3×10⁻² n_cr, MEASURED unacceptable, replaced by exactness

`TEST_PLAN` §7.5.2 chose `n_th` = 3×10⁻² `n_cr` from a sweep of the **discarded optical depth**
(τ_disc = 3.5×10⁻⁴, 300× under the seed noise) and had the ray jump analytically from the
injection face to the entry plane. Implemented exactly as specified, that **moved the 1D ramp CI
deck's absorbed fraction by +6.13 %** — from 1.2 % *below* the closed form to 4.9 % *above* it,
i.e. an order of magnitude outside the deck's 0.48 % tolerance. The 2D oblique deck moved 1.4 %.

The diagnosis, by replicating the march in Python against the same density field the operator
had used:

* The skipped region is **not vacuum** in that deck — the ramp starts at zero and rises, so the
  first 4 cells hold sub-threshold *plasma*. Light refracts there.
* Because it refracts, the discrete march does **not** advance by `h` in `z` per step. Measured:
  it lags the straight line by **1.6×10⁻³ h over 16 steps**. An analytic jump of a whole number
  of steps therefore lands the ray slightly *ahead* of where the march would have put it.
* That tiny lead changes which step first satisfies the near-critical trigger
  `n_ref ≤ n_floor && drds > 0`. In the pre-change run the trigger **never fires** and the ray
  turns by refraction alone; with the jump it fires, and the analytic layer adds 4.6 % of the
  beam in one deposit. A discrete flip, not a gradual error — which is why skipping **one** cell
  and skipping **four** gave the same +6.13 %.
* It is genuinely a phase effect and not a general fragility: perturbing `ray_cfl` by 1 part in
  10⁷ moves the same total by only 9×10⁻⁶.

**So τ_discarded was never the only error a skip could make, and the sweep that chose 3×10⁻²
could not see the one that mattered.** The threshold is gone. O2 now skips only steps whose
whole extent lies in field that is **exactly** empty, where `sample` returns `(n_ref, ∇n_ref) =
(1, 0)` exactly and the four RK4 stages provably reduce to the same derivative — and rather than
jumping it takes the steps with the same arithmetic, in the same order, minus the samples. The
result is bit-identical on every deck tested, including the production spot geometry.

**The exactness is free in the only place it was supposed to pay.** `Vskip` on
`P1_vac_2d_spot` at t = 0 reads **0.47** — the same 0.471 the plan measured with a 10⁻⁴ `n_cr`
contour. The forward vacuum gap of a vacuum-ablation run is empty *to the bit*, so a strict test
finds all of it. The threshold would have bought 1.93× → 2.10× on the march (§7.5.2's own table)
in exchange for an unbounded phase error near a turning point.

---

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

* **the GPU build.** `build_cuda` is configured `AMReX_OMP=OFF` with no `-fopenmp`, so
  `_OPENMP` is undefined and O1 is inert there — the production 2D runs get O2 + O3 (1.93×)
  and nothing else. `build_cuda_omp/` is being built with `-DAMReX_OMP=ON` (which puts
  `-Xcompiler=-fopenmp` in the CUDA flags) to fix that, deliberately as a **separate tree** so
  `build_cuda/bin/warpx.2d` stays valid.
* Tier 3 (time-integrated `E_abs` over a 1–3 ps slice) — not run, and arguably retired by the
  Tier-1/Tier-2 bit-identity: there is no drift to integrate when the dumps are byte-equal.
  Worth running once on the GPU build, where the comparison is genuinely different code.
* re-benchmark on an **idle** box. Everything above was measured at load ~18 on a shared
  32-core host, so the thread scaling is a lower bound.
