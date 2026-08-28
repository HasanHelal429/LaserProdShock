# P4_lez_kin_mr100_lam4x_i — wavelength + intensity — the last untested laser repair

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** `λ × µ^(−1/2)` restores `d_i0` to the real 7.256 µm and `I × µ^(1/2)` holds `T_ss` at the real 823 eV. Does the absorption regime come with them?
**Expected.** Plume `T_e` near the real-mass leg's 440.2 eV if `T_ss` governs. `⟨f_abs⟩` is the open question.
**Falsified by.** Nothing about the *temperature* — this is a measurement of the absorption
response, and all three signs are informative. A `⟨f_abs⟩` outside 0.05–0.99 would mean the
leg saturated or went transparent and the exponent cannot be read from it.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.7256 um

                                                               <== laser
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.4236 fs, 110592 steps = 46.84 ps
```

## Setup
Parent: **`P4_lez_kin_mr100`**. Keys that move:

| key | parent | **here** |
|---|---|---|
| `laser.wavelength_um` | 1.064 | **4.5593** (= 1.064 × µ^(−1/2)) |
| `laser.intensity` | 1.0e17 W/m² | **2.334e16 W/m² = 2.334e12 W/cm²** = 1e13 × µ^(1/2) |

**Why the length primaries do not move.** The config quotes every length in `d_e = λ/2π`, so
raising λ by 4.285 raises `d_e` 0.1693 → **0.7256 µm** and every length becomes 4.285× larger
in metres while its config number stays put. `d_i0` → the **real 7.256 µm**; the 45 `d_e`
target → **32.65 µm**, which is the paper's 4.5 real `d_i0`. The reduced ion is untouched.

**This knob is numerically free, and that is checked, not assumed:**

| | parent | here | |
|---|---|---|---|
| `dz` | 8.467e-08 m | 3.628e-07 m | ×4.285 |
| `dt` | 0.09885 fs | 0.42358 fs | ×4.285 |
| `n_cell` | 5000 | 5000 | unchanged |
| `max_step` | 110592 | 110592 | unchanged (`τ_own ∝ λ` too) |
| `t_end` | 10.93 ps | 46.85 ps | ×4.285 |
| **`ω_pe·dt`** | 0.7826 | **0.7826** | **invariant** |
| **`dz/λ_D`** | 58.11 | **58.11** | **invariant** |

`ω_pe ∝ √n_cr ∝ λ^(−1)` while `dt ∝ λ`, and `λ_D ∝ √T/√n ∝ λ` while `dz ∝ λ`. Both gates
cancel exactly. The deck's key set is identical to the parent's — verified by diff.

**What it costs:** `n_cr ∝ λ^(−2)` falls 18.4× to 5.36e25 m⁻³. Densities in `n_cr` are
unchanged, but in absolute terms this is no longer the paper's 1.064 µm problem. Acceptable
if the question is ablation physics; not if the question is this benchmark.

## Why the prediction is weak
The static estimate says `τ_abs ∝ λ^(−1)`, i.e. absorption gets **worse** by 4.285×, and with
the hotter plume's `T^(−3/2)` a further 4.285× — 18× worse in total. **That estimate is known
to be unreliable here:** evaluated across the mass sweep with each leg's own plume `T_e` it
predicts `µ^0.017` against a measured `µ^0.490`. `mr100_sim` and `mr100_i4x` both showed the
governing physics is dynamic, not static. So the static number is a prior to be tested, not a
prediction to be trusted — which is why the λ-only leg exists.

## Cost
5000 cells × 500 ppc × 110 592 steps — identical to the parent, **~6 min**.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.7826 | PASS — invariant under λ |
| G2 `dz/lambda_D` (target / ambient) | 58.11 | INFO — invariant under λ |
| G3 laser-off control | `P4_lez_kin_ic6_off` | at the parent's λ; see note |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

G3 note: the control runs at 1.064 µm and 10.93 ps against this leg's 46.85 ps. Grid heating
accumulates with step count, and the step count is unchanged, so it remains a reasonable
bound — but an energy-closure claim from this leg would need its own `_off` twin.

## Result
**The worst of the four probes. `⟨f_abs⟩` = 0.1210, plume `T_e` = 50.2 eV.**

| leg | λ | I (W/cm²) | `⟨f_abs⟩` | plume `T_e` | absorbed |
|---|---|---|---|---|---|
| `mr100` | 1.064 µm | 1e13 | 0.3642 | 157.7 eV | 3.64e12 |
| `mr100_i4x` | 1.064 µm | 4.285e13 | 0.2404 | 322.7 eV | 1.03e13 |
| `mr100_lam4x` | 4.559 µm | 1e13 | 0.0754 | 121.2 eV | 7.54e11 |
| **this leg** | 4.559 µm | 2.334e12 | **0.1210** | **50.2 eV** | **2.82e11** |
| `mrreal_drift` | 1.064 µm | 1e13 | 0.8402 | 440.2 eV | — |

It absorbs **12.9× less power than `mr100`** and runs **8.8× cooler than the real-mass leg**,
while the combination was designed to restore `d_i0` *and* `T_ss` to their real values. It
does restore both — and the plume does not care, because the laser is barely coupling.

The `⟨f_abs⟩` being *higher* than the λ-only leg's 0.0754 is the intensity exponent working as
measured: dropping `I` by 4.285× raises `f_abs` by `4.285^0.285` = 1.53×, and 0.0754 × 1.53 =
0.115 against 0.1210 measured — **5 % agreement**, a clean consistency check on
`d(ln f_abs)/d(ln I)` = −0.285 from `P4_lez_kin_mr100_i4x`.

### Verdict
**The last laser repair is closed.** Restoring the geometry costs the absorption, and no
intensity compensation buys it back — the two knobs pull the same quantity in opposite
directions and neither is strong enough.

## Retracted
nothing
