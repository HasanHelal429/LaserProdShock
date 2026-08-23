# P4_lez_kin_cl_psc — PSC optical depth, laser lnΛ = 20.35

**Phase.** 4, `TEST_PLAN.md` §12. One of a matched pair with the other `cl_*` leg.

**Question.** PSC's laser module converts `z → z·K_length` (cm) before integrating the
inverse-bremsstrahlung absorption, and `K_length = DI0_phys/√mr` with `DI0_phys` the **real**
proton skin depth. At the same ζ-profile PSC's optical depth is therefore **4.285×** WarpX's,
whose `d_e` **is** the real 0.1693 µm. Is that the mechanism behind the plume-`T_e` gap?

**Why lnΛ is the right knob.** `A ∝ Z_eff·lnΛ/(kT_e)^{3/2}` enters `K` **linearly**, and the
ray **path** — refraction and turning point — depends only on `n_e/n_cr`, not on `K`. So
scaling lnΛ by 4.285 is **mathematically identical** to scaling every path element by 4.285.
It reproduces PSC's length mapping *inside the absorption integral*, at the reduced mass
ratio, for **6 minutes** instead of the 1.8 h a true length rescale costs.

Only `laser.coulomb_log` moves. `collisions.coulomb_log` stays at 6.3.

## Geometry

`P4_lez_kin_ic6_coldsolid` unchanged — `mass_ratio` 2698, target 45 `d_e`, domain
[-50, 2450] `d_e`, `max_step` 110592, 500 ppc. The **only** deck differences are
`coulomb_log_mode` `nrl` → `constant` and `coulomb_log` → **20.35**.

| leg | laser lnΛ | role |
|---|---|---|
| `cl_ctrl` | **4.75** | the MEASURED `nrl` plume mean (per-cell dump, 168 cells, max 6.03) |
| `cl_psc` | **20.35** | 4.75 × 4.285 — PSC's optical depth |

The control exists so the pair isolates the 4.285× from the `nrl` → `constant` mode switch.

## Prediction

Baseline `mr100` gives `f_abs` 0.350 and plume `T_e` 157.7 eV, and **sits at 1.02× its own
analytic steady state** `T_ss = 823·µ^(-1/3)·f_abs^(2/3)` = 154.9 eV.

- **Optical depth is the mechanism** → `cl_psc` raises `f_abs` toward saturation and `T_e`
  toward the ceiling, with `cl_ctrl` unchanged from baseline.
- **It is not** → `f_abs` moves but `T_e` does not track `f_abs^(2/3)`.

**The known ceiling.** At `m_p/m_e` = 100, `f_abs` → 1.0 gives `T_ss` = **312 eV**. PSC sits at
**509 eV, 1.63× above that ceiling**, so this pair can confirm the *mechanism* but **cannot**
reach PSC's number, and is not expected to.

**Falsified by.** `T_e` failing to follow `f_abs^(2/3)`, or `cl_ctrl` differing from the
`nrl` baseline by more than the 13.5 % noise floor.

## Result

*Pending — not yet run.*

## Retracted

*Nothing yet.* See `RESULTS.md` for the two retractions and one un-retraction that led here.
