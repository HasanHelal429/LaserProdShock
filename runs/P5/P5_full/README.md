# P5_full — the ANALYTIC-IC arm of the initial-condition A/B

> **Role changed 2026-08-29.** This was written as the phase spine. The spine is now
> `P5_flashic`, which is this deck with the initial condition **lifted** from FLASH rather
> than fitted to it. `P5_full` is kept and still runs, because the pair is the only
> measurement of what the lift is worth: same mass, same duration, same everything, one
> analytic four-parameter corona against one 26-node table. The audit predicts the analytic
> arm over-absorbs by ~1.8× in optical depth; this is where that prediction gets tested on
> a real run instead of an integral. Read its Question below as the A/B's, not the phase's.

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** Is WarpX's plume `T_e` = 0.69 × FLASH's a *code difference*, or a *stopwatch
artifact* of comparing two codes at a time when neither has reached its asymptote?
**Expected.** If it is a code difference, the ratio `T_e,WarpX(τ)/T_e,FLASH(τ)` is flat at
≈ 0.69 across `τ_own` 0 → 24.26. If it is a rate difference, the ratio rises — FLASH climbs
379 → 953.5 eV over the pulse and a WarpX leg that is merely *slower* will close the gap.
**Falsified by.** A ratio curve that is neither flat nor monotone — that would say the two
codes disagree about the *shape* of the ablation history, not its level, and would move the
question to electron thermal transport (D3 Appendix C, never run).

---

## Why this run exists

`P4_lez_kin_mrreal_drift` produced the project's cleanest cross-code number: a real ion, a
real electron, no similarity transform anywhere, and — unusually — **matched absorption**,
`⟨f_abs⟩` 0.840 against FLASH's asserted 0.870. On that footing WarpX runs **0.69 ×** FLASH's
plume `T_e`, with `ζ_cr` at 1.03 × and `L_n` at 0.81 ×.

That number is quoted **at one time**, `τ_own` 5.39 — a fifth of the way into FLASH's flat
top. Retraction ledger 15 already killed one "the FLASH↔kinetic benchmark passes" for exactly
this reason: *"that agreement is a coincidence of the transient. FLASH is 99.9 % converged
there, WarpX 36–46 %; extrapolated it reads 1.59–2.00 ×."* The 0.69 × is the same kind of
claim, and it has the same exposure.

At µ = 1 the WarpX clock **is** the FLASH clock, so the fix is available and cheap: run the
leg for the whole pulse and replace the single ratio with a ratio-versus-τ curve. Nothing
about the physics changes. This is the run that makes the benchmark falsifiable.

## What changed from the parent, and nothing else did

| | `P4_lez_kin_mrreal_drift` | **this run** | why |
|---|---|---|---|
| `max_step` | 2 030 600 | **9 139 500** | `τ_own` 5.390 → **24.260**, i.e. `t_FLASH` 0.3 → **1.0 ns** |
| `thickness_de` | 192.8263 (4.5 `d_i0`) | **500** (11.67 `d_i0`) | the reservoir — see below |
| `center_de` | −96.41 | **−250** | keeps the interface at `z` = 0 |
| `axis.lo_de` | −214.2514 | **−521.4251** | same 0.5 `d_i0` margin behind a thicker target |
| `axis.hi_de` | 10497.7486 | **10498.5749** | rounds the span to 11020 `d_e` = 22040 cells |
| `max_grid_size` | 21424 | **22040** | must track `n_cell` (the GPU one-box rule) |
| diagnostics | 20/24/… dumps | **45 plotfiles at FLASH's own 0.02 ns cadence** | no time interpolation |
| `random_seed` | unset | **20260829** | so `P5_seed` is a real replicate |

Corona fit, all four temperatures, the corrected `drift_uz_de`, collisions, `cfl`, `ppc`,
`dz`, `density_min_frac` and both boundary conditions are **carried unchanged**.

## The reservoir, which is the reason for the second change

The 10 `n_cr` cap and the paper's 4.5 `d_i0` thickness were set for a run that stops at
0.3 ns. Over 0.9 ns they stop being a detail:

```
target areal n_i at 10 n_cr, 4.5 d_i0 (32.6 um)   =  2.47e22 m^-2
ablated over 0.9 ns at n_cr * C_S(440 eV = 1.425e5 m/s)  =  9.72e21 m^-2
                                        ->  39% of the entire target consumed
```

FLASH's solid holds `3.01e24 m^-2` — **122 ×** more — so it never notices. Extended
unchanged, the back half of this run would be a burn-through problem wearing an ablation
problem's label, and the `T_e` departure that produced would be a reservoir artifact
indistinguishable from the code difference we are trying to measure. At 500 `d_e` the draw is
**15.2 %**.

The extra 307 `d_e` is **1.4 %** of the domain, and all of it sits *behind* the critical
surface where the laser never reaches, so `t = 0` absorption is untouched.

**The thickening is A/B-tested for free.** Over `τ_own` 0 → 5.39 this run and its parent
differ only in target thickness, and the reservoir cannot yet bind there (~9 % drawn). If
they agree over that window, the change is a null and the extension is trustworthy. If they
do not, the reservoir binds earlier than the estimate above — which is itself the finding.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 9139500 steps = 903.4 ps
```

Box headroom: the parent's plume front sat at `ζ` = 14.31 at `τ_own` 5.39 (FLASH 19.62).
Extrapolated to `τ_own` 24.26 that is `ζ` ≈ 64 = 2743 `d_e`, a quarter of the 10499 `d_e` of
vacuum ahead of the target. **The box is not the binding constraint; the reservoir is.**

## Gates (pre-launch, from `make_inputs.py`)

| gate | value | verdict |
|---|---|---|
| G1 `ω_pe·dt` | 0.553 at `t` = 0, **0.783** at 2× compression (limit 1.2) | PASS |
| G2 `dz/λ_D` in the solid | 58.1 | known departure, as every prior leg |
| G4 `ray_cfl` | 0.25 | **WARN** — interior critical surface, ladder still undeclared (D4) |
| G5 ppc / `Tlocalfrac` | 500, mode `local` | PASS |
| G6 energy closure | | post-run |
| G3 laser-off subtraction | `P5_full_off` | must run concurrently |

## Cost

Parent: 2 030 600 steps in **4 h 24 m** on one RTX 4070 (under load 17.2). This is 4.5013 ×
that → **≈ 19.8 h**. Two 4070s exist; `P5_full_off` goes on the other one concurrently.

## Result
*(to be filled in after the run — including what is retracted)*

## Retracted
nothing yet — the run has not been launched.
