# P0_bc_periodic — the periodic-boundary wrap failure, reproduced on purpose

**Phase.** 0, `TEST_PLAN.md` §5.2
**Question.** With all-periodic boundaries on the propagation axis, does the runaway
ablation ion front wrap onto the far side of the domain and pollute it — and how fast?
**Expected.** Yes. WarpX ties particle boundaries to field boundaries
(`Source/Particles/ParticleBoundaries.cpp`), so periodic fields force periodic
particles. The fastest ions in a free rarefaction into vacuum accelerate without bound
(measured at 0.20 c upstream), so they should cross the 140 d_e from the target's
laser-facing face to the +z boundary and re-enter at −z within the run. Particle number
must stay **exactly constant** (nothing can leave), and ions should appear at the −z end
travelling +z, ahead of anything that got there physically.
**Falsified by.** Particle number falling, or no population appearing at the far
boundary within 2.35 ps. Either would mean the wrap hazard does not apply at these
parameters, and the boundary argument for the rest of the project would need redoing.

## Setup

1D, vacuum, no background field — the minimal configuration in which the hazard can be
isolated. A 1.5 n_cr target (flat top 20 d_e, Gaussian corona 15 d_e on the laser side,
centred at −50 d_e so the laser-facing face is at −40 d_e) is ablated by a 1.053 µm,
10¹⁸ W/m² beam entering at +z. Domain ±100 d_e, 400 cells at dz = 0.5 d_e.

**Length unit: d_e at critical density**, `d_e,cr = λ₀/2π = 0.1676 µm`. All five P0 runs
use it so their geometry numbers are directly comparable, and it is the only length
scale defined for a vacuum run (there is no ambient to reference).

`meta.expect_wrap: true` suppresses the validator warning that fires for exactly this
configuration — this run *is* the thing the warning warns about.

Parent: none (this is the Phase-0 baseline). Its opposite is `P0_bc_open`, which is
byte-identical except `boundary.axis` → `open`.

## Cost

400 cells × 2 species × 200 ppc = 160k macroparticles, 24 000 steps (dt = 0.0978 fs →
2.35 ps). Measured wall time: see `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 (0.214 initial; limit 2 at 131 n_cr) | PASS |
| G2 dz/λ_D (target cold) | 61 | info — under-resolved by construction |
| G3 laser-off control | `P0_bc_periodic_off` declared, not yet created | WARN |
| G4 ray_cfl | 0.25, target overdense → interior critical surface | WARN — ladder not run |
| G5 ppc / Tlocalfrac | 200 target ppc | PASS |
| G6 energy closure | | post-run |

Note G1 is far more comfortable here than in the upstream deck (0.21 vs 1.91) because
`dz` is referenced to the *critical* skin depth, which is 4× finer than `d_e,ambient`.
That is a deliberate consequence of the length-unit choice, not luck.

## Result

*(not yet run)*

## Retracted

Nothing.
