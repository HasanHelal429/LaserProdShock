# `runs/P4/` — superseded and defective runs

**Nothing here was deleted outright.** Each run below keeps its `config.yaml`, `README.md`,
generated deck and `warpx_used_inputs`, so it can be re-run and so the defect stays on record.
What was removed on **2026-08-28** is `diags/` and the raw `run.log` — 7.2 GB of output whose
conclusions are already in `RESULTS.md`. Each run's own README carries a banner naming the
defect and the successor.

A second 2.4 GB came from pruning `run.log` on the runs that were **kept** — see
`scripts/prune_run_log.py`. A finished 1D run writes four lines per step, so at 2e6 steps the
log is 692 MB of `STEP n starts` for a few hundred thousand diagnostic lines. The pruner keeps
every `LASERDEP` line, the header, the TinyProfiler footer, the last step and every
warning/error, verifies the re-parse matches, and refuses to touch a run still in flight.
`f_abs` re-measured identically on `mr100`, `clmatch` and `mrreal_drift` afterwards.

**P4 went from 14 GB to 4.6 GB.**

## Defective — built on a bug, a wrong IC, or a retired convention

| run | the defect | superseded by |
|---|---|---|
| `P4_lez_kin_mrreal` | IC corona drift **4.29× too fast** in its own `C_S0` (`uza/C_S0` 2.349 vs FLASH's 0.548). `drift_uz_de` was held fixed, but it is a velocity needing `1/s` and its ramp `1/s²`. Opened a density notch propagating at 2.28 `C_S0`; `L_n` came out 4.05× FLASH's | `P4_lez_kin_mrreal_drift` |
| `P4_lez_kin_flashic_ct` | Corona **5.19× too extended** — `scale_length_de` 6.955 and `corona_offset_de` 2.3144 never rescaled when `mass_ratio` went 2698 → 100 (should be 1.339 / 0.4456). Ledger 17. The A/B against `_res` still stands; the absolutes must not be quoted | `P4_lez_kin_ic6` |
| `P4_lez_kin_flashic_res` | Same 5.19× corona defect; its own README already retracts the reservoir motivation | `P4_lez_kin_thick` |
| `P4_lez_kin_ic6_ppc2k` | Ran on the **broken temperature-floor** configuration (`f_abs` 0.13–0.27), so it cannot settle the ppc question it was built for | `P4_lez_kin_cs_ppc4k` |
| `P4_lez_kin` | Analytic Gaussian corona that fails the paper's own Fig-2 test (peak deposition ζ 4.13 vs FLASH's 0.27), **and** `theta_e_init` 1.957e-4 = 100 eV, the retired IC convention. Its headline claim is ledger 15 | `P4_lez_kin_ic6` |
| `P4_lez_kin_bg` | Same Gaussian / 100 eV IC, plus a 1e-3 `n_cr` background **33 940× denser** than the chamber gas it stands for | `P4_lez_kin_ic6` |
| `P4_lez_kin_bg5` | Killed at 30.1 %; RESULTS records it was testing the wrong axis, and its declared laser-off control never existed | the table at `RESULTS.md:3970+` |
| `P4_lez_hyb` | Ran `electron_energy_mode: advected`, documented unusable; aborted at 36.9 % on CFL 1.218 | `P4_lez_hyb_clamp` |

## Superseded — sound runs whose question a later run answered better

| run | why | superseded by |
|---|---|---|
| `P4_lez_kin_flashic` | Reservoir-motivated 40 `n_cr` / 20 `d_i0` target rather than the paper-faithful 10 / 4.5. **Not** a carrier of the 5.19× bug — its `mass_ratio` was never changed | `P4_lez_kin_ic6` |
| `P4_lez_kin_ic6_long` | Ran 4× longer; `T_e` still rising because the target ran out first | `P4_lez_kin_thick` |
| `P4_lez_kin_ic6_coll1` | Collision-cadence hypothesis refuted; its README says it should not be carried forward | `P4_lez_kin_ic6_nocoll` |
| `P4_lez_kin_ic6_nocoll` | Collisions-off bound; hypothesis demoted to ~25 % of the gap | closed by ledger 21 |
| `P4_lez_kin_ic6_nmin4` | Density-floor / reservoir hypothesis measured and refuted: < 4 %, wrong direction | closed by ledger 20 |
| `P4_lez_hyb_bg3_open` | Boundary-condition twin of `bg3`; zero citations in RESULTS.md | `P4_lez_hyb_bg3` |
| `P4_lez_hyb_bg4` | 1e-4 background leg; its one number is recorded and the background axis was retired | axis retired |

## Kept, and why — do not delete these

- **`P4_lez_kin_ic6_off`** is the `controls.laser_off` for **14 runs**, including the live
  `clmatch` and `mr100`. Deleting it voids their G3 gate.
- **`P4_lez_kin_thick_off`** is the sole G3 control for the live `P4_lez_kin_thick`.
- **`P4_lez_kin_ic6_pscheat`** is the declared A/B control for `ic6_coldsolid`.
- **`P4_lez_kin_cl_ctrl`** and **`cl_psc`** are the two interpolation anchors that set
  `clmatch`'s lnΛ = 11.2. Without them that choice is unreproducible.
- **`P4_lez_kin_ic6_coldsolid`** supplies one of the six samples the 12–13.5 % noise floor is
  measured from.
- **`P4_lez_kin_mr25` / `mr400`** are held until their `_drift` reruns are compared; their
  uncorrected `drift_uz_de` line is the evidence for the defect.

## Two dangling controls, pre-existing

- `P4_lez_kin_flashic/config.yaml:155` and `P4_lez_kin_bg5/config.yaml:170` both name
  `controls.laser_off: P4_lez_kin_flashic_off` — **that run has never existed.**
- `P4_lez_kin_off` exists but was never launched (no `diags/`), so `P4_lez_kin` and
  `P4_lez_kin_bg` were effectively un-controlled too.

Neither matters now that all four are superseded, but a future leg must not inherit the
reference.
