# P0_bc_open — the candidate fix: pec fields + absorbing particles

**Phase.** 0, `TEST_PLAN.md` §5.2
**Question.** With `open` boundaries (field = `pec`, particle = `absorbing`), does the
runaway ablation front leave the domain cleanly — and what does the pec field wall
reflect back into the interior?
**Expected.** Particle number should **fall** as the fast front is absorbed (contrast
`P0_bc_periodic`, where it is exactly constant). `E_abs(t)` should match
`P0_bc_periodic` for as long as the plume is far from both boundaries: the boundary
choice must not perturb the drive itself. The pec wall zeroes tangential E, so some
near-wall sheath and image-charge structure is expected; the question is how far into the
domain it reaches, in d_e.
**Falsified by.** Particle number not falling (the absorbing BC is not firing);
`E_abs(t)` differing from `P0_bc_periodic` from t = 0 (the boundary changed the drive,
so the pair is not a controlled comparison); or wall structure reaching more than a few
d_e into the interior, which would make `open` unusable for a run whose shock forms near
the boundary.

## Setup

Byte-identical to `P0_bc_periodic` in every physical primary — same target, same laser,
same domain, same duration, same ppc. **The only change is
`geometry.boundary.axis: {lo: open, hi: open}`.** That is the point: with one variable
changed, any difference between the two runs is attributable to the boundary.

`B0 = 0` deliberately. This run isolates the *particle* boundary question; whether pec
also coexists with a uniform applied `B0` is the separate question `P0_bc_open_B` asks.
Keeping them apart means a failure has one candidate cause instead of two.

Parent: `P0_bc_periodic`.

## Cost

400 cells × 2 species × 200 ppc, 24 000 steps (2.35 ps). See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 | PASS |
| G2 dz/λ_D (target cold) | 61 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 200 | PASS |
| G6 energy closure | | post-run |

## Result

*(not yet run)*

## Retracted

Nothing.
