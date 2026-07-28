# P0_bc_inject — what happens when the plume reaches the laser injection face?

**Phase.** 0, `TEST_PLAN.md` §5.1, §5.2

**Established from the operator source first** (`LaserDeposition.cpp`, ray launch):

```cpp
c0[m_axis] = m_inject_hi ? phi[m_axis] : plo[m_axis];
```

Rays are launched **exactly on the injection boundary plane**, not one cell inside it. So
the boundary cell's plasma is traversed and absorbs from the very first RK4 step, and
`deposit` clamps its cell index into the valid box. Nothing special happens at the face.

**Question.** The ablation plume always flows *back up the beam*, so it eventually
reaches the launch plane. From then on the laser is absorbed at the boundary rather than
at the target. Is that transition physical absorption in the blow-off, or does it couple
to the pec/absorbing boundary and make the drive history a boundary artifact?

**Expected.** `f_abs(t)` should track `P0_bc_open_B` while the beam's path is clear, then
depart once the plume arrives at the face — with the deposition profile's peak migrating
from the target's corona toward the +z boundary. That is real: a beam is absorbed in the
plasma it has to cross.
**Falsified by.** `f_abs(t)` departing from `P0_bc_open_B` **from t = 0**, which would
mean the target's position alone changed the drive and the two runs are not comparable;
or the absorbed power showing a discontinuity or non-monotonic jump exactly at the
arrival time, which would indicate boundary coupling rather than absorption.

## Setup

Identical to `P0_bc_open_B` except `plasma.target.center_de: -50 → 40`, putting the
laser-facing face at **+50 d_e**, i.e. 50 d_e from the +z injection face instead of
140 d_e. At t = 0 the corona density at the face is 2×10⁻⁵ n_cr — optically negligible,
so the beam starts with a clear path; the plume then reaches the launch plane well inside
the run rather than at the very end. That separation matters: it is what makes "before"
and "after" both observable in one run.

`profile_intervals` is 4000 rather than 8000, giving 7 deposition-profile dumps, because
the migration of the deposition peak toward the face is the actual observable here.

Parent: `P0_bc_open_B`.

## Cost

400 cells × 4 species, 24 000 steps (2.35 ps). See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 | PASS |
| G2 dz/λ_D | target 61, ambient 1.73 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 200 target | PASS |
| G6 energy closure | | post-run |

## Result

*(not yet run)*

## Retracted

Nothing.
