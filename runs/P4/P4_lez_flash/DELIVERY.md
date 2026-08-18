# FLASH leg delivered — inventory and accounting

Collaborator: J. Ploegstra (`jploegstra`), run on chablis 2026-08-17, 8 MPI ranks.
Two runs delivered, both from the deck in this directory, both completed
(`exiting: reached max SimTime`, t = 1 ns, no aborts, no NaN, no HYPRE failures).

| | radiation OFF | radiation ON |
|---|---|---|
| shared folder | `FLASH_LaserAblation-Ploegstra_2026-08` | `FLASH_LaserAblationRad-Ploegstra_2026-08` |
| run subdir | `Ablation_prod_08-17` | `Ablation_prod_rad_08-17` |
| basename | `lez1d_` | `lez1drad_` |
| size | 36 MB | 45 MB |
| steps / wall | 6 019 / ~38 s | 24 919 / 253 s (6.7x) |

Locations are under `/mnt/cellar/shared/simulations` (reachable as `~/shared/simulations`).

## 1. What is in each folder

Identical layout in both:

* **51 plotfiles** `*_hdf5_plt_cnt_0000..0050`, every 0.02 ns, t = 0 .. 1.0002 ns.
  Variables: `dens depo tele tion velx sumy ye`.
* **11 checkpoints** `*_hdf5_chk_0000..0010`, every 0.1 ns. Full state, 35 vars
  (39 with radiation): adds `eele eion erad pele pion prad trad cond fllm shok
  tite`, plus rad-only `absr emis mgdc r001`.
* **1 forced plotfile** `*_forced_hdf5_plt_cnt_0000` — the end-of-run dump.
* `flash.par` — the deck as run (staged copy, patched in place; the FLASH source
  tree was **not** modified).
* `flash4` — the executable, alongside `amr_runtime_parameters.dump`.
* `Al_1group_FLASH.prp` — the PROPACEOS table, byte-identical between the two runs
  (sha256 `75a37f39...`); supplies **both** EOS and 1-group opacity.
* `EOS_printout_tables.txt` — 1.8 MB EOS dump.
* `*.dat` — 8-column scalar time series: time, mass, 3x momentum, E_total,
  E_kinetic, E_internal. 6 021 / 24 921 rows.
* `*_LaserEnergyProfile.dat` — per-step laser energy: specified in, **unabsorbed
  out**, and the two increments. NB: "Energy out" is the ray energy *leaving the
  domain*, so absorbed = in − out.
* `*.log` + `flash.out` — the production log plus **6 (no-rad) / 3 (rad) numbered
  logs from earlier attempts**, which are the debugging history, not extra runs.
* `media/` + `scripts/` — the collaborator's own figures and the code that made them
  (see §4).
* `PROVENANCE` — setup line, binary and par sha256, EOS provenance, and for the rad
  run a full outcome block. Excellent; it is the file to read first.

## 2. Three real bugs in our shipped deck, found and fixed

1. **`ed_power` unit error — the laser was 1e7x too powerful.** We wrote
   `1.0e20` believing erg/s; FLASH reads watts and multiplies by `ed_Joule2erg`
   internally (`ed_setupPulses.F90:104`). The deck as shipped would have run at
   1e20 W/cm², not 1e13. Verified fixed: measured flat-top power is
   **1.000000e13 W**, delivered energy 9 506.5 J against 9 500 J expected for a
   0.1 ns ramp + 0.9 ns flat top (ratio 1.0007).
2. **`sim_rhoCham = 1e-7` was a symptom, not a fix.** It had been raised for dt
   stability; with the power corrected the paper's **1e-10 g/cm³ runs fine**. (The
   rad deck still carries a stale header comment claiming 1e-7; the body is 1e-10.
   The comment is wrong, the value is right.)
3. **EOS table substituted.** Our `ionmix4` / `al-imx-003.cn4` does not exist in
   their tree; they used PROPACEOS `Al_1group_FLASH.prp` and added the three
   settings the working OmegaShock config needs: `eos_useLogTables = .false.`
   (PROPACEOS energy columns are not sign-definite, so log interpolation is
   invalid), `eos_tolerance = 1e-8`, `eos_maxNewton = 100000`. **Caveat:** this
   table's floor is 2 eV, so our 290 K initial condition is ~2 decades below it and
   is met by edge extrapolation. Affects t = 0 only.

Our `# CHECK` items all resolved as written: `sim_teleTarg` in kelvin, `ms_targZMin
= 13`, `ed_gridType_1 = "regular1D"`, unit cross-section. Only ignored parameter
was `gr_pmrpAmrErrorChecking`.

## 3. Physics content

