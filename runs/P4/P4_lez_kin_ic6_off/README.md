# P4_lez_kin_ic6_off — the G3 laser-off control for `P4_lez_kin_ic6`

**Phase.** 4, `TEST_PLAN.md` §12. Gate **G3**.

**Question.** How much of `P4_lez_kin_ic6`'s electron heating is the **laser**, and how much
is the **grid**?

**Why it matters here more than in any earlier run.** `ic6` ends with `T_e` **still
climbing** (129.8 → 183.8 → 224.6 → 271.2 eV, no plateau, where FLASH is flat by τ ≈ 20)
while `f_abs` is still **0.992**. That is the one combination in which a spurious numerical
heat source is *invisible* in the energy budget: real absorption and grid heating both look
like energy arriving. Earlier in the campaign the control was deferred on the argument that
grid heating **suppresses** absorption, so a high `f_abs` is self-validating — that
reasoning held when `f_abs` was mid-range and **does not hold now.**

**Expected.** A few percent of the driven `T_e` rise. `dz/λ_D` is 253 in the cold solid but
only **1.8 in the underdense plume**, and the plume is where every benchmark quantity is
measured — so the badly-resolved region is a mass reservoir, not the region under study.

**Falsified by.** A control `T_e` rise comparable to the driven one, which would mean the
`ic6` result is substantially numerical and that implicit PIC (`theta_implicit_em`,
~1.9× per step, grid-heating immunity without resolving λ_D) is required before any of it
can be quoted.

**Why not just resolve λ_D.** Cost scales as `f²` — cells and steps both scale with 1/dz —
and the solid needs dz ÷ 253. Reaching even the project's own `dz/λ_D` ≤ 8 gate costs
**×998, about 15 days**; reaching 1 is 931 days. Measuring the effect is 21 minutes.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 552960 steps = 54.66 ps
```

## Setup
**`laser.intensity: 0.0`, and nothing else** — verified by deck diff against
`inputs_P4_lez_kin_ic6`, which differs in exactly one line. Grid heating accumulates with
step count and depends on the grid, the ppc and the species, so any other difference makes
the G3 subtraction meaningless.

## Cost
5000 cells × 500 ppc × 552 960 steps, **~21 min** on one RTX 4070 (the physics run's time;
the control is if anything cheaper with no ray march).

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` | 0.783 | PASS |
| G2 `dz/lambda_D` solid / plume | 253 / **1.8** | INFO |
| G3 | **this run IS the control** | — |
| G5 ppc | 500 | PASS |

## Result
_Pending._

## Retracted
Nothing yet.
