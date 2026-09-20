# P6_mr_heavy — LEG C — the same mass ratio, bought the other way (μ = 1)

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** Can we have leg A's physics at leg B's cost?
**Expected.** Agreement with leg A on `zeta_cr`, `L_n`, `uza/C_S0` and `<f_abs>`, at **18.4× less cost**.
**Falsified by.** Disagreement with leg A beyond the 1.32% scatter. But the first suspect is then the
GRID, not the convention — see the risk below — and the discriminator is a finer-`dz` repeat.

---

## What this run is

`m_i/m_e` = 2698, identical to leg B, reached by raising the electron to 18.3625 `m_e`
instead of lightening the ion. The ion is therefore **real aluminium** and `mu` = 1, exactly
as in leg A. This is PSC's convention ("PSC's ion is REAL aluminium at every
ReducedMassRatio").

`d_e` = 0.7257 µm — PSC's skin depth — so every length in `d_e` is leg A's divided by
√18.3625 = 4.2851, and `ic_flash.yaml`'s nodes are rescaled by the same factor. **That
rescale is an exact change of abscissa, not a re-fit**: the physical profile is bit-for-bit
leg A's and no fit residual is introduced.

**Why it should work.** `ω_pe ∝ 1/√m_e` falls by precisely the factor `dt` rises with
`dz ∝ d_e ∝ √m_e`, so `ω_pe·dt` is **invariant** — measured 0.5534 and 0.7826, identical to
legs A and B. The binding stability limit does not degrade, so the coarser grid is free.

**What it costs, and this is the real risk.** `λ_D` is mass-**independent** while `dz` grows
as `√m_e`, so `dz/λ_D` degrades 58.1 → 249.0. Grid heating rises, which is why the G3
laser-off control is mandatory here rather than good practice. The finer-`dz` repeat is
deliberately NOT run up front, so that it tests a real disagreement instead of pre-empting one.

## Geometry

`d_e` = **0.7257 µm**, `dz` = 0.5 `d_e` = 0.3628 µm, **5136 cells** (÷8 = 642),
axis −121.6819 → 2446.3181 `d_e`, `dt` = 4.236e−16 s, 2133000 steps = 1.000 ns.

## Gates

G1 **pass** (0.5534 / 0.7826 — invariant, the whole mechanism). G2 info, `dz/λ_D` = **249.0**.
G8 0.215. G9 **pass**, `mu` = 1.

## Cost

**≈ 4.5 h**, measured in flight (228284 steps in 28.9 min). First submitted at a 2 h wall on a
wrong ≈0.5 h estimate; a 6 h continuation is chained behind it.

**~16× cheaper than leg A** (4.5 h against 73 h) against a predicted 18.4×. Throughput does not
scale perfectly with cell count, which is why the saving is 16× and not 18.4× — but the cost
half of the hypothesis is already substantially confirmed, before any physics is compared.

## The findings this leg is built on

* **`refraction = 0`** — straight rays, Snell invariant carried analytically. Straight-ray
  CONVERGES (last `ray_cfl` increment +0.02% ± 0.66, 0.0σ); the refracting RK4 march drifts
  +18.3% over the same rungs, and the `n_floor` attribution sweep put **95% of that in the
  trajectory**, not the analytic layer.
* **`ray_cfl = 0.05`** — the G4-ladder production value, converged in both march modes.
  Held so P6 differs from `P5_flashic` in the mass convention and the march, not a third thing.
* **`near_critical_fix` ON** (operator default) — drives `overfrac`, the deposit landing in
  evanescent cells, from 0.57 to exactly 0. It does **not** fix `ray_cfl` convergence: that
  was tested against a criterion written in advance and failed (+8.62% ON vs +8.78% OFF).
  Straight rays are what fixes convergence.
* **The operator's optical/dynamical mass split.** Without it a heavy-electron leg either
  rescales `n_cr` by 18.4× — driving a 10 `n_cr` target underdense — or misses the energy
  budget by the mass factor (measured 3.98×).
* **Checkpointing on.** Multi-hour runs; the queue wall is not negotiable.

## Judged on

`zeta_cr`, `L_n`, `uza/C_S0` = 0.548 against FLASH — **geometry, not temperature**. The
broken real-mass leg's `T_e` was off 5% while its scale length was off 4×. `E_abs`
differences below ~3% are not measurements: 1σ of GPU scatter at fixed seed is 1.32%.

## Result

NOT YET RUN.

## Retracted

Nothing yet.
