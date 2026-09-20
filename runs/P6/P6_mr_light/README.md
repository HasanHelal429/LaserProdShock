# P6_mr_light — LEG B — reduced mass the usual way (μ = 0.0545)

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** Does the known reduced-mass penalty reproduce at exactly the `m_i/m_e` that leg C uses?
**Expected.** **This leg is predicted to FAIL, quantitatively.** `T_ss` down by `mu^(1/3)` = 0.379× and
optical depth by `mu^0.490` = 0.24×, both fitted (0.322 and 0.490).
**Falsified by.** `T_ss` and optical depth landing on leg A's. That would overturn the `mu` scalings the
whole Phase-4/5 analysis rests on, and P6's premise with them.

---

## What this run is

`m_i/m_e` = 2698 at a **real** electron, so the ion is 18.4× too light and `mu` = 0.0545.
Same grid as leg A; 497700 steps, because the ion response time is `mu` times leg A's — this
covers the same 24.26 `tau_own` in 49 ps of lab time rather than 900 ps.

Neither repair recovers the penalty: rescaling the handoff temperature by `mu^(1/3)` made
absorption *worse* (predicted `<f_abs>` 0.856, measured 0.2735), and raising intensity by
`mu^(-1/2)` gave `T_e` 322.7 eV against a predicted 416 because `f_abs` fell.

**Why it is in the group.** Without it, leg C agreeing with leg A could be dismissed as the
mass ratio 2698 simply being good enough. B and C share that mass ratio *exactly* and differ
only in which mass was moved. B is what makes C's result mean something.

## Geometry

Identical to leg A: `d_e` = 0.1693 µm, `dz` = 0.0847 µm, 22040 cells,
axis −521.4251 → 10498.5749 `d_e`, `dt` = 9.885e−17 s, 497700 steps.

## Gates

G1 **pass** (0.5534 / 0.7826). G2 info, `dz/λ_D` = 58.1. G8 0.215.
G9 **warn**, `mu` = 0.0545 — expected and intended.

## Cost

**≈ 2.6 h**, measured in flight (93181 steps in 28.9 min). First submitted at a 2 h wall on a
wrong ≈0.5 h estimate; a 6 h continuation is chained behind it. **~0.036×** leg A.

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
