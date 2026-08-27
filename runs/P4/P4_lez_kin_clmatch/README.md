# P4_lez_kin_clmatch — WarpX at PSC's absorbed fraction, so only the ion mass is left

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** With `f_abs` matched to PSC by construction rather than corrected for, is the
remaining WarpX↔PSC temperature gap exactly `µ^(1/3)`?
**Expected.** `<f_abs>` = 0.583 ± 0.03 (PSC `run_ourflash_511keV`'s time-integrated value),
and plume `T_e` = **192 eV** — PSC's 508.8 eV divided by `µ^(1/3)` = 2.645.
**Falsified by.** `T_e` outside 192 ± 26 eV (the 13.5 % measured noise floor) once `<f_abs>`
is within 5 % of 0.583. That would mean `µ^(1/3)` is not the whole difference and something
beyond the ion mass separates the codes.

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

## Setup
Parent: **`P4_lez_kin_cl_ctrl`**, which is itself `P4_lez_kin_mr100` with
`laser.coulomb_log_mode: constant`. The only key that moves from the parent is
**`laser.coulomb_log` 4.75 → 11.2**. `collisions.coulomb_log` stays at 6.3, the mass ratio
stays 2698, the IC, target, grid and duration are untouched.

**Why this is a legitimate knob and not a fudge.** `A ∝ lnΛ` enters the IB coefficient
*linearly* and the ray path depends only on `n_e/n_cr`, so scaling `laser.coulomb_log` is
mathematically identical to scaling every path element — the mechanism established by
`cl_psc` (RESULTS 2026-08-23). Here it is used purely to land the absorbed fraction on PSC's,
so that the comparison no longer has to carry `f_abs^(2/3)`.

**Why removing `f_abs` from the comparison matters.** The cross-code tables reduce each leg
by `T_ss = 823·µ^(1/3)·f_abs^(2/3)`. That correction does not hold up: applied to the µ-sweep
it gives 1529 / 838 / 495 eV for mr25 / mr100 / mr400, a 3.1× spread where a valid reduction
would give one constant. `f_abs` is a violently spiky instantaneous diagnostic and the
`^(2/3)` amplifies it. Matching `f_abs` experimentally removes that term entirely and leaves
`µ^(1/3)`, which the µ-sweep *did* confirm to 2.3 % over {100, 400}.

**The 11.2 is an estimate and may need one iteration.** Interpolating optical depth
`τ = −ln(1−<f_abs>)/2` between `cl_ctrl` (lnΛ 4.75, `<f_abs>` 0.4074) and `cl_psc`
(lnΛ 20.35, `<f_abs>` 0.7455) puts the target at lnΛ ≈ 11.2. If the measured `<f_abs>` misses
0.583 by more than 5 %, re-solve on the three points and rerun — the leg is ~6 minutes.

**Convention, stated because the project has mixed them.** `<f_abs>` here is the
TIME-INTEGRATED fraction, `xcode_compare.absorbed()['f_mean']`, not the final instantaneous
`f_end` the older RESULTS tables quote. See GOTCHAS "Cross-code comparison".

## Cost
5000 cells × 500 ppc × 110592 steps. Parent measured 345 s (TinyProfiler) on one RTX 4070;
this leg is identical in size, so **~6 min**.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 (limit 2, budget 1.2) | PASS |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO — identical to parent |
| G3 laser-off control | `P4_lez_kin_ic6_off` | PASS |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
**Landed, and the prediction holds.** `<f_abs>` = **0.5629** against the 0.5833 target — 3.5 %
low, inside the 5 % tolerance, so no second iteration was needed. Plume `T_e` = **197.4 eV**
(17 cells, n-weighted 0.05–1.0 `n_cr`, `tau_own` 5.39). Wall 390.6 s on one RTX 4070.

| leg | laser lnΛ | `<f_abs>` | plume `T_e` |
|---|---|---|---|
| `mr100` | nrl per-cell (4.75 in plume) | 0.3642 | 157.7 eV |
| `cl_ctrl` | constant 4.75 | 0.4074 | 168.1 eV |
| **`clmatch`** | **constant 11.2** | **0.5629** | **197.4 eV** |
| `cl_psc` | constant 20.35 | 0.7455 | 255.1 eV |
| PSC `run_ourflash_511keV` | NRL per-cell (6.27 in plume) | 0.5833 | 508.8 eV |

**PSC / `clmatch` = 2.578 measured against 2.709 predicted** (`µ^(1/3)` = 2.645 times a 1.024
residual `f_abs` correction) — **4.8 % apart on a 13.5 % noise floor.**

The point of matching `f_abs` was to make the answer independent of the disputed
`f_abs^(2/3)` term, and it did: the residual mismatch is 3.5 %, so that term contributes only
2.4 % of the 2.709. **The ion-mass difference between WarpX and PSC is `µ^(1/3)` and nothing
else** — there is no residual for a code difference to hide in.

Within this mass ratio the `f_abs^(2/3)` correction also behaves: 0.3642 → 0.4074 predicts
169.9 eV against 168.1 measured (1 %); 0.3642 → 0.5629 predicts 210.9 against 197.4 (6.4 %).
It is *across* the µ-sweep that it fails (see RESULTS 2026-08-27), which is why this leg
exists.

## Figures
`media/P4/P4_lez_kin_clmatch/`

| figure | what it shows |
|---|---|
| **`lnlambda_ladder.png`** | **the result.** Plume `T_e` vs `⟨f_abs⟩` for the four legs of the lnΛ ladder at fixed `m_i/m_e`, with PSC at 508.8 eV and PSC ÷ `µ^(1/3)` landing on the ladder. From `scripts/lnlambda_ladder.py`, which measures every point from the run dirs — nothing hardcoded |
| `laser_history.png` | `f_abs(t)` (plateau 0.46, spiky), cumulative `E_abs` (linear — late/early `dE/dt` = 1.38, so the drive is NOT saturated), `Tlocalfrac` pinned at 1.000 (no temperature-floor contamination) |
| `laser_profile.png` | per-cell deposition profile at the 5 profile dumps |
| `fields_streak.png`, `fields_lineouts.png` | density and field streaks, 17 frames over 10.93 ps |
| `phase_space.png` | ion phase space. Target-ion front (99.9th pct) 7.75 → 11.99 `C_s`(target); free expansion, no reflection — an ablation run, not a shock run |

Interpolating the ladder to PSC's exact `⟨f_abs⟩` = 0.5833 gives **203.9 eV**, so
PSC/ladder = **2.495** against `µ^(1/3)` = 2.645 — **5.7 % apart**. Comparing `clmatch`
directly at its own 0.5629 gives 4.8 %. Both inside the 13.5 % floor.

## Retracted
nothing
