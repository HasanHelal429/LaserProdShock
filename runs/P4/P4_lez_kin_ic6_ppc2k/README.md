# P4_lez_kin_ic6_ppc2k

**Phase.** 4, `TEST_PLAN.md` §12. See `config.yaml` `meta.description` for the full
statement of the check and its prediction, and RESULTS.md 2026-08-19 (root cause) for the
finding these two runs test.

**The finding under test.** WarpX absorbs `f_abs` = 0.15–0.32 where PSC absorbs 0.47–0.56 and
FLASH 0.870, on the same IC and with a kernel cross-validated to 8e-9. Traced in the source to
`LaserDeposition.cpp:703`, `m_theta_floor = m_theta_e` — the temperature floor **defaults to
`electron_temperature`** (here `th_t` = 378.3 eV) — and the gate at :1017 accepts a measured
per-cell temperature **only if `kT > kT_floor`**. The plume sits at ~120 eV, so the
measurement is never accepted, `Tlocalfrac` reads 0, and `K` is evaluated at 378.3 eV
everywhere. `K ∝ T^(-3/2)` makes that a **5.6×** under-estimate.

**Controls.** `P4_lez_kin_ic6` (the production configuration) on identical dump times, and
each other — A changes the floor, B changes ppc, neither changes anything else.

## Result
**NULL, exactly as predicted.** 16 min, `reached max_step`, `--verify` OK, ppc = 2000 in
`warpx_used_inputs`.

| τ_own | control `f_abs` / `Tlocalfrac` | **ppc 2000** |
|---|---|---|
| 0.50 | 0.142 / 0.000 | 0.126 / **0.000** |
| 2.70 | 0.217 / 0.000 | 0.187 / **0.000** |
| 5.39 | 0.319 / 0.000 | 0.268 / **0.000** |

`Tlocalfrac` stays at **0.000** at 4× the particles, and `f_abs` is unchanged (slightly lower,
within run-to-run scatter). `E_abs` 2.3805e5 → 2.1623e5 J.

**This is the control that makes check A interpretable**: the blocker is the temperature
**floor** (`kT > kT_floor`, floor defaulting to `electron_temperature` = 378.3 eV), **not**
macroparticle statistics (`min_macroparticles_per_cell`, default 4, easily met at 500 ppc).
Raising ppc cannot help, and did not.

## Retracted
Nothing yet.
