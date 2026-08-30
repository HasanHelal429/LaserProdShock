# Phase 5 — the FLASH benchmark, done on the terms P4 established

Phase 4 ended with the project's cleanest cross-code number and two structural problems
underneath it. Phase 5 exists to fix the terms of the comparison, not to add physics.

**The framing change.** PSC is a *conduit for PIC physics*, not the benchmark. It is another
PIC code, and Phase 4 disqualified it as a reference three separate ways: its RMR knob is an
**electron-mass** knob (`T_e ∝ m_e^(−0.187)`, so RMR = 100 is not converged), its `f_abs`
diagnostic is documented valid only for **sub-critical** profiles while this target is
overdense, and its legs are not τ-matched to anything. It stays in `xcode_matrix.py` as a
PIC-class cross-check with those caveats attached. **FLASH is the benchmark.** Every
acceptance criterion in this phase is against FLASH.

**The consequence.** A benchmark is only as good as its anchor, so Phase 5 audits FLASH as
hard as it audits WarpX. Two of the three findings below are about FLASH.

---

## What the pre-launch audit already found

Both of these came out of analysis only — no simulation — and both change what is worth
running. Full derivation in `RESULTS.md` (2026-08-29).

### 1. The "matched absorption" claim does not survive its own convention

`DELIVERY.md`'s 87.04 % is a **whole-run** figure, 0 → 1 ns, and it reproduces exactly. The
PIC legs never simulate 0 → 0.1 ns; they start at the handoff and integrate from there. On
the **same window** (`scripts/flash_absorption.py`):

| window | FLASH `⟨f_abs⟩` |
|---|---|
| 0.0 → 0.1 ns (the ramp, which no PIC leg runs) | 0.4156 |
| **0.1 → 0.3 ns — `mrreal_drift`'s window** | **0.6823** |
| 0.1 → 1.0 ns — `P5_full`'s window | 0.8960 |
| 0.0 → 1.0 ns — the `DELIVERY.md` basis | 0.8704 |

`mrreal_drift` absorbs `⟨f_abs⟩` = 0.8402. So WarpX absorbs **1.23 × more** than FLASH over
the matched window, not 3.4 % less. The pair was never matched. Correcting onto FLASH's
absorption through Manheimer's `f_abs^(2/3)` multiplies WarpX's `T_e` by 0.871:
**440.2 → 383 eV against FLASH's 647, i.e. 0.59 ×, not 0.69 ×.**

### 2. Half of that excess is FLASH's grid, not WarpX's error

Integrating the *same* IB kernel along both profiles at the handoff
(`scripts/ic_optical_depth.py`) gives `τ_WarpX/τ_FLASH` = **3.04**, which decomposes:

| | factor | what it is |
|---|---|---|
| FLASH's own grid vs. its profile resampled to `dz` = 0.0847 µm | **1.69 ×** | FLASH's `dx_min` is **0.781 µm** and it has **no cells at all** in `0.9 < n/n_cr < 1`. The near-critical layer, where the IB kernel diverges as `(1−n̂)^(−1/2)`, is **structurally absent** from FLASH's absorption. |
| the fitted exponential corona vs. FLASH's actual profile, at matched resolution | **1.80 ×** | ours is genuinely the more absorbing shape. `rms(ln n)` = 0.107 on the fit, and IB goes as `n²`. |

**Both are real and they push the same way.** Roughly half the absorption discrepancy is
physics FLASH is *missing* at 0.781 µm, and half is fidelity our initial condition is
*lacking*. Neither is a defect of the deposition operator, which remains cleared.

This is the first result in the project that says the anchor itself needs checking, and it
is why F1 below outranks every WarpX run in the plan.

---

## The runs

**All twelve run on Perlmutter** — see `perlmutter/README.md`. Single-GPU array tasks, so
the wall clock is the longest single leg rather than the sum.

