# P5_flashic — the phase spine: real mass, whole pulse, IC lifted from FLASH

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** With the initial condition lifted rather than fitted, is WarpX's plume `T_e`
still below FLASH's — and is the ratio flat (a code difference) or rising (a stopwatch
artifact)?
**Expected.** The 1.80× optical-depth excess the analytic fit carried is gone by
construction (measured 1.0038 on the rendered deck, below). If absorption was the whole
story, the `T_e` ratio should move toward 1. If it does not, the residual is real physics.
**Falsified by.** A `T_e` ratio that is *unchanged* from the analytic leg's — that would
say the IC fidelity never mattered and the 2026-08-29 audit mis-attributed the gap.

---

## What this run is

The Phase-5 headline. Real aluminium ion, real electron, no similarity transform anywhere,
run for the whole of FLASH's flat top (`t_FLASH` 0.1 → 1.0 ns) on FLASH's own 0.02 ns dump
cadence, with **all four handoff profiles lifted straight from FLASH's plotfile** instead
of fitted to it.

## The initial condition, and why it is not a fit

`corona_profile: flash_table` replaces the four-parameter analytic exponential with a node
table (`ic_flash.yaml`, tracked) that `scripts/flash_ic_fit.py` fitted directly to FLASH's
0.1 ns state and `deck.py` renders as WarpX parser expressions. Measured on the **rendered
deck**, evaluating its own parser strings against FLASH:

| | analytic exponential | **this run** |
|---|---|---|
| `rms(ln n)` vs FLASH | 0.107 | **0.0032** (26 nodes) |
| `T_e` relative rms | *isothermal — not applicable* | **0.0030** |
| optical depth ratio vs FLASH, same grid | **1.798** | **1.0038** |

Three assumptions go at once, and the third is the one that has already cost this project:

1. the exponential **form** — `rms(ln n)` 0.107, and IB goes as `n²`;
2. the **isothermal corona** — `K ∝ T^(−3/2)`, so an isothermal assumption is an
   absorption knob, not a detail;
3. the **two-parameter linear velocity ramp** — the key whose scaling families
   (`uza ~ 1/s`, `uzb ~ 1/s²`) were held fixed once and cost a **4.05×** error in `L_n`
   (`HANDOFF.md` §6). A lifted profile has no scaling families to get wrong.

**Two departures from FLASH are kept**, both recorded in `ic_flash.yaml`'s `clamp` block
and both reported by the fitter: the **10 `n_cr` density cap** (the overdense interior is
not representable on a uniform PIC grid) binding on 46.6 % of cells, and a **`T_e` floor**
at `theta_e_solid` where FLASH's cold interior is Debye-unresolvable, binding on 45.6 %.
Both are the solid, as intended.

**Config keys that are now INERT.** With the density coming entirely from the table,
`thickness_de`, `scale_length_de`, `corona_density_over_ncr`, `corona_offset_de`,
`theta_e_init`, `theta_i_init` and `drift_uz_de` shape nothing. They are deleted from this
config rather than left in place, and `make_inputs.py` prints a NOTE if any reappear — a
key that *looks* load-bearing and is not is exactly how a fork-only input went unnoticed
for 27 runs in the sibling project.

The target's extent is now wherever the table's flat tail runs to, i.e. the domain edge at
−521 `d_e`. That is ~2.6× the paper's 4.5 `d_i0` and it is deliberate: steady ablation at
this leg's own `C_S` removes ~9.7e21 ion/m² over 0.9 ns, which is 39 % of a 4.5 `d_i0`
target at the cap and 15 % of this one.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 9139500 steps = 903.4 ps
```

## Gates

| gate | value | verdict |
|---|---|---|
| G1 `ω_pe·dt` | 0.553 at `t` = 0, 0.783 at 2× compression (limit 1.2) | PASS |
| G2 `dz/λ_D` in the solid | 58.1 | known departure |
| G4 `ray_cfl` | 0.25 | **gated by `P5_raycfl_*` — run that ladder first** |
| G5 ppc / `Tlocalfrac` | 500, mode `local` | PASS |
| G3 laser-off subtraction | `P5_flashic_off` | concurrent |

## Cost

`P4_lez_kin_mrreal_drift` ran 2 030 600 steps in 4 h 24 m on one RTX 4070. This is 4.5013×
that → **≈ 19.8 h on a 4070**, and an A100 is ~1.5–2.5× that machine on these decks, so
**≈ 8–13 h on Perlmutter**. Submitted single-GPU (`numerics.max_grid_size = n_cell` is one
box and one box cannot be split across ranks). See `perlmutter/README.md`.

## Result
*(to be filled in after the run — including what is retracted)*

## Retracted
nothing yet — the run has not been launched.
