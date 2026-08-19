# P4_lez_kin_ic6_long — `P4_lez_kin_ic6` run 4× longer, to τ_own 108

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** Does the kinetic leg reach quasi-steady ablation at all, and at what
temperature? `P4_lez_kin_ic6` ended with `T_e` **still climbing** (129.8 → 183.8 → 224.6 →
271.2 eV, increments 54/41/47, no sign of a plateau) and `f_abs` still at **0.992**, so
`f_abs`, `ζ_front` and `L_n` were all being read off a transient rather than a converged
state.

**This is not more benchmark.** FLASH ends at τ = 27 (1 ns) and, on the aligned clock, the
kinetic leg already covers FLASH's entire run by τ_own = 24.3. There is no FLASH data beyond
that. What this tests is the WarpX leg's *own* approach to steady state.

**Expected.** `T_e` plateaus and `f_abs` falls away from 0.992 as the target goes underdense.
Three outcomes, all informative:
1. plateau near its own `T_e,SS` = 312 eV → right physics, slower approach; the τ = 27
   disagreement is a transient;
2. plateau elsewhere → converges to a genuinely different state, which is real disagreement;
3. no plateau at all → something is pumping energy in — but see below, that is now unlikely.

**Falsified by.** Outcome 3, which after the G3 result would need an explanation other than
grid heating.

**Why no numerical caveat.** `P4_lez_kin_ic6_off` (2026-08-19) measured the grid-heating
contribution and found it **negative**: the laser-off run's electrons *cool* by 35 %, and the
energy they lose turns up in the ions (+1.944e5 J against −1.794e5 J, closing to 8 %). So the
parent's rising `T_e` is laser absorption, and `dz/λ_D` = 253 in the cold solid is harmless
for this measurement — as the plume value of 1.8 predicted.

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
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 2211840 steps = 218.6 ps
```

## Setup
`P4_lez_kin_ic6` with `max_step` 552 960 → **2 211 840**, and the diagnostic intervals scaled
by the same 4× so the dump *count* is unchanged (`runs/README.md`'s `_long` rule) rather than
producing 4× the data. Deck diff against the parent is duration and diagnostic cadence and
nothing else.

**Domain risk, recorded in advance.** The domain is unchanged at −50 … 2450 `d_e`. The
parent's plume front reached 510 `d_e` — **21 %** — and its growth was *decelerating*
(increments in ζ per 5.4 τ: 12.6, 11.2, 10.9, 7.4, 5.4). Extrapolating that, 4× duration
lands near 1300 `d_e`, comfortably inside. But `T_e` is still rising, so the plume may
*re-accelerate* as it heats, and the estimate is an extrapolation of a decelerating trend
under a drive that has not saturated. The `hi` boundary is `open`, so an overshoot bleeds
plume rather than reflecting it — the failure mode is a G6 energy-closure loss, not an
instability. **Check the front against 2450 `d_e` before quoting anything from late times.**
The domain was deliberately NOT enlarged, so the run stays comparable to its parent.

## Cost
5000 cells × 500 ppc × 2 211 840 steps. The parent was 21 min, so **~84 min** on one RTX 4070.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` | 0.783 | PASS |
| G2 `dz/lambda_D` solid / plume | 253 / 1.8 | INFO |
| G3 laser-off control | **passed on the parent** — grid heating measured NEGATIVE | PASS (inherited) |
| G4 `ray_cfl` | 0.25 | PASS |
| G5 ppc | 500 | PASS |
| G6 energy closure | **0.876** = (ΔKE+ΔFE)/E_abs, with 53.5 % macroparticle / **0.89 % weight** loss | LOSS, not heating |

## Result
**Outcome 3: no plateau at τ_own 108** — but not for the reason outcome 3 was written to
catch, and both secondary expectations came out backwards. Full entry: RESULTS.md
2026-08-19 (extended).

- `T_e` still rising significantly at τ 70–108: `Te_at_cr` **+1.751 ± 0.436 eV/τ** (4.0 σ),
  `Te_mean_plume` **+2.092 ± 0.225 eV/τ** (9.3 σ). The last four dumps *look* flat
  (501→522→524→522 eV); the regression says they are not.
- It **is** converging, slowly. `T(τ) = T_∞ − A e^(−τ/τ_relax)` gives `Te_at_cr` →
  **381.5 ± 21.5 eV**, `τ_relax` = 44.3, i.e. **1.22 × its own `T_e,SS` = 312 eV**, 93.8 %
  reached. `Te_at_cr` is the Manheimer comparator; the band mean (620 eV, 1.99 ×) is pulled
  up by the hot tenuous far plume and is the wrong number to judge against `T_e,SS`.
- **The asymptote is unreachable in this configuration.** `n_peak` = 18.66 exp(−τ/38.7)
  crosses 1 `n_cr` at **τ ≈ 113**, five τ after this run ends and far short of ~3 `τ_relax`.
  The target is consumed as fast as the temperature relaxes. Quasi-steady ablation needs a
  **thicker/denser target**, not a longer run — this closes the "just run it longer" route.
- **`f_abs` rose, it did not fall**: time-mean 0.282 (τ<10) → **0.975** (τ 78–108), run-mean
  0.823. The plume goes optically thick over 2500 `d_e` (`Vskip` → 0 by τ ≈ 30) long before
  the target thins; the absorber becomes the plume.
- **Domain risk half-materialised.** The `1e-2 n_cr` front hit 2450 `d_e` at **τ 78.2**; the
  bulk `0.1 n_cr` contour reached only **1302 `d_e`**, inside — the README's extrapolation
  was right for the bulk, wrong for the tenuous precursor.
- **Late data survive it**: outflow is **supersonic (Mach 2.3–4.8) at the wall at all
  times**, so the boundary is causally disconnected from the ablation region. Local
  quantities near the critical surface are sound to τ 108. Band-integrated quantities
  (`ζ_front`, `L_n`, `Te_mean_plume`) are truncation-contaminated from **τ ≈ 102** (edge
  `n_e` crosses the `1e-2` band floor at τ 93); `ζ_front` pins at the wall.
- No shock: phase space is a pure self-similar rarefaction fan, no reflected population.

Movies: `media/P4/P4_lez_kin_ic6_long/{movie_fields,movie_phase}.mp4`.

## Retracted
Nothing from this run. Noted against the *parent*: `f_abs` "still 0.992" was an
**instantaneous** `laser_report` sample, not a time-mean — the same statistic here reads
1.0000 instantaneously against a run-mean of 0.823. Quote a windowed mean instead.
