# P6_mr_full — LEG A — the reference (μ = 1, real electron)

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** What do the FLASH observables look like with no mass convention in play at all?
**Expected.** `T_ss` at its full 823 eV ceiling and `<f_abs>` near 0.84. Absorption is not broken by
construction here — this is the only regime in which a cross-code number may be quoted
without a `mu` correction.
**Falsified by.** Nothing internal. This leg DEFINES the reference; if it disagrees with FLASH the
problem is upstream of the mass question entirely, and P6 stops until that is understood.

---

## What this run is

Real aluminium ion **and** real electron: `m_i/m_e` = 49542, `mu` = 1. No mass scaling of
any kind, so the WarpX clock IS the FLASH clock — this covers FLASH's flat top to 1.000 ns
exactly, with every dump landing on a real FLASH plotfile time and needing no interpolation.

The expensive leg, deliberately. Its price is the measurement being bought.

## Geometry

`d_e` = 0.1693 µm (= λ₀/2π), `dz` = 0.5 `d_e` = 0.0847 µm, 22040 cells,
axis −521.4251 → 10498.5749 `d_e`, `dt` = 9.885e−17 s, 9139500 steps = 1.000 ns.

## Gates

G1 **pass** (`ω_pe·dt` 0.5534 at t=0, 0.7826 at 2× compression). G2 info, `dz/λ_D` = 58.1.
G8 0.215 — the critical layer is sub-grid, as on every lifted-IC leg. G9 **pass**, `mu` = 1.

## Cost

**≈ 73 h**, MEASURED — `P5_flashic/progress.log` reports 0.0321 s/step at this exact grid and
step count, i.e. `ETA ~73h20m`. Submitted as **4 chained 24 h segments**; checkpointing plus
`--signal=1@600` carries the state across the walls.

CORRECTION: this section first said 8–13 h, taken from `P5_flashic`'s README rather than from
its own telemetry. That README estimate is wrong by 6–9× and the run's `progress.log` said so
from its first 10% mark. **1.00×** — the reference cost.

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
