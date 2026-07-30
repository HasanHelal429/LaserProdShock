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
| `o3-reuse-end-of-step-sample.patch` | written, syntax-checked, **not yet compiled** | O3: RK4 stage 1 takes the caller's already-computed `(n_ref, ∇n_ref)` instead of re-sampling the same point. 6 field samples per step → 5. Bit-identical, because `sample()` is pure and the fields are frozen for the march. Invalidated on the turning-point rewind of `c`, without which it would be only *nearly* exact. |

**Before applying any of these, capture the Tier-1 baseline** — the binaries are the only record
of pre-change behaviour and a rebuild destroys them. See `../README.md`.
