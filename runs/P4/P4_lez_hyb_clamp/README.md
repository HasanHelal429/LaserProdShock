# P4_lez_hyb_clamp — the hybrid leg with the advection-CFL clamp (option 2)

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does capping the electron-energy advection CFL let the hybrid leg run the full
benchmark, and does it do so without distorting the ablation?

**Status: validated over 100 000 steps.** Identical to `P4_lez_hyb` in every physical
respect; the only difference is `solver.hybrid.ue_cfl_max = 0.5`.

---

## Why it exists

`P4_lez_hyb` aborts at step 80 145 with advection CFL 1.218. The cause was isolated by
controlled experiment (RESULTS 2026-08-12): with `electron_energy_mode = source_only` the
identical problem runs to completion, so the electron internal-energy advection is the
blocker. `u_e = (J_i - J)/rho` divides a noisy, near-zero `J` by a near-zero `rho` in the
tenuous plume; with `B0` = 0 and quasineutrality a real flow gives an advection CFL of
~0.007, so anything near 1 is noise.

`ue_cfl_max` caps `|u_e|` per component at that fraction of a cell per step. **This is a
numerical admission, not a physical model**: donor-cell upwind cannot represent transport
faster than one cell per step under any circumstances, so limiting there converts a hard
abort into a bounded, documented approximation.

The physically-motivated alternative is `n_trust` (option 1), which damps only the `J/rho`
term as density falls so that `u_e -> v_i`, the exact quasineutral current-free limit. That
one leaves the dense current-carrying region untouched and is the better choice for
production; this one is the guarantee that no run can die.

## Geometry

Identical to `P4_lez_hyb` — 2500 `d_e` box, 5000 cells, reflecting axial faces, 10 `n_cr`
aluminium target at `Z` = 13. See that run's README for the diagram and the two rescalings
(lengths x4.29, times x18.36).

## Result

Ran **100 000 / 100 000** steps with **zero** CFL aborts, against step 80 145 for the
unclamped deck. Absorption held at **0.726 of peak** with `Tlocalfrac` = 1, so the clamp is
not distorting the deposition.

Still to establish: whether the clamp perturbs the ablation-front structure relative to the
`n_trust` run. Since the clamp acts wherever the CFL would be exceeded — not only in the
tenuous plume — that has to be measured rather than assumed.

## Retracted

Nothing. Note for provenance: an earlier attempt to film the option-2 run was abandoned
because it shared `diags/` with the option-1 test, which overwrote it — the collision
`scripts/launch.sh` exists to prevent, and which was reintroduced by invoking WarpX
directly. This directory exists so the movie comes from uncontaminated output.
