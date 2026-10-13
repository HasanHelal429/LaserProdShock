# P8_hyb_laser_CH — OMEGA 2019 shot in 1D, HYBRID (kinetic ions, fluid electrons)

**Phase.** 8: hybrid twins of `P7_omega19_I5e13` (the kinetic, heavy-electron run of the
same shot). The matrix is drive {laser, heater} × ions {effective CH, C⁶⁺ + H⁺}.
**This run.** Drive: the 351 nm laser at P7's 5e13 W/cm² (2 ns flat top), deposited into the electron FLUID (`density_source: hybrid_rho`, `temperature_mode: hybrid_fluid`, `deposit_to: electron_fluid`). Ions: one effective CH ion, Z = 3.5, A = 6.50 (target and ambient).
**Question.** Does a hybrid model, at real ion masses and real densities and with no
electron kinetics (so no Debye, ω_pe or grid-heating constraint), launch a precursor that
reaches TCC (3 mm) at ~750 km/s, with n_e/n_e0 ≈ 10, T_e/T_e0 ≈ 10 and B_y ≈ 23 T near
2.85 mm at t0 + 3.75 ns, as the shot measured?
**Falsified by.** Precursor speed far from 750 km/s after calibration; an upstream T_e that
runs away before the piston arrives (laser variants: the 1D ambient-heating caveat below);
B_y never compressing above the 3 T upstream value; the hybrid aborting on the electron-energy
advection CFL or the density floor (whistler substeps are sized for the floor).

## Setup (from `config.yaml`, which is the source of truth)
- **Same physics as P7:** an 80 µm CH target at 10 n_cr with its face at z = 0, a 3 µm
  exponential corona, a 40 eV CH ambient at 0.9×10¹⁸ cm⁻³ on both sides, the coil field
  B_y = 10 T·x₀/(d+x₀) (x₀ = 1.29 mm, 3 T at TCC), and a 5 mm box. It runs to 4.5 ns.
- **Hybrid numerics:**
  - dz = 2 µm (2,544 cells; P7 uses 0.15 µm).
  - dt = 400 fs (particle CFL 0.4 at 2000 km/s), 11,250 steps.
  - 194 whistler substeps: 10× the requirement in the 10 T ambient, 1× at the 0.1 n_amb
    density floor.
  - Advected electron energy, uniform 40 eV start; η = Spitzer at 400 eV (1.6×10⁻⁷ Ω·m).
  - Shape 1, no filter, ppc 200/200.
  - Ion–ion collisions only (no electron particles).
- **Coil field on the grid:** the hybrid's Ohm's law sees only the grid B. In 1D its curl
  is carried as electron current, and the unbalanced ∇B²/2µ₀ pushes the ambient (~5% of
  v_sh by 10 ns).
- **Caveat:** Hybrid deposition cannot be restricted to the target, so in 1D the beam also heats the ambient column, ~400 eV/ns at 40 eV (P7 avoids it with `heat_species: target`). Read the upstream T_e before trusting the precursor.
- **Gates:** G4 and G8 warn as in P7, since the initial 3 µm corona is 1.5 cells. The corona
  builds itself within ~10 ps.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.2394 um

                                                               <== laser
      ##................................................................
      ^                                                                ^
      reflecting                                                    open
      z = -355                                                  z = +20900

  #  target flat top : 10 n_cr, 334.202 d_e thick, centred at -167.101 d_e
  ~  coronal ramp   : exponential, L_n = 12.5326 d_e on the LASER-FACING side (face at z = +0)
  .  ambient        : 9.9445e-05 n_cr, theta_e = 7.8278e-05  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 3.01 T along y (perpendicular to z), 1/w_ci0 = 3.47e+03 ps
  grid              : 2544 cells, dz = 8.35507 d_e, dt = 400 fs, 11250 steps = 4500 ps
```

## Launch
`perlmutter/submit.sh p8` (warpx-fix `build_fix`, which carries the hybrid solver, the hybrid
laser swaps and the electron-fluid heater). Branch `hybrid-omega`, generator changes: the
profiled B goes on the grid when hybrid; `operators.heater` (electron fluid) is new.

## Result
**ABORTED** at step 466 (t = 186 ps; debug array 59724252, 2026-10-12): `Non-finite value detected in E-field` (WarpXPushFieldsHybridPIC.cpp:227). A true vacuum gap (n_e = 0) opened at z ≈ 84-86 µm between the expanding plume and the swept ambient, and B ran away there (2.1e4 T). The density floor keeps Ohm's law finite, but the whistler requirement scales as B/n_floor, and with no vacuum treatment the Hall term blew up. All four first-pass runs failed this way; the matrix is rerun as `*_hv` with `holmstrom_vacuum_region = 1`.

## Retracted
Nothing yet.
