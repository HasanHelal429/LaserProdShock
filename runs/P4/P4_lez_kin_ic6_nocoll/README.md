# P4_lez_kin_ic6_nocoll — collisions OFF: the decisive bound on the collision hypothesis

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** Are collisions responsible *at all* for WarpX collapsing `T_i/T_e` from 0.308 to
≈1.2 within one ion response time, while FLASH and PSC hold `T_e ≫ T_i`?

**Why this run and not a cap test.** Two suspects were on the list; both are now closed
analytically or empirically:

- **Cadence** — `P4_lez_kin_ic6_coll1` (`intervals` 1) converged to the `intervals` 10 control
  by τ 5.39 (`T_i/T_e` 1.173 vs 1.172). Refuted.
- **The Perez `σ_max` cap** — (i) `sigma_eff = min(π b0² lnΛ, σ_max)` can only *reduce* `s12`,
  so removing it makes equilibration *faster*, the wrong direction; (ii) on **e–i**, the
  channel that governs `T_e`↔`T_i`, `(π b0² lnΛ)/σ_max` = **0.055 / 0.255 / 1.18** at
  n = 0.01 / 0.1 / 1 `n_cr` and 120 eV, i.e. **essentially inactive across the plume band**.
  It is strongly active on **i–i** (3–680), but i–i transfers no energy *between* species.
  Rebuilding WarpX to disable it would cost hours to confirm a predictable null.

Switching collisions off bounds the whole hypothesis in one 10-minute run.

**Setup.** `P4_lez_kin_ic6` with `collisions.enabled: false`, `max_step` = 110592 (τ_own 5.39).
Controls: `P4_lez_kin_ic6` (`ndt` = 10) and `P4_lez_kin_ic6_coll1` (`ndt` = 1), both on
identical dump times.

**Expected.**
1. **If collisions are the cause**: `T_e` stays near its 377 eV start and tracks FLASH/PSC
   (472/455 eV at τ 1.35, 559/516 at τ 2.70), and `T_i/T_e` stays near 0.3.
2. **If they are not**: `T_e` still collapses toward ~120 eV and `T_i/T_e` still rises. The
   collision operator is then exonerated entirely and the search moves to the laser kick
   (which deposits into electrons) or to the expansion dynamics.

**Falsified by.** Either outcome is informative; outcome 2 would retire the collision
hypothesis that has driven the last three runs.

**Caveat, stated in advance.** With collisions off the run is not physical — e–i thermalisation
and collisional absorption both vanish, so `f_abs` will change too. This is a *diagnostic
bound*, not a physics run, and its `T_e` is an upper bound on what removing collisional
coupling can buy.

## Result
**Outcome 2 — the collision hypothesis is RETIRED.** 3 min, `reached max_step`, `--verify` OK,
and `warpx_used_inputs` contains **zero** `pairwisecoulomb` entries.

| τ_own | ndt=10 | ndt=1 | **OFF** | FLASH | PSC |
|---|---|---|---|---|---|
| 2.70 `T_e` | 119.3 | 106.5 | **176.7** | 559.3 | 516.0 |
| 2.70 `T_i/T_e` | 1.198 | 1.089 | **0.468** | 0.325 | — |
| 5.39 `T_e` | 123.4 | 121.2 | **162.5** | 646.3 | 562.9 |
| 5.39 `T_i/T_e` | 1.172 | 1.173 | **0.640** | 0.352 | — |

Collisions **do** drive the `T_i/T_e` inversion — off, the ratio returns to 0.47–0.64. But
`T_e` recovers only from 0.19× to **0.25×** FLASH: **three-quarters of the temperature deficit
survives with collisions completely disabled.** Collisions are a contributing factor, not the
cause.

## The actual cause: WarpX is not absorbing

`f_abs` = `Pabs`/I₀ in the same window:

| τ_own | WarpX `ic6` | PSC | FLASH |
|---|---|---|---|
| 0.50 | **0.153** | 0.47 | 0.870 |
| 2.70 | **0.218** | 0.56 | 0.870 |
| 5.39 | **0.322** | ~0.5 | 0.870 |

WarpX absorbs **3× less than PSC and 4–6× less than FLASH**, on the same initial condition,
with a kernel cross-validated against PSC's to 8e-9. That is why its electrons cool
(377 → 177 eV) while FLASH's heat (378 → 559 eV): expansion cooling beats the drive.

**Leading candidate — `Tlocalfrac` ≈ 0.0000 for the whole run.** `temperature_mode: local`
is essentially never delivering a measured per-cell `T_e`, so the IB coefficient is evaluated
on the **fallback** `laser_deposition.electron_temperature` = `th_t` = 378.3 eV instead of the
actual ~120 eV plume. With `K ∝ T^(-3/2)` that under-estimates absorption by
`(378/120)^1.5` ≈ **5.6×** — the size of the observed deficit. `CLAUDE.md` gate G5 says in so
many words: *"local temperature mode needs ppc … Watch `Tlocalfrac`."* It was not watched.

**To confirm** (not yet done): re-run with `temperature_mode: constant` at a realistic ~130 eV
and check `f_abs` rises ~5×; and/or raise ppc until `Tlocalfrac` is O(1).

## Retracted
**The collision hypothesis, in full.** RESULTS 2026-08-19 (PSC preliminary) concluded "the
WarpX discrepancy is electron–ion over-equilibration". That is **demoted**: the equilibration
is real and collision-driven, but it accounts for only ~25 % of the `T_e` gap. The primary
cause is the absorbed fraction. The `σ_max` cap and the collision cadence are both cleared.
