# P4_lez_kin_mr25 — does the plume `T_e` scale as `mu^(1/3)`, or not at all?

**Phase.** 4, `TEST_PLAN.md` §12. Leg 1 of 3 in the mass-ratio scan.

**Question.** Every WarpX Phase-4 leg sits at **0.26–0.38× FLASH's** plume `T_e` in raw eV,
while PSC — *same reduced mass ratio, same normalisation convention, same laser module* —
sits at **0.87–0.96×**. Two readings survive, and they make opposite predictions:

1. **Similarity.** `mu^(1/3)` = 2.638 is *exactly* the factor that leaves the
   inverse-bremsstrahlung optical depth `∫K dz`, `K ∝ n²Z lnΛ T^(-3/2)`, invariant when
   lengths scale by `√mu`. A reduced-mass run at equal `f_abs` is then **expected** to sit
   2.638× cooler in raw eV — and `1/2.638` = **0.379** sits at the top of WarpX's measured
   band. On this reading WarpX is correct and **PSC is the outlier**, overshooting its own
   steady state by 63 %.
2. **Invariance.** The paper's own `m_p/m_e` = {100, 400} scan reports *"good
   convergence"*, yet `mu^(1/3)` over a 4× mass change is `4^(1/3)` = **1.587**, a 59 %
   shift that "good convergence" would exclude. On this reading `T_e` does **not** scale,
   the similarity argument does not reach the measured temperature, and **WarpX's deficit
   is a real code difference**.

**This is a WarpX-only test.** No PSC, no FLASH, no cross-code normalisation — the thing
that has contaminated every comparison so far is absent by construction.

## Geometry

Identical physical setup to `P4_lez_kin_ic6_coldsolid` — same laser, same densities, same
initial condition **in raw eV** — with the ion mass changed and **every length defined in
`d_i0` rescaled by `s = √(mr/2698)`**, so the ζ-geometry and the duration in `tau_own` are
preserved. `dz` stays 0.5 `d_e` (the skin depth is set by `n_cr` and the *real* `m_e`, and
does not move).

| knob | value |
|---|---|
| `m_p/m_e` | **25** |
| `reference.mass_ratio` (`m_Al/m_e`) | 674.5 |
| `s = √(mr/2698)` | **0.5** |
| target `thickness_de` | 22.5 (= 4.5 `d_i0`) |
| corona `scale_length_de` | 3.4775 (= 0.6955 `d_i0`) |
| domain `[lo, hi]_de` | [-25, 1225] (= 2500 `d_i0`/10) |
| `max_step` | 27648 (= `tau_own` 5.39, so `∝ s²`) |
| wall-clock (cost `∝ s³`) | **~45 s** |

**Held fixed on purpose:** `theta_e_init`/`theta_i_init`/`theta_e_solid` (raw eV) and
`drift_uz_de`. Scaling the initial temperature by `s²` would build the similarity answer
into the initial condition; holding it fixed makes this a controlled experiment in which
**only the ion mass and the ζ-preserving lengths move**.

## Prediction

`T_ss` = 823/`mu^(1/3)` is the Manheimer steady state for each leg:

| leg | `m_p/m_e` | `m_Al/m_e` | `mu` | `s` | `T_ss` | vs `mr100` |
|---|---|---|---|---|---|---|
| `P4_lez_kin_mr25` | 25 | 674.5 | 73.45 | 0.5 | **197 eV** | 0.630 |
| `P4_lez_kin_mr100` | 100 | 2698.2 | 18.36 | 1 | **312 eV** | 1.000 |
| `P4_lez_kin_mr400` | 400 | 10792.6 | 4.59 | 2 | **495 eV** | 1.587 |

- **Similarity holds** → measured plume `T_e` tracks `T_ss`, a **2.52× spread** across the
  scan (0.630 : 1 : 1.587).
- **Invariance holds** → all three legs land within the **12 % run-to-run noise floor**
  (measured, CUDA non-reproducibility).

The two outcomes differ by **20×** relative to the noise. There is no ambiguous middle.

**Control.** `mr100` is the baseline repeat — it re-measures `P4_lez_kin_ic6_coldsolid` at
identical settings and therefore also re-measures the noise floor in this exact
configuration.

**Falsified by.** Either outcome falsifies the other. A result *between* 1.0 and 1.587 with
all three legs outside the noise band would mean the temperature scales with mass but not by
`mu^(1/3)`, and the exponent itself becomes the measurement.

## Result

*Pending — not yet run.*

## Retracted

*Nothing yet.* This scan exists **because** two earlier claims were retracted: that the
absorbed energy was lost to the under-dense solid (refuted — PSC's solid heats 13× and takes
a *larger* share while its plume stays 3× hotter), and that WarpX's target was 4.285× too
thin with an 18.36×-fast clock (refuted by PSC's `INIT_param.f`, which puts the mass ratio in
`DI0_code` and `TD0_code` but **not** in `K_temperature` — i.e. the two codes' conventions
are identical and the discrepancy was an artifact of comparing microns).
