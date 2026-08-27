# P4_lez_kin_mrreal — WarpX at the REAL mass ratio: the ground truth the µ-sweep extrapolates to

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** What does the reduced ion mass ratio actually cost? Run the same problem with
real aluminium against a real electron and compare directly, with no similarity transform.
**Expected.** Plume `T_e` = **416 eV**, i.e. mr100's 157.7 eV × `µ^(1/3)` = 2.638, if the
scaling the µ-sweep confirmed over {25, 100, 400} extends to µ = 1. Against PSC's 508.8 eV
(real ion) and FLASH's 647 eV. `f_abs` is expected HIGH and possibly saturated — the IC is
pinned in raw eV, so the t=0 optical depth is 4.285× mr100's (`tau_est` 89.9 vs 21.0).
**Falsified by.** `T_e` outside 416 ± 56 eV (13.5 % noise floor). Below it, `µ^(1/3)`
over-predicts and the transform costs more than the scan says; above it, the scan's exponent
is too small and the reduced legs are further from truth than believed.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~
      ^                                                                ^
      reflecting                                                    open
      z = -214                                                  z = +10498

  #  target flat top : 10 n_cr, 192.826 d_e thick, centred at -96.4132 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 21424 cells, dz = 0.5 d_e, dt = 0.09885 fs, 2030600 steps = 200.7 ps
```

## Setup
Parent: **`P4_lez_kin_mr100`**, the µ-sweep's centre leg. Same recipe as the rest of the
scan, at `s = √(49542/2698.15)` = **4.28503**:

| family | keys | factor |
|---|---|---|
| lengths quoted in `d_e` | `thickness_de` 45→192.8263, `center_de` −22.5→−96.41315, `scale_length_de` 6.955→29.8024, `corona_offset_de` 2.3144→9.9173, `axis.lo_de` −50→−214.2514, `hi_de` 2450→10497.7486, `max_grid_size` 5000→21424 | `s¹` |
| times and step counts | `mass_ratio` 2698.15→49542, `laser.profile_intervals`, `max_step` 110592→2030600, the four `diagnostics.*_intervals` | `s²` |
| held fixed | `cfl` 0.35, `dz_over_de` 0.5, `ppc` 500, `particle_shape` 2, every `theta_*` (IC pinned in raw eV), `density_over_ncr` 10, `charge_state` 13, all laser and collision keys | 1 |

**`d_e`, `dz` and `dt` do not move.** `d_e` is a real-electron quantity and the electron is
real in every leg of this scan, so `dz` = 8.467e-08 m and `dt` = 9.885e-17 s are *bit-identical*
to mr100's — as they are across the whole existing sweep. That is why both numerical gates
read exactly the parent's values and this leg adds no new numerical risk, only cost.

**Two traps handled.** `2500·s/0.5` = 21425.1 cells, and AMReX aborts if `n_cell` is not
divisible by `blocking_factor` 8 (the deck never sets one, so the default applies) — trimmed
to **21424** = 8×2678, which is why `hi_de` is 10497.7486 and not 10498.32. And
`max_grid_size` is reset to 21424 to match: a 1D WarpX run on a GPU needs the whole domain in
one box or it loses 7.9×. `max_step` 2030600 is a whole multiple of `plotfile_intervals`
507650 and of `laser.intervals` 10, and lands at 5.390 `tau_own` — mr100's 5.39 to 4 figures.

**Why this leg is worth 4–6 h.** The µ-sweep spans µ ∈ [0.0136, 0.218] and every cross-code
statement extrapolates it to µ = 1, a factor 4.6 past the top rung. This is the rung. It also
lands on FLASH's and PSC's own ion mass, so its `T_e` is comparable to theirs in **raw eV**
with no reduction at all — the only leg in the project for which that is true.

## Cost
21424 cells × 500 ppc × 2030600 steps, one RTX 4070, `max_grid_size` = whole domain.
Measured ms/step on this GPU: mr25 2.110, mr100 3.121, mr400 4.541 — the scan's wall time
goes as **`s^2.55`, not `s³`** (per-step cost rises only ~1.47× per doubling of cells against
an ideal 2.0, i.e. the GPU is underused below ~10k cells). At 21424 cells it should saturate,
so the estimate brackets: `s^2.55` gives 3.9 h, linear-per-step gives 5.5 h, ideal `s³` gives
7.6 h. **Pilot-measured value below.**

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 (limit 2, budget 1.2) | PASS — identical to mr100 |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO — identical to mr100 |
| G3 laser-off control | `P4_lez_kin_ic6_off` (mr100 basis) | see note |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

G3 note: the existing `_off` control is at mr100's mass ratio and duration. Grid heating
accumulates with step count, and this leg runs 18.4× more steps, so the mr100 control does
**not** bound it. If G6 shows a non-trivial gap, an `_off` twin of this leg is required
before any energy statement — budget the same wall time again.

## Result
<pending>

## Retracted
nothing
