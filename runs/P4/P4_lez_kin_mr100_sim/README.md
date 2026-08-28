# P4_lez_kin_mr100_sim — the similarity branch of the handoff, run cleanly for the first time

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** `HANDOFF.md` §7.4 says the optical-depth failure (`τ_abs ∝ µ^0.490` where the
similarity transform promises `µ⁰`) is caused entirely by pinning the handoff temperature in
raw eV while the lengths transfer in similarity units. Scale the temperature too and it should
disappear. Does it?
**Expected.** `⟨f_abs⟩` **0.364 → ~0.86**, landing on the real-mass leg's 0.840. `K ∝ T^(−3/2)`,
so lowering the corona from 378.3 to 143.4 eV raises `K` by 2.638^1.5 = **4.285×** at unchanged
path length, taking `τ_abs` 0.226 → 0.970. Plume `T_e` ≈ 167 eV if `T_e/T_ss` holds at the
real-mass leg's 0.535.
**Falsified by.** `⟨f_abs⟩` staying near 0.364, or landing anywhere well short of ~0.86. That
would mean the raw-eV handoff is *not* the whole explanation for `µ^0.490` and something else
in the transform is broken.

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
Parent: **`P4_lez_kin_mr100`**. Two keys move, and the generated deck differs in exactly two
constants — verified by diffing `my_constants` against the parent:

| key | parent (raw-eV branch) | **here (similarity branch)** |
|---|---|---|
| `theta_e_init` | 7.4032e-4 = 378.3 eV | **2.8062e-4 = 143.4 eV** |
| `theta_i_init` | 2.2622e-4 = 115.6 eV | **8.5749e-5 = 43.8 eV** |

Both are the parent's value × `µ^(1/3)` = 0.37905, so `T_e/T_i` = 3.27 is preserved. Lengths,
times, drift, `dz`, `dt`, `cfl`, `ppc` and every laser and collision key are untouched — the
mass ratio itself does not change, so this isolates the handoff convention alone.

**Why the solid floor is not scaled.** `theta_e_solid` = 1.26 eV stays. It is a numerical
device (FLASH's real solid is 290 K = 0.025 eV, Debye-unresolvable on a uniform grid), not a
transferred physical state, and the overdense solid does not absorb. Scaling it would push it
further below the floor without touching the quantity under test.

## Why this has never been run
Neither branch of the fork has ever been executed cleanly:

| | lengths | temperature | velocity |
|---|---|---|---|
| the µ-sweep (`mr25`…`mrreal`) | scaled `s¹` ✓ | **raw eV** ✗ | fixed ✗ → corrected 2026-08-28 |
| `flashic_ct` / `flashic_res` | **not scaled** ✗ (5.19× corona) | scaled `µ^(1/3)` ✓ | `uza` scaled `1/s` ✓ |
| **this run** | scaled ✓ | **scaled ✓** | correct ✓ |

`flashic_ct` is the closest existing attempt and is the mirror-image mistake: it scaled the
temperature and the drift when `mass_ratio` went 2698 → 100, and left every length alone. Its
diagnostics were deleted on 2026-08-28 (see `runs/P4/SUPERSEDED.md`); its absolute numbers were
already retracted for the 5.19× corona, so nothing usable was lost.

## Cost
5000 cells × 500 ppc × 110 592 steps — identical to the parent, **~6 min** measured (345 s on
one RTX 4070, more under contention).

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 | PASS — unchanged, no electron-sector key moved |
| G2 `dz/lambda_D` (target / ambient) | rises ~1.6× vs the parent | INFO — `λ_D ∝ √T` and T falls 2.638× |
| G3 laser-off control | `P4_lez_kin_ic6_off` | PASS |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

G2 note: this is the one gate the change touches. A 2.638× colder corona has a `√2.638` = 1.62×
smaller Debye length at fixed density, so `dz/λ_D` goes 58.1 → ~94 in the target. Still an
INFO-level measurement on this project's uniform grid, but worth quoting beside the result.

## Result
<pending — not launched>

## Retracted
nothing
