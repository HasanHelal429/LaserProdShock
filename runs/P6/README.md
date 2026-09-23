# Phase 6 — the mass-convention experiment

**One question.** A reduced mass ratio can be bought two ways. Which one, if either,
reproduces the full-mass-ratio physics at reduced-mass cost?

Phase 5 established that lightening the ion is not free: `T_ss ~ mu^(1/3)` (fitted 0.322)
and optical depth `~ mu^0.490` (fitted 0.490), where `mu = m_i/m_i,real`. Two repairs that
leave the ion light were tried and both were refuted — rescaling the handoff temperature
by `mu^(1/3)` made absorption *worse* (predicted `<f_abs>` 0.856, measured 0.2735), and
raising intensity by `mu^(-1/2)` gave `T_e` 322.7 eV against a predicted 416 because
`f_abs` fell (`d(ln f_abs)/d(ln I)` = −0.285). The conclusion on record is **only more ion
mass fixes it** (HANDOFF.md 7.4).

Raising the *electron* instead keeps the ion real at the same computational mass ratio.
That is PSC's convention, and until now this project could not express it: `deck.py`
hardcoded the real `m_e`, and the deposition operator derived `n_cr` and the energy kick
from a single mass. Both are now fixed (`reference.electron_mass_scale`; the operator's
optical/dynamical split).

## The three legs

| leg | convention | `m_i/m_e` | `mu` | `d_e` | cells | steps | `dz/λ_D` | cost |
|---|---|---|---|---|---|---|---|---|
| `P6_mr_full`  | real e⁻, real ion  | 49542 | **1.000** | 0.1693 µm | 22040 | 9139500 | 58.1 | 1.00× (**~73 h**, measured) |
| `P6_mr_light` | real e⁻, light ion | 2698  | **0.0545** | 0.1693 µm | 22040 | 497700 | 58.1 | ~0.036× (**~2.6 h**) |
| `P6_mr_heavy` | **heavy e⁻**, real ion | 2698 | **1.000** | 0.7257 µm | 5136 | 2133000 | **249.0** | ~0.06× (**~4.5 h**) |

Plus one G3 laser-off control each — six runs.

**The design.** B and C share `m_i/m_e` = 2698 exactly and differ only in which mass moved.
So if C matches A, that cannot be explained away as 2698 being a generous mass ratio: B
proves it is not.

**The prediction.** A and C agree; B is low by the measured exponents. C costs what B costs.

**First result, before any physics.** Measured in flight: C runs in ~4.5 h against A's ~73 h —
a **16× speedup** against the predicted 18.4×. Throughput does not scale perfectly with cell
count, so the saving is 16× rather than 18.4×; the cost half of the hypothesis holds.

## Why `ω_pe·dt` does not degrade, and `dz/λ_D` does

`ω_pe ∝ 1/√m_e` falls by exactly the factor `dt` rises with `dz ∝ d_e ∝ √m_e`, so
`ω_pe·dt` is **invariant** — measured 0.5534 at t=0 and 0.7826 at 2× compression on all
three legs. The binding stability limit is untouched, which is why the 4.285× coarser grid
is free.

`λ_D` is mass-**independent**, so `dz/λ_D` degrades by the full 4.285×: 58.1 → 249.0. That
is the real price and the real risk. It is also why each leg carries its own laser-off
control: the three legs do not share a grid-heating background, and an unsubtracted
comparison would read that difference as physics.

## Judged on

`zeta_cr`, `L_n`, and `uza/C_S0` = 0.548 against FLASH — **geometry, not temperature**. The
broken real-mass leg's `T_e` was off 5% while its scale length was off 4×. `E_abs`
differences below ~3% are not measurements (1σ of GPU scatter at fixed seed is 1.32%).

## Decisions

- **D1** Straight rays (`refraction = 0`) on all six. Straight-ray converges (+0.02% ± 0.66
  on the last `ray_cfl` increment); the refracting RK4 march drifts +18.3% over the same
  rungs, and 95% of that sits in the trajectory rather than the analytic layer.
- **D2** `ray_cfl = 0.05`, the established production value, so P6 differs from
  `P5_flashic` in the mass convention and the march — not in a third thing.
- **D3** Leg C's `ic_flash.yaml` nodes are divided by √18.3625 = 4.2851. The table is
  quoted in `z/d_e` and C's `d_e` is that much larger, so this is an **exact change of
  abscissa, not a re-fit** — the physical profile is bit-for-bit leg A's.
- **D4** `laser_deposition.electron_mass` is pinned to the real mass on leg C. Letting the
  operator resolve it from the species would rescale `n_cr` by 18.4× and drive the 10 `n_cr`
  target underdense.
- **D5** No seed repeats in this first round. A-vs-B is a 2.6×/4.3× effect and needs none.
  **A-vs-C is an agreement claim and will need 3 seeds each before it can be asserted** —
  held back deliberately until there is a result worth costing.
- **D6** No finer-`dz` leg C up front. If C disagrees with A the first suspect is the grid,
  and the finer-`dz` repeat is the discriminator — but running it now would pre-empt a
  disagreement rather than test one.

## Correction — leg B is not what this table says (2026-09-23)

`P6_mr_light`'s initial condition was never similarity-scaled: only the time family was
applied, and its lengths and velocities are the mu = 1 leg's. In its own normalised units it
starts 4.285x too wide and 4.285x too slow (uza/C_S0 ~0.128, not 0.548). It therefore does
NOT test the reduced-mass convention, and the mu-exponent predictions in the table above do
not apply to it as built. Full account and the fix in `P6_mr_light/README.md`, Retracted.
Legs A and C are unaffected -- both are mu = 1 and need no similarity map.

## Status

All six configured, decks rendered, gates checked. **Not yet launched** — GPU submission
from `m5032_g` is currently refused by NERSC's policy plugin (CPU submission works; other
users' GPU jobs run normally).
