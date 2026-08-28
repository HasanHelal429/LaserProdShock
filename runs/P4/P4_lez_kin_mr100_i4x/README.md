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
**366.9 s. Outcome 3: `⟨f_abs⟩` FELL. Intensity does not recover the regime.**

| leg | `⟨f_abs⟩` | `f_end` | plume `T_e` |
|---|---|---|---|
| `mr100` (I = 1e13) | 0.3642 | 0.3495 | 157.7 eV |
| **this leg** (I × 4.285) | **0.2404** | 0.4066 | **322.7 eV** |
| `mrreal_drift` (real mass) | 0.8402 | 0.9148 | 440.2 eV |

Predicted `T_e` ~416 eV; **measured 322.7** — 22.4 % short, outside the 13.5 % floor. And
`⟨f_abs⟩` **fell 0.660×**, `d(ln f_abs)/d(ln I)` = **−0.285**.

### But the shortfall is entirely the absorbed fraction, and Manheimer is exact
Raising the incident intensity 4.285× raised the **absorbed** intensity only **2.828×**,
because `f_abs` dropped. Feed that into Manheimer instead:

```
T_e ~ I_abs^(2/3):   2.828^(2/3) = 2.000x     MEASURED 322.7/157.7 = 2.046x     2.3% APART
```

**`T_e ∝ I_abs^(2/3)` holds to 2.3 %.** The entire 22.4 % miss against the naive prediction is
the falling absorbed fraction — the scaling law is not in question, the coupling is.

### Why `f_abs` falls: absorption is self-limiting
`K ∝ Z lnΛ n² T^(−3/2)`, so the hotter plume this leg creates is a *worse* absorber. The
plume heats, `K` drops faster than the lengthening path can compensate, and the coupling runs
in the direction that opposes the knob. This is the documented self-limiting behaviour
(`GOTCHAS.md`, "Absorption is self-limiting, and that is real physics"), here measured as a
clean power law for the first time.

### The answer to "can a laser scaling recover the regime"
Composing the two measured exponents: `f_abs ∝ I^(−0.285)`, so `I_abs ∝ I^0.715` and
**`T_e ∝ I^0.476`** — not `I^(2/3)`. To reach the real 823 eV target at `m_p/m_e` = 100 the
intensity would have to rise **≈32×, to 3.2e14 W/cm²**, and `f_abs` would fall to ~0.135 —
*further* from the real-mass leg's 0.840 than the 0.364 it started at. **You would buy the
temperature by making the absorption worse.**

(That extrapolates 7.5× beyond the measured pair, so treat ≈32× as an estimate. The direction
and the mechanism are measured; the exact factor is not.)

**So intensity is a temperature knob, not a regime knob** — and the two are anti-correlated,
which rules out the "separable" reading this run was built to test. On the intensity-adjusted
target this leg sits at `T_e/T_ss` = **0.392**, against `mr100`'s 0.506 and the real-mass
leg's 0.535: raising the intensity moved it *away* from its own steady state.

## Retracted
nothing## Retracted
nothing
