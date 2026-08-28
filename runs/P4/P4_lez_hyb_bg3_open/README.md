# P4_lez_hyb_bg3_open — hybrid with a 1e-3 n_cr background species

> ## [SUPERSEDED] — diagnostics deleted 2026-08-28
> **Boundary-condition twin of bg3 (`lo: open` as well as `hi`). Zero citations in RESULTS.md.**
> 
> Superseded by: **P4_lez_hyb_bg3**. `diags/` and `run.log` were removed to reclaim disk; the
> config, deck, `warpx_used_inputs` and this README are kept as the provenance record.
> Re-run from the config if the raw output is ever needed again.
> See `runs/P4/SUPERSEDED.md` for the full ledger.

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does a tenuous background species remove the low-density `u_e` divergence
outright, instead of clamping or switching off transport to survive it?

**Status: queued.** Runs after `P4_lez_hyb` (open boundaries) reports.

---

## Why

`u_e = (J_i − J)/ρ` diverges because `ρ` → 0 in the plume's tenuous edge. Both guards built
so far treat that: `ue_cfl_max` caps the result, `n_floor` switches transport off below a
threshold. Both alter the model. A background species instead removes the condition —
`ρ` is never near zero because there are genuinely ions there, with real dynamics that the
plume snowplows.

**Deliberately NO guards**: `ue_cfl_max` and `n_trust` are both off, so this is a clean test
of whether the background alone suffices.

## Geometry

Identical to `P4_lez_hyb` — 2500 `d_e`, 5000 cells, open axial faces, 10 `n_cr` target at
`Z` = 13 — plus a uniform `1e-3 n_cr` background at ~1 eV, 50 ppc.

## Result

Not yet run.

Measured cost of the background, computed before launching: areal density **0.35% of the
plume's**, i.e. mass loading two orders of magnitude below the 20 % tolerance the benchmark
is judged at.

## Retracted

Nothing. One correction carried from the design discussion: this is **not** a chamber gas in
the FLASH sense. FLASH's 10⁻¹⁰ g/cm³ is **2.95×10⁻¹⁴ `n_cr`**, ten orders of magnitude too
tenuous to bound `u_e`. FLASH needs a density floor for its own fluid reasons; this is our
choice on its own terms, and it should be justified as such rather than by appeal to FLASH.
