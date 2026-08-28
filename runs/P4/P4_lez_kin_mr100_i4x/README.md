# P4_lez_kin_mr100_i4x — raise the intensity by µ^(−1/2): does the temperature regime bring absorption with it?

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** A reduced-mass leg targets `T_ss` = 312 eV instead of 823 because
`T_ss ∝ µ^(1/3)`. Raising the intensity by `µ^(−1/2)` cancels that exactly, since
`T_ss ∝ I^(2/3)`. **Does restoring the temperature regime also restore the absorption
regime, or are the two separable?**
**Expected.** Plume `T_e` **157.7 → ~416 eV** (`157.7 × 4.285^(2/3)`), against the real-mass
leg's measured 440.2 — a 6 % agreement if the Manheimer scaling holds in `I` as well as it
does in `µ`. `⟨f_abs⟩` is **the open question**; both outcomes are informative.
**Falsified by.** `T_e` outside 416 ± 56 eV (13.5 % floor), which would mean `I^(2/3)` does
not hold at this intensity — the plume would then be off the Manheimer branch entirely.

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
Parent: **`P4_lez_kin_mr100`**. **One key moves**, and the generated deck differs in exactly
one line — verified by diffing `my_constants` and `laser_deposition` against the parent:

| key | parent | **here** |
|---|---|---|
| `laser.intensity` | 1.0e17 W/m² = 1e13 W/cm² | **4.285e17 W/m² = 4.285e13 W/cm²** |

`4.285` = `µ^(−1/2)` at `µ` = 0.054461. Mass ratio, IC, lengths, times, drift, `dz`, `dt`,
`cfl`, `ppc`, lnΛ and every collision key are untouched.

## What this is testing, and why the algebra cannot answer it
`T_ss = 5.94 µ^(1/3) Z^(−1/3) λ^(4/3) I^(2/3)`, so `I ∝ µ^(−1/2)` cancels the `µ^(1/3)` and
the leg should sit on the **real** 823 eV target while still carrying a 0.055× ion.

The absorption side is genuinely open. The static optical-depth formula does **not** describe
this campaign: `K ∝ λ^(−2) T^(−3/2) Z lnΛ` (verified numerically against `units.K_ib`) with a
path `L ∝ λ µ^(1/2)` gives `τ_abs ∝ λ^(−1) µ^(1/2) T^(−3/2)`, and evaluated with **each leg's
own measured plume `T_e`** that predicts `µ^0.017` — essentially invariant — against a
measured **`µ^0.490`**. A residual of `µ^0.474` is unaccounted for. `P4_lez_kin_mr100_sim`
already showed the missing physics is dynamic, not static: the plume forgets the handoff
temperature (`d(ln T_plume)/d(ln T_IC)` = 0.156) and a colder start builds its corona more
slowly.

So the prediction here is a *measurement*, not a derivation:

* **If `T_e` → ~416 eV and `⟨f_abs⟩` stays near 0.36** — temperature and absorption are
  **separable**. A reduced leg can be put on the right ablation temperature while still
  under-absorbing by ~4×, which localises the deficit to the optical depth alone and makes
  intensity the recommended knob for any leg whose question is about temperature.
* **If `⟨f_abs⟩` rises with it** — they are coupled through the corona the hotter plume
  builds (`C_S ∝ √T`, so a hotter leg extends its absorbing path faster), and intensity
  becomes a genuine regime-recovery knob rather than a temperature-only one.
* **If `⟨f_abs⟩` falls** — the coupling runs the other way (a hotter plume lowers
  `K ∝ T^(−3/2)` faster than it lengthens the path) and no single laser knob recovers both.

## Cost
5000 cells × 500 ppc × 110 592 steps — identical to the parent, **~6 min**.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 | PASS — no electron-sector key moved |
| G2 `dz/lambda_D` (target / ambient) | 58.1 at t=0 | INFO — the IC is unchanged; the *plume* will be hotter, so this improves in the region that matters |
| G3 laser-off control | `P4_lez_kin_ic6_off` | PASS |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
<pending>

## Retracted
nothing
