# P4_lez_kin_flashic_ct — FLASH-IC kinetic leg at m_i/m_e = 100, corona temperature consistent

**Phase.** 4, `TEST_PLAN.md` §12; decisions **D1** (initial condition) and **D5** (`n_max`).

**Question.** `P4_lez_kin_flashic` absorbed only **`f_abs` = 0.358** against FLASH's 0.870
and the analytic leg's 0.769, and its plume settled at **0.54×** its own Manheimer value —
the only Phase-4 leg not sitting near 1.0. Is that a **mixed-unit initial condition**
rather than a limit of the reduced mass ratio?

**Expected.** `f_abs` recovers to **0.7–0.8** and plume `T_e`/own-`T_e,SS` (now **104 eV**) to **≈ 1**,
*while keeping* the exponential corona and the compact critical surface the parent run was
built for. If so this leg should beat the analytic leg on `ζ_front` and `L_n`, because it
has both the right corona shape and the right energetics for the first time.

**Falsified by.** `f_abs` staying near 0.36 — which would mean the deficit is not the
corona temperature and the D1 entry's structural claim survives after all. Also falsified,
differently, by `f_abs` → 1.0 and staying there: that would say the self-limiting
`κ ∝ T^(−3/2)` picture does not hold at this corona.

**Parent.** `P4_lez_kin_flashic`, preserved unmodified.

> **THE ION MASS CHANGED TOO (2026-08-18).** This run was first built as a
> single-variable change to the parent (corona temperature only, at the inherited
> `mass_ratio` = 2698) and launched twice in that form. It was then rebuilt at
> **`mass_ratio` = 100** — the **ion**-to-electron ratio, not the proton's. The paper
> (§II.B) says *"we use a mass ratio of m_p/m_e = 100"*, which for aluminium gives
> 26.98 × 100 = 2698 mₑ, and that is what every earlier Phase-4 leg ran. But the paper
> reaches its reduction with a **reduced speed of light** (`m_e c²` = 60 keV against the
> real 511 keV), which WarpX cannot follow — it has real `c` and real `mₑ`. Running the
> ion at 100 mₑ directly is this project's choice, and it is **not** comparable to the
> existing legs without redoing them.
>
> One thing improves for free: the deck's `d_i = d_e√(mass_ratio)` = **10 `d_e`** now
> coincides with the comparison's `d_i0`, where at 2698 the deck said 51.94 `d_e` and the
> comparison used 10. That is `TEST_PLAN.md` §12.2's "two different `d_i0`" trap, closed.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
       #####~                                                           
      ^                                                                ^
      reflecting                                                    open
      z = -224                                                  z = +2464

  #  target flat top : 40 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5376 cells, dz = 0.5 d_e, dt = 0.07061 fs, 774144 steps = 54.66 ps
