# P7_omega19_I5e13 — the 2019 OMEGA shot in 1D, laser-driven, middle intensity rung

**Phase.** 7, the laser-driven magnetized shock modelled on Schaeffer et al., PRL 122,
245001 (2019). This is the first rung of the drive-intensity calibration, at 5e13 W/cm².
**Question.** At 5e13 W/cm² (351 nm, 2 ns flat top), does the CH piston launch a precursor
that reaches TCC (x = 3 mm) at the measured ~750 km/s? If not, which way is it off, and by
how much?
**Expected.** A precursor time of flight within a factor ~1.5 of 750 km/s, since the
nominal OMEGA drive is ~3.5–7e13 W/cm². Planar 1D should over-drive the density at 3 mm
relative to the experiment, because there is no lateral expansion. In the pile-up the
paper measures n_e/n_e0 ≈ 10, T_e/T_e0 ≈ 10, and a compressed field B_y ≈ 23 T near
2.85 mm at t0 + 3.75 ns.
**Falsified by.** Any of these:
- the ambient heats far above 40 eV ahead of the piston: grid heating at dz/λ_D = 3, or
  laser leakage, since the laser must not heat it;
- the far plume runs out of particles despite splitting (n_e noise ≳ 50% at ~1e18);
- energy closure fails: E_abs against the particle-energy gain beyond the P6 grid-heating
  budget.

## Geometry
```
                                                               <== laser
      ##................................................................
      ^                                                                ^
      reflecting                                                    open
      z = -355                                                  z = +20888

  #  target flat top : 10 n_cr, 334.202 d_e thick, centred at -167.101 d_e
  ~  coronal ramp   : exponential, L_n = 12.5326 d_e on the LASER-FACING side (face at z = +0)
  .  ambient        : 9.9445e-05 n_cr, theta_e = 7.8278e-05  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 3.01 T along y (perpendicular to z), 1/w_ci0 = 3.47e+03 ps
  grid              : 33900 cells, dz = 0.62663 d_e, dt = 0.2502 fs, 17988000 steps = 4500 ps
```
d_e,ref = d_e at n_cr with the heavy electron = 0.2394 µm. The "B0" in the diagram is the
TCC value of the applied profile B_y = 10 T · x₀/(d + x₀), x₀ = 1.29 mm, where d is the
distance from the target face. The profile is applied to the particles; the grid carries
only the plasma's response.

## Setup
- **Drive.** 351 nm at 5e13 W/cm², normal incidence from +z, flat top from t0 to t0 + 2 ns
  (`intervals 0:7994660:10`). Straight rays, lnΛ per cell (nrl), Z_eff = 5.286 for CH.
  `heat_species: target`, so the laser neither sees nor heats the ambient.
- **Target.** CH at 10 n_cr (P6 cap D5; solid is ~38 n_cr), 80 µm thick, with a 3 µm
  exponential preformed ramp. The solid is at 1.26 eV, the ramp at 10 eV. Species C⁶⁺ and
  H⁺ at 1:1, each n_e/7, with real masses.
- **Ambient.** CH, C⁶⁺ + H⁺, n_e0 = 0.9e18 cm⁻³ (9.94e-5 n_cr), T_e = T_i = 40 eV.
- **Masses.** Heavy electron, m_p/m_e,sim = 100 (m_e × 18.36); ions real. The laser optics
  are pinned to the real m_e.
- **Numerics.** dz = 0.15 µm (3 λ_D,amb: the coarse pilot grid, decision 2026-10-12). cfl
  0.5, shape 3, filter 4. ppc 100 target / 50 ambient. `particle_splitter` on the target
  species at min_ppc 40, every 100 steps (warpx-cda `feature/particle-splitter`, 8699318af).
- **Collisions.** 17 pairwise-Coulomb pairs with lnΛ per cell. Piston-ambient ion pairs are
  omitted, because the precursor is collisionless in those.
- **Diagnostics.** z–u_z and z–u_x phase-space histograms for all 6 species every 10 ps
  (synthetic Thomson-scattering ion v_x at 3 mm); field frames every 15 ps (B_y, E_z, ρ by
  species); 30 subsampled particle dumps; checkpoints every 0.5 ns.

## Cost
- **Smoke run** (job 59722824, 40,000 steps = 10 ps, 1 A100): **10.3 ms/step** at
  5.33e6 macroparticles.
  - Clean: no NaN; f_abs 0.82 at 10 ps.
  - Ambient e⁻/H⁺ held at 40.0 eV: no grid heating yet.
  - The splitter had added 19,501 particles.
  - `lnLmean` ≈ 1.0 is the n_e²-weighted mean over the whole box, dominated by the 1 eV
    solid (P6 heavy reports the same 1.007 → 1.13).
  - An earlier attempt (59722579) aborted at init: 33,900 cells is not a multiple of the
    blocking factor 8. The domain is now 33,920 cells.
- **Run:** 33,920 cells × (100 target / 50 ambient ppc, split to ≥ 40) × 1.8e7 steps.
  Estimated ~55–75 h on one A100 as the plume grows.
  `perlmutter/submit.sh p7 --time 47:30:00 --chain 2`, jobs 59723061 → 59723064, launched
  2026-10-12.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` (10 n_cr / 2× compressed) | 0.991 / 1.401 | warn (budget 1.2) |
| G2 `dz/lambda_D` (target cold / ambient) | 1919 / 3.0 | ambient: the pilot's open question |
| G3 laser-off control | none | warn |
| G8 critical layer resolved | 0.2 cells at t = 0 | warn: the ramp self-steepens |
| G9 ion mass physical | 1.0 (composition) | pass |

## Result
*(after the run)*

## Retracted
Nothing.
