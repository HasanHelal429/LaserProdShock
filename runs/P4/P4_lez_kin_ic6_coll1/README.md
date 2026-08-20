# P4_lez_kin_ic6_coll1 — is the `T_e`/`T_i` over-equilibration a collision-supercycling artifact?

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** WarpX collapses `T_i/T_e` from **0.308** (matching FLASH's 0.293) to **1.216**
within one ion response time, destroying the `T_e ≫ T_i` state that is the paper's headline
result — while FLASH holds ≈0.3 throughout and PSC, at the **same reduced mass ratio and the
same IB kernel**, tracks FLASH's `T_e` to 0.92–0.96× (RESULTS 2026-08-19, PSC preliminary).
Is that WarpX's collision **supercycling**?

**Why supercycling is the suspect.** WarpX runs `ndt_supercycle = 10`; the Perez et al. 2012
operator requires `ν·Δt ≪ 1`, and supercycling multiplies the effective `Δt` tenfold. PSC uses
the same `collide_every = 10` but **instruments the violation** — its large-angle counter
reads `FRACTION LA` ≈ **0.78** in our run — whereas **WarpX has no equivalent diagnostic**, so
we do not currently know whether its `ν·Δt` is in range in the plume. Note the Coulomb log
runs the *wrong way* to explain the discrepancy (PSC's collision lnΛ ≈ 8.28 exceeds WarpX's
6.3 by 31 %, so PSC should equilibrate *faster*), which is part of why the cadence is the
remaining suspect.

**Setup.** `P4_lez_kin_ic6` with **`collisions.intervals` 10 → 1** and nothing else changed.
`laser.intervals` stays at 10, so this is a single-variable test. Duration cut to
`max_step` = 110592 (τ_own 5.39) — enough to cover both PSC comparison points — with ic6's
dump cadence kept, so the times line up exactly.

**Control.** `P4_lez_kin_ic6` itself. Its dumps already sit at τ_own 0, 1.35, 2.70, 4.04, 5.39.

**Expected, with numbers.** The control reads:

| τ_own | `T_e` | `T_i` | `T_i/T_e` |
|---|---|---|---|
| 0.00 | 377.2 | 116.3 | 0.308 |
| 1.35 | 131.8 | 160.2 | **1.216** |
| 2.70 | 119.3 | 143.0 | 1.198 |
| 5.39 | 123.4 | 144.7 | 1.172 |

FLASH at the matched times gives `T_e` = 472 eV (0.15 ns) and 559 eV (0.20 ns); PSC gives
455 and 516 eV.

1. **If supercycling is the cause**: `T_i/T_e` stays near 0.3 and `T_e` stays in the
   400–500 eV band, approaching FLASH/PSC.
2. **If it is not**: `T_i/T_e` still runs to ≈1.2 and `T_e` still collapses to ≈120 eV. The
   operator itself — or genuine physics at the reduced mass ratio — is then responsible, and
   the next suspect is the Perez `σ_max` cap (D3's "1.5 capped point") or the absence of any
   mass-ratio correction in WarpX, where PSC explicitly boosts i–i by
   √(1836.15/`ReducedMassRatio`) = 4.285×.

**Falsified by.** Outcome 2. That would clear the cadence and move the investigation to the
operator's cross-section cap and its reduced-parameter handling.

**Cost.** ic6 was 21 min for 552960 steps; this is 110592 steps (20 %) with collisions 10×
more frequent. D3 measured collisions at ~10–15 % of step cost at `ndt` = 10, so expect
roughly **8–12 min**.

## Result
**Outcome 2 — the prediction is FALSIFIED. Supercycling is NOT the cause.** 14 min,
`reached max_step`, `--verify` OK.

| τ_own | | `T_e` | `T_i` | `T_i/T_e` | `T_e`/FLASH |
|---|---|---|---|---|---|
| 0.00 | ndt=10 / ndt=1 | 377.2 / 377.2 | 116.3 / 116.3 | 0.308 / 0.308 | 0.997 |
| 1.35 | ndt=10 | 131.8 | 160.2 | 1.216 | 0.279 |
| | **ndt=1** | **126.7** | **135.4** | **1.069** | **0.268** |
| 2.70 | ndt=10 | 119.3 | 143.0 | 1.198 | 0.213 |
| | **ndt=1** | **106.5** | **116.0** | **1.089** | **0.190** |
| 5.39 | ndt=10 | 123.4 | 144.7 | 1.172 | 0.191 |
| | **ndt=1** | **121.2** | **142.2** | **1.173** | **0.188** |

Collisions every step buy a **small, transient** improvement in `T_i/T_e` (1.216 → 1.069 at
τ 1.35) that has **vanished by τ 5.39** (1.173 vs 1.172). `T_e` is *slightly lower* with more
frequent collisions — the correct direction for more equilibration, and nowhere near enough
to close a 4× gap against FLASH (0.19×) or PSC (0.87–0.96× of FLASH).

**The collision cadence is cleared.** The over-equilibration is set by the operator's *rate*,
not how often it is applied.

**Cost note.** 0.0076 s/step against the control's 0.0023 — collisions every step is **3.3×**
the step cost, not the ~2× implied by D3's 10–15 % at `ndt` = 10.

## Retracted
Nothing from this run. The hypothesis it was built to test — that WarpX's `ndt_supercycle`
= 10 violates the Perez operator's `ν·Δt ≪ 1` requirement and thereby over-equilibrates — is
**refuted** and should not be carried forward.
