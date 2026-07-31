# `patches/` — the Phase 1.5 source changes, versioned here

`warpx-cda` is a separate repository, and its working tree carries **unrelated** modifications
that predate this campaign (`ParticleHeater`, the `laser_deposition/run_laser_shock*` decks).
Committing there would bundle them, so the operator changes for Phase 1.5 are kept as patches
under version control **here**, against `warpx-cda` commit `c817b634`.

Apply with:

```bash
cd /home/hhelal/warpx-cda
git apply /home/hhelal/LaserProdShock/studies/ray_march_perf/patches/<name>.patch
```

| patch | status | what it does |
|---|---|---|
| `o123-ray-march.patch` | **built and accepted** 2026-07-30 (Tier 1 exact, Tier 4 thread-invariant) | O1 + O2 + O3 in one patch, because they touch the same three lambdas and splitting them would leave the tree in a state no test was written for. |

`o3-reuse-end-of-step-sample.patch` was folded into the patch above and deleted; it was never
built on its own.

### What is in it

**O3 — the redundant sample.** RK4 stage 1 takes the caller's already-computed
`(n_ref, ∇n_ref)` instead of re-sampling the same point. 6 field samples per step → 5.
Bit-identical, because `sample()` is pure and the fields are frozen for the march. Invalidated
on the turning-point rewind of `c`, without which it would be only *nearly* exact.

**O1 — OMP over rays.** Three pieces of shared mutable state had to go first, and the
dangerous one was `A_loc` (the interpolated IB coefficient, kept as a side channel in the
enclosing scope): it is now an out-parameter of `sample()`, so it is per-caller by
construction and the "read it immediately after the call whose position you mean" ordering
contract is retired. `H_arr` and `absorbed_power_total` become `n_accumulators` (default 16)
per-bucket accumulators, reduced in bucket order.

The parallel loop is over **buckets, not rays** — that is what makes the accumulator ownership
hold for any thread count. With a ray-level `parallel for`, rays `i` and `i + n_acc` share a
bucket and can land on two different threads whenever the thread count does not divide
`n_acc` (12 threads and 16 buckets, say), which brings back both the race and the
thread-dependent summation order.

Guarded on `_OPENMP`, **not** `AMREX_USE_OMP`: the march is host code whose cost does not
depend on the AMReX backend, and a CUDA build — where `AMREX_USE_OMP` is off — is exactly the
case where it is the serial bottleneck holding up an otherwise busy device. `ray_threads`
overrides the thread count for the march alone, so a GPU run can keep `OMP_NUM_THREADS=1`.

**O2 — the vacuum skip.** Steps whose whole extent lies in *empty* field skip their five
`sample()` calls and keep their arithmetic, so they are bit-identical rather than approximate.
Not a density threshold — see the finding in `../README.md`.

**Before applying any of these, capture the Tier-1 baseline** — the binaries are the only record
of pre-change behaviour and a rebuild destroys them. See `../README.md`.
