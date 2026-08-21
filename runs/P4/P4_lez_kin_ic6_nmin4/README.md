# P4_lez_kin_ic6_nmin4 — match PSC's ELECTRON RESERVOIR, not just its heating

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** At comparable absorbed fraction (PSC 0.47–0.56, WarpX `pscheat` 0.42–0.46) PSC's
electron energy grows **5.5×** over t_F 0.1→0.2 ns while WarpX's grows **1.2×**. Is that because
WarpX spreads the same absorbed joules over a **larger, colder electron population**?

**Why this is now the leading candidate.** The PSC laser-off control (2026-08-20) **retracted**
the electron-drain hypothesis: with no laser *both* codes convert electron energy to ion energy
and **PSC drains faster** (0.518 vs WarpX's 0.739 at t_F 0.2 ns). So the difference is
**resupply**, not drain. The one structural difference in the electron population is the
density floor: PSC's fixed macroparticle weight puts it at `n_cr`/NPPC = **1e-3 `n_cr`**;
WarpX's uniform 500 ppc carries electrons down to **1e-5 `n_cr`**.

**Setup.** `P4_lez_kin_ic6_pscheat` — already PSC-equivalent in heating (floor 1 eV,
`min_macroparticles` 1, `coulomb_log_mode` nrl) — with **`density_min_frac` 1e-6 → 1e-4**
and nothing else changed. That makes the floor `1e-4 × 10 n_cr` = **1e-3 `n_cr`, exactly
PSC's**. Deck diff against the control is the two `density_min` lines only.

**Control.** `P4_lez_kin_ic6_pscheat`, identical dump times.

**What is already known, and why this is not redundant.** `studies/ppc_ladder` (2026-08-18)
varied this knob and concluded 1e-6 was better — **on shape**. The same data goes the other way
on magnitude:

| leg | floor | `RISE` (shape) | `⟨T_e⟩` at τ 27 |
|---|---|---|---|
| FLASH | — | 1.148 | **839.0 eV** |
| 4 decades | 1e-4 | 1.504 | **473.2 eV** |
| 6 decades | 1e-6 | **1.133** | **361.6 eV** |

The narrower floor was **1.3× hotter**. But those two legs also differ in the corona (analytic
Gaussian `L_n` = 27 vs the FLASH-fitted exponential 6.955), so the comparison confounds floor
with IC. **This run isolates the floor.**

**Expected.**
1. **Reservoir hypothesis holds**: `T_e` rises materially toward FLASH/PSC, and the electron
   share of the energy gain rises from 0.26 toward PSC's 0.65–0.69.
2. **It does not**: the reservoir is cleared and the resupply difference lies elsewhere.

**Falsified by.** Outcome 2.

**Stated cost, in advance.** This will likely **degrade the shape agreement** back toward
`RISE` ≈ 1.5, since that is what widening the floor fixed. If it buys magnitude at the price of
shape, that is a real tension between two acceptance metrics and must be recorded as such, not
reported as a clean win.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 110592 steps = 10.93 ps
```

## Result
**Outcome 2 — FALSIFIED. The electron reservoir is cleared.** 5 min, `reached max_step`,
`--verify` OK; deck diff against the control is the two `density_min` lines only.

| τ_own | | `T_e` | `T_e`/FLASH | `T_i/T_e` | e share | `f_abs` |
|---|---|---|---|---|---|---|
| 1.35 | pscheat (1e-6) | 165.2 | 0.350 | 1.002 | −0.738 | 0.380 |
| | **nmin4 (1e-4)** | **159.1** | **0.337** | 1.175 | −0.975 | 0.368 |
| 2.70 | pscheat | 171.3 | 0.306 | 1.006 | −0.100 | 0.377 |
| | **nmin4** | **165.1** | **0.295** | 1.056 | −0.122 | 0.455 |
| 5.39 | pscheat | 186.6 | 0.289 | 1.093 | 0.312 | 0.557 |
| | **nmin4** | **187.5** | **0.290** | 1.113 | 0.302 | 0.512 |

Raising the floor to PSC's exact value moves `T_e` by **<4 %, in the wrong direction** at two
of three times. The electron share does not improve. WarpX spreading energy over a larger,
colder electron population is **not** why PSC's electrons gain 5.5× where WarpX's gain 1.2×.

**And it reconciles with `studies/ppc_ladder`.** That study saw 473.2 → 361.6 eV on this knob
— but with the **analytic Gaussian corona, `L_n` = 27 `d_e`**. That corona spans 1 → 1e-5
`n_cr` over ~311 `d_e`, so dropping the floor adds ~125 `d_e` of tenuous plasma. The
FLASH-fitted exponential at `L_n` = 6.955 spans the same decades in ~80 `d_e` and adds only
~32 `d_e`. **The floor is a strong lever on a long corona and a weak one on a short corona**,
which is why the earlier magnitude change does not transfer to the current IC. The shape
result from that study is unaffected.

## Retracted
The reservoir-size hypothesis for the resupply difference, advanced in RESULTS 2026-08-20
(PSC control). Measured and refuted at the single-variable level.

## Retracted
Nothing yet.