| ID | what | ~cost (A100) | order |
|---|---|---|---|
| `P5_raycfl_{050,025,010,005}` | the G4 march-convergence ladder, 2 ps each | minutes | **1 — gates the phase** |
| `P5_seed` | seed replicate of the spine over 0.3 ns; the error band | ~1.5 h | 2 |
| **`P5_flashic`** | **the spine**: real mass, whole 1 ns pulse, **IC lifted from FLASH** | 8–13 h | 2 |
| `P5_flashic_off` | its G3 laser-off control | < spine | 2 |
| `P5_full` | the same deck with the **analytic** IC — the A/B for the lift itself | 8–13 h | 2 |
| `P5_flashic_t02`, `_t04` | handoff-time ladder: does the evolution remember its IC? | 7 / 5 h | 3 |
| `P5_flashic_n20` | density cap 10 → 20 `n_cr` | 8–13 h | 4 — after the spine |

And two asks of the FLASH collaborator, **seconds of compute each** (the no-rad run is
38 s), which outrank everything above on value per cost:

| ID | what | why |
|---|---|---|
| **F1** | rerun radiation-OFF at `lrefine_max` **5 and 6** (`dx_min` 0.39 / 0.20 µm) | Finding 2. Does FLASH's absorbed fraction **rise** when it resolves the critical layer? If it does, part of the "code difference" is a FLASH resolution artifact and the anchor moves. |
| **F2** | rerun at `diff_eleFlCoef` **0.03** and **0.12** (the deck runs the paper's 0.06) | The Larsen flux limiter sets the coronal scale length — what our IC is lifted from and what sets the absorbing path. If `L_n` moves more than the 0.81× we report against, FLASH's own calibration is inside our error bar. |

## Decision register

Status key: **[SET]** configured as shown · **[OPEN]** needs your call.

**D1 — PSC's status. [SET]** Demoted to a PIC-class cross-check. No new PSC runs. It stays
in `xcode_matrix.py` with its three disqualifications printed beside it. *Cost of being
wrong:* none that is not recoverable — the PSC data is on disk and the matrix still renders it.

**D2 — the target thickening. [SET, and A/B-tested for free]** `thickness_de` 192.83 → 500.
At 4.5 `d_i0` and the 10 `n_cr` cap the target holds 2.47e22 ion/m² and steady ablation
removes 9.72e21 over 0.9 ns — **39 % of it**. FLASH's solid holds 122 × more and never
notices. At 500 `d_e` the draw is 15.2 %, and the extra 307 `d_e` is 1.4 % of the domain,
all of it behind the critical surface where the laser never reaches. Over `τ_own` 0–5.39
`P5_full` and `P4_lez_kin_mrreal_drift` differ **only** in this, so the change validates
itself. *Cost of being wrong:* the back half of a 20 h run is a burn-through problem
mislabelled as an ablation problem.

**D3 — the comparison observable. [SET]** A ratio-versus-τ **curve**, not a single-time
ratio, on the five quantities FLASH can adjudicate: plume `T_e`, `ζ_cr`, `L_n`, plume front,
and `v` at 0.1 `n_cr`. Retraction ledger 15 killed one "benchmark passes" for being a
single-time claim on an unconverged transient; the 0.69 × was the same claim. `P5_full`
dumps on FLASH's own 0.02 ns cadence so no time interpolation enters.

**D4 — `ray_cfl`. [OPEN]** The G4 warning is still live and inherited: `ray_cfl` = 0.25 is
not asymptotic for turning-point problems, and every P5 leg has an interior critical surface
at 10 `n_cr`. The ladder (0.05/0.10/0.25/0.50 at **this** target density) has been "TO BE
RUN" since P4 and is *more* load-bearing now that Finding 2 puts 41 % of the fitted IC's
optical depth in `0.9 < n̂ < 1`, right at the turning point. **Recommend running it before
`P5_full`** — it is four short runs, not four long ones.

**D5 — the initial condition. [SET: lifted, and its sensitivity measured]** Option (b),
built. `corona_profile: flash_table` replaces the four-parameter analytic exponential with a
node table lifted straight from a FLASH plotfile, and **all four handoff profiles** go —
`n_e`, `T_e`, `T_i`, `v_z` — not just the density. Measured on the *rendered deck*, by
evaluating its own parser strings against FLASH:

| | analytic exponential | lifted table |
|---|---|---|
| `rms(ln n)` vs FLASH | 0.107 | **0.0032** (26 nodes) |
| `T_e` relative rms | *isothermal* | **0.0030** |
| optical depth vs FLASH, same grid | **1.798** | **1.0038** |

**The 1.80× is gone.** Three assumptions go with it: the exponential *form*, the isothermal
corona (`K ∝ T^(−3/2)` makes that an absorption knob), and the two-parameter velocity ramp
whose scaling families cost a 4.05× error in `L_n` once already — a lifted profile has no
scaling families to get wrong.

*Architecture.* `scripts/flash_ic_fit.py` reads FLASH **once** and writes `ic_flash.yaml`
(tracked, diffable); `deck.py` renders it as a **ramp sum**, `f = f₀ + Σ dmₖ·max(0, z/dₑ −
zₖ)`, flat rather than nested, with a closing term so it goes flat outside the fitted span
instead of extrapolating off a cliff. So `config.yaml` stays the single source of truth, the
deck stays a pure function of it, and **nothing downstream needs h5py or the FLASH mount** —
which is what makes the Perlmutter move clean.

*Kept departures*, both in the table's `clamp` block and both reported by the fitter: the
10 `n_cr` cap (46.6 % of cells) and a `T_e` floor where FLASH's cold solid is
Debye-unresolvable (45.6 %). Both are the solid.

*Inert keys.* `thickness_de`, `scale_length_de`, `corona_density_over_ncr`,
`corona_offset_de`, `theta_e_init`, `theta_i_init` and `drift_uz_de` now shape nothing. They
are deleted from the lifted configs rather than left in place, and `make_inputs.py` prints a
NOTE if any reappear.

*One unit trap, caught by a guard.* `xcode_compare.flash_series` returns velocity normalised
to `C_S0`, not `c`. Written into a field the deck renders as `u = γv/c`, that overstates the
drift by `c/C_S0` = 1533× — a **4.01 c** initial condition, measured before the conversion
existed. `flash_ic_fit.py` now converts once, at the only place that knows both units, and
**refuses to write a table with |v|/c > 0.2**. Nothing downstream could have flagged it: 0.5
is a plausible `v/C_S0` and an implausible `v/c`.

**The sensitivity study.** FLASH ran the whole 1 ns, so it can seed a PIC leg at any time.
`P5_flashic_t02` and `_t04` hand off at 0.2 and 0.4 ns and end at 1.0 ns like the spine, so
the three rungs share a window and are directly overlayable. **Collapse → the evolution has
forgotten the handoff and the benchmark compares physics. Separation → it substantially
compares initial conditions, and running longer does not fix that.** Prior evidence is
narrow and optimistic: `d(ln T_plume)/d(ln T_IC)` = 0.156 (`HANDOFF.md` §7.4) — but that was
one knob, on a reduced-mass leg, with an analytic IC.

**D6 — run order. [OPEN]** Recommended: send **F1 and F2 to the collaborator today** (they
cost seconds and can invalidate the anchor), launch `P5_full` + `P5_full_off` on the two
GPUs concurrently, and hold `P5_full_n20` until `P5_full` has reported — Finding 2 raises it
from a reservoir test to a **critical-surface-gradient** test, and its predicted direction
(higher cap → steeper gradient → *less* absorption, toward FLASH) is now a real hypothesis
rather than a fishing expedition.

---

## Acceptance

Phase 5 succeeds if it can say, with a band, **which of these is true**:

1. the ratio curve is flat → a genuine code difference, and the number is quotable;
2. the ratio curve rises → the 0.69 × was a stopwatch artifact and the codes converge;
3. the ratio moves when FLASH's resolution or flux limiter moves → the benchmark's anchor
   was inside our error bar all along, and that is the finding.

A negative result stated quantitatively is a result (`CLAUDE.md`). Outcome 3 is the one
nobody has looked for, and the audit above says it is live.