Grid as specified: `nblockx = 8`, `nxb = 16`, `lrefine_max = 4` → dx_min 0.781 µm,
17 leaf blocks / 272 cells at 1 ns (peaks at 464 during the transient).

Measured from the plotfiles (n_e from `dens*ye*N_A`, cross-checked: solid Al gives
795.5 n_cr, exact):

| t [ns] | Te_max [eV] OFF / ON | n_e,max/n_cr OFF / ON | x(n_cr) [µm] OFF / ON | rho_max/rho_solid OFF / ON |
|---|---|---|---|---|
| 0.10 | 379 / 382 | 904 / 903 | 51.9 / 51.9 | 1.14 / 1.14 |
| 0.20 | 569 / 563 | 1192 / 1208 | 55.9 / 55.9 | 1.50 / 1.52 |
| 0.40 | 726 / 722 | 2081 / 2056 | 60.6 / 59.8 | 2.62 / 2.58 |
| 0.60 | 825 / 808 | 2732 / 2632 | 68.4 / 62.9 | — |
| 0.80 | 894 / 881 | 3423 / 3287 | 73.1 / 66.0 | — |
| 1.00 | **953.5** / **935.6** | 4141 / 3730 | 78.9 / 67.6 | 5.21 / 4.69 |

* **Laser absorption 87.04 % (OFF) / 84.06 % (ON).**
* Energy closure: mesh dE_total 8 059 J vs 8 274 J absorbed → **97.4 %** for the
  no-rad run (remainder leaves the outflow boundaries). The rad run closes to 83 %,
  the 17 % being radiation leaving through the `vacuum` MGD boundaries — expected,
  not an error. Mass conserved to 0.002 % in both.
* **T_e peaks at 953 eV / 936 eV**, i.e. FLASH sits just above the 823 eV Manheimer
  steady state and matches the paper's ~800 eV plateau.

### Radiation changes very little — the paper's Fig. 1 claim, reproduced
Profiles at 1 ns are indistinguishable beyond x ≈ 100 µm. Peak T_e differs by
1.9 %, peak T_i by 7 %, v_max by 0.4 %. The differences are confined to the
ablation front, where rad-OFF holds a higher-density shelf and pushes the critical
surface 11 µm further out. T_rad reaches 55.3 eV with radiation on vs 0.17 eV off,
so the module is genuinely active. **This validates using the radiation-OFF run as
the PIC comparison leg.**

### Two caveats for our analysis
* **`nele` is missing from the plotfiles.** `plot_var_8 = "nele"` was accepted as a
  parameter but is not a mesh variable in this build, so FLASH silently dropped it.
  Use `n_e = dens * ye * N_A` — exact, not an approximation.
* **Ion temperature at t ≤ 0.4 ns has a vacuum artifact.** Peak T_i reads 78 keV at
  0.1 ns, 141 keV at 0.2 ns, 208 keV at 0.4 ns — but these sit at x = 110–623 µm in
  *undisturbed* 1e-10 g/cm³ chamber vapour with no heat capacity, carrying ~5e-10 of
  the mass, far ahead of the plume. By 0.6 ns they are gone (407 eV). This matters
  for **D1**: initialising WarpX from the 0.1 ns snapshot must mask on density or it
  imports a 78 keV ion population. The radiation-ON run does not have the artifact
  (157 eV at 0.1 ns) because radiation drains those cells.

## 4. Their figures (`media/`)

Radiation OFF: `handoff_0p1ns.png` (the D1 snapshot: rho, T_e, v_x — 380 eV flat
across the plume, v_x ramping to 980 km/s, 5-decade density ramp out to 110 µm),
`profiles_evolution.png` (0.2–1.0 ns), `spacetime.png` (log dens and log tele as
(x,t) maps), `laser_coupling.png`, `timestep.png`, and `figures.html` (1.8 MB,
self-contained page).

Radiation ON: `rad_profiles_evolution.png`, `rad_spacetime.png`,
`rad_radiation_field.png`, plus five rad-vs-norad comparisons
(`compare_profiles_1ns / _trad / _laser / _timestep / _delta.png`) and
`figures_radiation.html`.

Both `scripts/` dirs contain the generating code, with documented colour choices
(single-hue ordinal ramps for time, categorical only for the two configurations,
no dual axes, no rainbow). `make_rad_figures.py` hardcodes
`NORAD = /home/jploegstra/cellar/data/Ablation_prod_08-17`, so it needs that path
edited to re-run against the shared copy.

## 5. Operational note recorded by the collaborator

`flash4` links Open MPI (`libmpi.so.40`), but the `PATH` `mpirun` on chablis is
MPICH from `miniconda3/envs/flash_env`. **Absolute `/usr/bin/mpirun` must be used**;
a bare `mpirun` silently starts 8 independent serial jobs.
