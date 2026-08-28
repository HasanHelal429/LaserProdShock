# P4_lez_kin_flashic — kinetic leg, no background, initialised from the FLASH snapshot

> ## [SUPERSEDED] — diagnostics deleted 2026-08-28
> **Reservoir-motivated 40 n_cr / 20 d_i0 target rather than the paper-faithful 10 / 4.5. NOT a carrier of the 5.19x corona bug -- its mass_ratio was never changed.**
> 
> Superseded by: **P4_lez_kin_ic6**. `diags/` and `run.log` were removed to reclaim disk; the
> config, deck, `warpx_used_inputs` and this README are kept as the provenance record.
> Re-run from the config if the raw output is ever needed again.
> See `runs/P4/SUPERSEDED.md` for the full ledger.

**Phase.** 4, `TEST_PLAN.md` §12; decisions **D1** (initial condition) and **D5** (`n_max`).

**Question.** How much of `P4_lez_kin`'s departure from FLASH is its *initial corona*
rather than its physics? Its plume runs 2.03× too far and 1.37× too fast, and its target
disassembles — but it also starts from a Gaussian corona 18× too far out, 3.8× too cold,
and at rest. This run replaces the initial condition with one fitted to FLASH's own 0.1 ns
snapshot and changes nothing else about the solver.

**Decision D1, executed.** Replaces `P4_lez_kin`'s analytic ramp with an initial condition
fitted to the delivered FLASH run (`Ablation_prod_08-17`) at **t = 0.1 ns**, the state the
paper hands to PSC. No background species, as the paper specifies.

## The question
`P4_lez_kin` (no background) departs from FLASH badly at τ = 27: plume front **2.03×** too
far, outflow **1.37×** too fast, density scale length **1.82×** too long, and its target
disassembles from 10 to **1.74 n_cr** — it goes fully underdense, so the laser stops being
absorbed at a surface at all. This run asks how much of that is the **initial corona**
rather than the physics.

## Geometry
1D, `z` only. Domain **−224 → +2464 `d_e`** (2688 `d_e`, **5376 cells** at `dz` = 0.5 `d_e`;
5376 = 64 × 84, and AMReX aborts outright if the domain is not divisible by
`blocking_factor` — the first draft's 5340 was not). Target slab spans **−200 → 0 `d_e`**
with its laser-facing face at `z` = 0; the corona extends to +`z`. **`lo` = reflecting**
(the rest of a semi-infinite target), **`hi` = open** (the plume leaves). Laser injected
from the `hi` face, travelling −`z`.

## What changed from `P4_lez_kin`, and why — each fitted, not assumed

| | `P4_lez_kin` | this run | FLASH at 0.1 ns |
|---|---|---|---|
| peak `n_e` | 10 `n_cr` | **40 `n_cr`** | 795 `n_cr` |
| slab thickness | 45 `d_e` | **200 `d_e`** | 295 `d_e` |
| corona form | Gaussian | **exponential** | exponential (rms 0.107 vs 0.361) |
| corona scale | 27 `d_e` | **6.955 `d_e`** | 6.955 `d_e` (fitted) |
| `n_cr` surface at | 40.6 `d_e` | **2.31 `d_e`** | 2.31 `d_e` (fitted) |
| corona `T_e` | 100 eV | **378.3 eV** | 378.3 eV, isothermal |
| corona `T_i` | 10 eV | **115.6 eV** | 115.6 eV (`T_e/T_i` = 3.27) |
| solid `T_e` | 100 eV | **20 eV** | 0.138 eV |
| initial flow | **at rest** | `v/C_S0` = 0.548 + 0.056 `z/d_e` | same (rms 0.099) |
| collisions | every 10 steps | **every step** | — |

1. **Reservoir.** PIC cannot carry 795 `n_cr` (`ω_pe·dt` = 4.93 against the 1.2 gate).
   40 `n_cr` × 200 `d_e` gives `ω_pe·dt` = 0.79 at `cfl` = 0.25 and an areal density
   **11.7×** `P4_lez_kin`'s. FLASH ablates 1.06e23 m⁻² over 27 τ = **7.9 %** of this
   reservoir, against ~100 % of `P4_lez_kin`'s. That is the difference between a target
   that ablates and one that disassembles. Still 15 % of FLASH's reservoir — **not** a
   match, and the run should be read with that in mind. [D5]
2. **Corona form.** A Gaussian is the wrong shape and cannot be tuned into the right one:
   its local scale length `L²/(2z)` varies through the corona, so matching `L_n` at
   `n` = 0.1 `n_cr` forces the critical surface to 24–42 `d_e`. `P4_lez_kin` put it at
   40.6 `d_e` where FLASH has it at 2.31 — a factor 18 — so its laser began depositing far
   out in a tenuous corona instead of at a compact ablation front.
3. **Temperature.** FLASH's corona is isothermal at 378 eV (spread 374–379 across four
   decades) over a cold solid. 100 eV everywhere is 3.8× too cold where inverse
   bremsstrahlung goes as `T^(-3/2)`, and far too hot in the reservoir.
