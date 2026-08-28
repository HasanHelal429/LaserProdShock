# P4_lez_kin_bg — the kinetic leg with the same background as `P4_lez_hyb_bg3`

> ## [DEFECTIVE] — diagnostics deleted 2026-08-28
> **Same Gaussian / 100 eV IC, plus a 1e-3 n_cr background 33940x denser than the chamber gas it stands for.**
> 
> Superseded by: **P4_lez_kin_ic6**. `diags/` and `run.log` were removed to reclaim disk; the
> config, deck, `warpx_used_inputs` and this README are kept as the provenance record.
> Re-run from the config if the raw output is ever needed again.
> See `runs/P4/SUPERSEDED.md` for the full ledger.

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does the 2.2–2.7× peak-density disagreement between the kinetic and hybrid
legs survive when the two differ in **one** thing — the electron closure — instead of two?

**Status: running.**

---

## Why it exists

The first kinetic↔hybrid comparison (2026-08-13) found `T_e` agreeing to 5–20 % but peak
`n_e` differing by **2.2–2.7×**, and the critical surfaces behaving qualitatively
differently (kinetic hovering at 130–190 `d_e`, hybrid marching to 442).

That comparison was **confounded**: the hybrid carried a 10⁻³ `n_cr` background — needed to
bound `u_e = (J_i − J)/ρ`, which is what finally let it complete — and the kinetic leg did
not. Two differences, so a disagreement could not be attributed to the closure.

Full PIC does not need the background at all. It is carried here **only** to restore the
one-variable comparison the phase is built on, at a measured cost of 0.35 % mass loading.

## Geometry

Identical to `P4_lez_kin` (2500 `d_e`, 5000 cells, open axial faces, 10 `n_cr` target at
`Z` = 13, `max_grid_size` = 5000) plus the ambient, matched to `bg3` at `namb = 0.001*ncr`
and 50 ppc. Verified identical: both decks emit `my_constants.namb = 0.001*ncr`.

## Result

Not yet complete.

**Gate note, accepted deliberately**: G2 warns the ambient is Debye-under-resolved,
`dz/λ_D` = 11.3 against a budget of 8. Raising the ambient temperature would fix it but
would break the match with `bg3`, and the target already sits at 113 by construction — so
the match is worth more than the 1.4× excess. Recorded rather than silently tuned.

## Retracted

Nothing. The earlier `P4_lez_kin` result is not retracted — it is valid on its own terms,
and remains the no-background reference. What is retracted is any attribution of the
density disagreement to the electron closure, pending this run.
