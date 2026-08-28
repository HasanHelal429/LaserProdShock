# P4_lez_kin_mrreal_drift — the real mass ratio, with the IC corona drift corrected

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Same as `P4_lez_kin_mrreal`: what does the reduced ion mass ratio cost? That leg
answered it with a starting corona 4.29× too fast in its own `C_S0`. This one repeats it with
the drift rescaled.
**Expected.** Plume `T_e` **below** the parent's 464.3 eV — the parent's extra initial flow
inflated the plume extent (`L_n` 4.05× FLASH, `zeta_front` 2.81× FLASH, both anomalous against
`mr100` *and* FLASH). If `µ^(1/3)` still holds, ~416 eV.
**Falsified by.** `T_e` unchanged from 464.3 eV, which would mean the drift is not what drove
the parent's extended plume and something else is.

## Setup
Parent: **`P4_lez_kin_mrreal`**. One key moves:

| key | parent | here | why |
|---|---|---|---|
| `plasma.target.drift_uz_de` | `[1.5271e-3, 1.5593e-4]` | **`[3.5638e-4, 8.4922e-6]`** | `uza` is a velocity in `c`, so it scales as `1/s`; `uzb`'s ramp is *per `d_e`* while the flow is per `d_i0`, so it scales as `1/s²` |

**The defect this fixes.** The mass-ratio recipe (`mr25/mr100/mr400` READMEs) lists
`drift_uz_de` under *held fixed by design*, and `mrreal` followed it. But the recipe's two
families are `s¹` for `d_e`-quoted lengths and `s²` for times and step counts — a **velocity**
belongs to neither, and holding it fixed while `C_S0` falls by `s` leaves the corona `s` times
too fast in normalised units. Measured at the handoff (`tau` 2.7), `v` at `n_e = 0.1 n_cr`:

| | FLASH | `mr100` | `mrreal` |
|---|---|---|---|
| `v/C_S0` at 0.1 `n_cr` | 1.722 | 1.748 ✓ | **21.060** ✗ |
| `uza/C_S0` | 0.548 | 0.548 ✓ | **2.349** ✗ |

`mr100` matches FLASH because `1.5271e-3` was chosen against *its* `C_S0`; every other leg of
the sweep inherits the same error in proportion to `s`. `mr25` and `mr400` are affected too
(by `0.5` and `2.0`), which is worth re-checking before their numbers are quoted again.

## Cost
Identical to the parent: 21424 cells × 500 ppc × 2030600 steps, **~3 h 35 m** measured.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 | PASS |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO |
| G3 laser-off control | none at this mass ratio | **NOT VALID** — as the parent |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
**2030600/2030600 steps, 15 830 s = 4 h 24 m** (one RTX 4070; slower than the parent's 3 h 35 m
only because the machine carried other load, 17.2 vs 0.4). Clean, 5 dumps, no `.old.`.

**Plume `T_e` = 440.2 eV**, `⟨f_abs⟩` = **0.8402** (`f_end` 0.9148), 17 cells, `tau_own` 5.390.

### The notch is gone and the geometry lands on FLASH
At `tau` = 8.0, each leg as a ratio to FLASH:

| | FLASH | **this leg** | parent (IC bad) | `mr100` |
|---|---|---|---|---|
| `zeta_cr` | 1.289 | **1.324 (1.03×)** | 0.538 (0.42×) | 0.253 (0.20×) |
| `L_n` | 4.423 | **3.604 (0.81×)** | 17.895 (4.05×) | 4.485 (1.01×) |
| `zeta_front` | 19.623 | **14.310 (0.73×)** | 55.231 (2.81×) | 16.083 (0.82×) |
| `v_band_max` | 4.045 | **2.676 (0.66×)** | 10.144 (2.51×) | 2.832 (0.70×) |
| `Te_mean_plume` | 646.3 | **445.7 (0.69×)** | 491.1 (0.76×) | 165.1 (0.26×) |

**The critical surface now sits within 3 % of FLASH's** and the scale length within 20 %, where
the parent had them at 0.42× and 4.05×. That is the fix working.

### What the IC error was actually worth
`T_e` moved only **1.055×** (464.3 → 440.2) — the temperature was fairly robust to it. What it
wrecked was the *geometry* (`L_n` 4.05× → 0.81×) and the *absorption* (`⟨f_abs⟩` 0.6233 →
0.8402, because a slower corona stays dense near the target and absorbs more).

### Against `µ^(1/3)`
`µ^(1/3)` from `mr100` predicts **416.1 eV**; measured **440.2** — **5.8 % apart on a 13.5 %
floor**, better than the parent's 11.6 %. The similarity scaling holds to real mass.

### Raw eV, no normalisation, all on a real Al ion

| code | plume `T_e` | `⟨f_abs⟩` |
|---|---|---|
| FLASH | 647.0 eV | 0.870 |
| PSC `run_ourflash_511keV` | 508.8 eV | 0.5833 |
| **WarpX, this leg** | **440.2 eV** | **0.8402** |

**WarpX's absorbed fraction is now within 3.4 % of FLASH's**, so WarpX↔FLASH is very nearly a
matched-`f_abs` comparison with no correction needed: **WarpX runs 0.69× FLASH's plume `T_e`**
(0.705× after the small `f_abs^(2/3)` adjustment). Against PSC, 0.865 in raw eV — but PSC's
`f_abs` is 0.583, so that pair is *not* matched and the 13.5 % should not be read as agreement.

### One thing to be aware of
Panel (b) of the figure shows WarpX's `T_e` climbing to 4–8 × `T_e,SS` beyond ζ ≈ 8, where
FLASH stays flat near 0.8. That is the tenuous outer plume, below the 0.05 `n_cr` band the
scalar is measured over, and it is the known resolved-dynamic-range artifact (RESULTS
2026-08-18, the density-floor entry) — not a new finding. The dense plume, which is what
`Te_mean_plume` reports, tracks FLASH.

## Figures
`media/P4/P4_lez_kin_mrreal_drift/paper_fig3_mrreal_drift.png` — FLASH vs WarpX profile
evolution at `t_FLASH` 0.10 / 0.20 / 0.30 ns (`tau_own` 0 / 2.70 / 5.39). PSC omitted; the
three-way version was too dense to read.

## Retracted
nothing