4. **Flow.** The handoff state is a rarefaction already moving at up to 4–5 `C_S0`.
   Starting it at rest is visible in the earlier comparison as the front-position ratio
   running 1.69 at τ = 6.7 and only settling to 1.11 by τ = 27.
5. **Collisions every step** — the D3 gate measured that `ndt` = 10 costs 10–15 % in the
   `e–i` rate for ~10 % of the step cost (`studies/collision_gate/`).

## Verified before launch (smoke run, 4 steps)
The realised initial state, measured from the step-0 particle dump, against what was asked:

| | asked | realised |
|---|---|---|
| corona scale `L` | 6.955 `d_e` | **6.9550** |
| `n = n_cr` at | 2.3144 `d_e` | **2.3204** |
| drift `v/C_S0` | 0.5482 + 0.055975 `z` | **0.5465 + 0.056032 `z`** |
| peak `n_e` | 40 `n_cr` | **40.00** |
| solid `T_e` | 20 eV | **19.95** |
| corona `T_e` | 378.3 eV | **≈378** |

and the corona density tracks FLASH's to a few percent across four decades. No new key
appears in WarpX's `Unused ParmParse` list, so `ux_std_function`, `uz_mean_function`,
`ncor`, `zcor`, `uza`, `uzb` and `th_ts` were all genuinely queried — the check CLAUDE.md
requires, because a binary that predates a deck flag ignores it silently.

**The smoke test also exposed a real bug** (now fixed, `tests/test_structures.py`):
`density_min` was applied identically to both species although the ion density function is
`(n_e expression)/Z`, so ions were culled a factor **Z = 13** in density earlier than
electrons — leaving an 18 `d_e` shell at the plume tip with net charge **−1.000** of the
local density. Only 7.5e-5 of the total charge, which is why no energy budget ever caught
it, but locally complete. **Every Z ≠ 1 run this project has produced carries it.**

## Known departures from FLASH — stated, not smoothed over
* **Reservoir is 15 % of FLASH's**, and 7.9 % of it is consumed over the run against
  FLASH's 0.275 %. This run is closer to quasi-steady ablation than `P4_lez_kin` was, but
  it is not FLASH.
* **Solid at 20 eV, not 0.138 eV.** At 40 `n_cr`, FLASH's true value gives
  `dz/λ_D` = 6100 and the solid would numerically heat faster than the laser heats it.
  20 eV gives 413. G2 will warn; that is why the laser-off control is mandatory here.
* **`dz/λ_D` = 116 in the corona** (G2 warns) — unavoidable at one uniform grid.
* **The initial corona is truncated at `n_e` = 4e-3 `n_cr`** by `density_min`
  (`z` ≈ 40.7 `d_e`), where FLASH's runs to 1e-7. That tail carries 3.5e-6 of the areal
  density, so it is negligible as mass, but the initial plume tip is not represented.
* **`ray_cfl` = 0.25 is unvalidated at 40 `n_cr`** (G4 warns): there is an interior critical
  surface and convergence is non-monotonic for turning-point problems. A ladder is owed.