```

## Setup — what differs from the parent, and why

| | `P4_lez_kin_flashic` | **this run** |
|---|---|---|
| `mass_ratio` (m_Al/mₑ) | 2698 | **100** |
| µ vs real aluminium | 18.36 | **495.4** |
| own `T_e,SS` | 312 eV | **104 eV** |
| `theta_e_init` (corona `T_e`) | 7.4032e-4 = **378.3 eV** | **9.3560e-5 = 47.81 eV** |
| `theta_i_init` (corona `T_i`) | 2.2622e-4 = **115.6 eV** | **2.8590e-5 = 14.61 eV** |
| `drift_uz_de` | [1.5271e-3, 1.5593e-4] | **[7.9294e-3, 8.1002e-5]** |
| `max_step` | 774 144 (54.66 ps) | **149 184 (10.53 ps)** |
| everything else | — | **identical** |

Every one of those follows from the ion mass. `T` scales as µ^(−1/3) = 0.1264;
`C_S0 = √(Z kT_e0/m_i)` is 5.194× faster so the drift in `u = γv/c` rises with it;
`d_i0` falls 51.94 → 10 `d_e`; and the τ unit `d_i0/C_S0` goes 2.0277 → 0.39037 ps, so
**the same τ = 27 costs 5.2× fewer steps — not 27×**, because `d_i0` shrinks along with
`C_S0` and the two partly cancel. `T_e/T_i` = 3.27 is dimensionless and is preserved.

The parent's IC transferred **three of four** quantities in similarity units and one in
absolute units:

| IC element | transferred as | consistent? |
|---|---|---|
| corona shape, `L_n` = 6.955 `d_e` | FLASH `ζ` × 10 — normalised | yes |
| corona anchor `n_cr`, offset 2.31 `d_e` | `n_e/n_cr` | yes |
| drift `v/C_S0` = 0.548 + 0.05598 `ζ` | normalised to WarpX's `C_S0` | yes |
| corona `T_e`, `T_i` | **absolute eV, straight from FLASH** | **no** |

`T_e,SS = 5.94 µ^(1/3) Z^(−1/3) λ^(4/3) I^(2/3)` carries **µ^(1/3)**, and µ here is
18.363× smaller than real aluminium, so FLASH's 378.3 eV corona corresponds to
**378.3 / 18.363^(1/3) = 143.4 eV**. Setting it 2.638× too hot suppresses inverse
bremsstrahlung by **2.638^1.5 = 4.29×**, which is the size of the parent's absorption
deficit. `T_e/T_i` = 3.27 is dimensionless and transfers unchanged.

`theta_e_solid` = 20 eV is **deliberately not rescaled**: it was never a fit to FLASH
(FLASH's solid is 0.138 eV) but a numerical floor chosen so the solid does not Debye-heat
faster than the laser heats it. It stays a known departure, as in the parent.

## Cost
5376 cells × 500 ppc × 774 144 steps. Parent measured **1 h 27 m** on one RTX 4070 at
0.0068 s/step (`progress.log`), and this run is identical in size, so the same estimate
holds. The `_off` control costs the same again.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 1.199 at 2.3× compression | PASS |
| G2 `dz/lambda_D` (target / ambient) | **326.9**, against the parent's 116.2 | INFO — see below |
| G3 laser-off control | **not run up front** — see below | deferred |
| G4 `ray_cfl` check | 0.25, interior critical surface present | WARN, as parent |
| G5 ppc / `Tlocalfrac` | 500 | PASS |
| G6 energy closure | | post-run |

**G2 is the cost of this correction, and it is now the main numerical worry.** `λ_D ∝ √T`,
so a corona 7.91× cooler is √7.91 = 2.81× less Debye-resolved: 116.2 → **326.9**. That is
approaching the ~250× that `CLAUDE.md` records as the unavoidable cold-target case, and it
is worse than any earlier Phase-4 leg.

**The mitigating factor is that this run is 5.2× shorter in steps** (149 184 against
774 144), and grid heating accumulates with step count — so the *integrated* heating need
not be worse than the parent's even though the per-step rate is. That is an argument, not
a measurement, and it is the thing the G3 control would settle.

**The G3 control is deliberately deferred, and the asymmetry is why.** Grid heating warms
the corona, and `κ_ib ∝ T^(−3/2)`, so it **suppresses** absorption — the same direction as
the defect this run exists to remove. So the two outcomes are not symmetric:

- **`f_abs` comes back high (0.7–0.8, the expectation):** self-validating. Grid heating
  could only have pushed it *down*, so a high value cannot be a grid-heating artifact and
  the control would add nothing.
- **`f_abs` comes back low:** the one branch where a real absorption deficit and grid
  heating are not distinguishable, and the control becomes necessary. Run it then.

Regenerate the control if that branch is reached: copy this config, set
`laser.intensity: 0.0`, add `controls.physics_run: P4_lez_kin_flashic_ct`. (The parent
declared a control and never ran one either.)

## Result
_Pending._

## Retracted
Nothing yet.