## Cost
5376 cells, `max_step` = 774 144 (= 28 × 27 648), `dt` = 0.0706 fs, `t_end` = 54.66 ps
= **26.96 `d_i0/C_S0`** — the same normalised duration as FLASH's 1 ns and every other
Phase-4 leg.

## Result — ran 2026-08-18, 774 144 steps, 1 h 27 m on one GPU, no NaN

**The initial corona did describe most of the discrepancy, and the energy budget is now
right. What is left is absorption, and that part cannot be fixed at a reduced mass ratio.**

### Against FLASH at τ = 27 (ratio to FLASH; 1.000 = perfect)
| | old analytic IC | **this run** |
|---|---|---|
| peak `n_e` | 1.74 `n_cr` — **disassembled** | **37.8 `n_cr`** — survives, 5.4 % consumed |
| `ζ_cr` | −4.13 (collapsed) | 7.87 (**1.89×**) |
| plume front | **2.03×** | 0.50× |
| `v` at 0.1 `n_cr` | 1.37× | 0.24× |
| `L_n` | 1.82× | 0.41× |
| plume `T_e` | 0.56× | 0.20× |

### The energy budget, which is the thing that was actually wrong
| | absorbed per TARGET electron | per ABLATED electron |
|---|---|---|
| FLASH | 13.4 eV | 4872 eV |
| old analytic IC | **243 eV — 18× too much** | 248 eV |
| this run | **9.2 eV — 0.69×** | 170 eV |

The old run over-coupled by **18×**, which is the whole reason its plume ran 2× too far and
1.4× too fast. Two causes, both in the initial corona: it was 3.8× too cold, and inverse
bremsstrahlung goes as `T^(-3/2)`, so it absorbed **7.3×** too strongly; and its reservoir
was 11.7× too small, so that energy landed in far too little mass. Measured optical depth
through the corona in absolute metres confirms it directly — the old run reaches **5.68×**
FLASH's by τ = 27, this run **0.53×**.

### This run is now SELF-CONSISTENT, which the old one was not
`T_e,SS ∝ I_abs^(2/3)`, and against each leg's own reduced-mass Manheimer value (312 eV):

| | `f_abs` | `T_e` its absorption supports | measured | ratio |
|---|---|---|---|---|
| FLASH | 0.870 | 823 eV | 839 | **1.019** |
| old analytic IC | 0.813 | 298 eV | 473 | **1.587** |
| this run | 0.358 | 173 eV | 168 | **0.974** |

The old leg sat 1.6× above what its absorption could support — a target being volumetrically
cooked rather than ablated. This one sits at 0.97 of its own prediction: it is doing the
right physics, just under-driven.

### What is left, and why it is not fixable here
The entire residual is the absorbed FRACTION, 0.358 against FLASH's 0.870. Absorption
integrates `κ` over **metres**; the hydrodynamics scales with `d_i0`. The reduced mass ratio
separates the two, and `d_i0` is **4.29× smaller** in WarpX — so a corona matched in
normalised units is 4.29× shorter in absolute length and cannot carry FLASH's optical depth.
Matching the absorption instead would require a corona 4.29× longer in `d_i0`, which would
then be the wrong hydrodynamic profile. **At a reduced mass ratio you can match the
ablation dynamics or the absorption, not both.** This is a limitation of the paper's whole
approach, not of this deck, and is probably why PSC also reduced `c` — which moves `n_cr`
and rescales the absorption with it. WarpX has real `c` and cannot.

### Caveat on a diagnostic
`Tlocalfrac` reads 1.2e-7 here against ~1.0 in the old run, which looks alarming and is not:
it is `n_e²`-weighted over **all** cells, so the opaque 40 `n_cr` slab outweighs the corona
~45 000:1 and the number describes the slab, which absorbs nothing. The absorbing plasma
demonstrably used its own per-cell temperature — `A × T_e^{1.5}` is constant to four
decimals across all 447 absorbing cells, and every `laserdep_profile` dump has `theta_e > 0`
in 100 % of corona cells. **Do not read `Tlocalfrac` on a run whose target is much denser
than its corona.**

## Retracted
_Nothing yet._
