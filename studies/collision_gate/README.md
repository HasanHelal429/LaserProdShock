# `collision_gate/` — D3: does WarpX's Coulomb module reproduce the theoretical e–i equilibration rate?

**Status: prediction written 2026-08-18, before the ladder ran.**
Gate on: `runs/P4/P4_lez_kin_bg` (and every other Phase-4 kinetic run).
Origin: `TEST_PLAN.md` §12.8 risk 1; decision **D3** in `runs/P4/README.md`;
Lezhnin et al., Phys. Plasmas **32**, 022701 (2025), **Appendix B**.

## Why this gate exists

The paper is explicit that collisions are load-bearing — *"auxiliary simulations with
either collisions or laser heating turned off demonstrated drastically different plasma
evolution."* So `P4_lez_kin_bg` is meaningless if its collision operator is wrong.

The specific risk: PSC implements a **special correction** to keep `e–i` and `i–i` rates
right under reduced `m_p/m_e` and reduced `c` (their Ref. 47). WarpX's `BinaryCollision`
is not known to have an equivalent. If it does not, transport is distorted **invisibly** —
nothing crashes, the numbers are simply wrong. This is the same discipline as CLAUDE.md's
"run phase space before the word shock": the cross-check that stops a plausible wrong
answer.

Two things found while setting this up, before a single run:

1. **`P4_lez_kin_bg` uses `collisions.intervals = 10`** (`ndt_supercycle = 10`), which is
   the paper's own base cadence — and the paper reports that this **underestimates the
   equilibration rate** wherever `ν_ei·dt_coll > 1`, with `ν_ei` the *Braginskii momentum*
   collision frequency. At our `dt` that product is **4.83** at `n_e = n_cr`, `T_i` = 12 eV.
   That is squarely their Fig. 11(a) failing case. It is *not* a hypothetical.
2. **`P4_lez_kin_bg`'s collision pairs cover only the target species.** `amb_electrons` and
   `amb_ions` are collisionless, and there are no target↔ambient pairs at all. At 1e-3 `n_cr`
   the ambient carries 0.35 % of the mass so this is probably minor, but it is undeclared
   and should be recorded.

## Method

Lezhnin Appendix B exactly, at **our production numerics** rather than theirs: a spatially
uniform, periodic, **laser-off** box of Maxwellian electrons and aluminium ions with
`T_e` = 1.1 `T_i`, in which `e–i` collisions are the only process that can move energy
between species.

* Box **20 `d_e`** (= 2 `d_i0`, `d_i0` = 10 `d_e` the proton skin depth at `n_cr`),
  40 cells at `dz` = 0.5 `d_e`, **periodic** both faces — no boundary of any kind.
* `Z` = 13, `m_i` = 2698 `m_e` (aluminium at the paper's reduced `m_p/m_e` = 100),
  `lnΛ` = 6.3 **pinned in both the deck and the analytic formula**, so `lnΛ` is removed as
  a confound. This tests the *operator*, not a `lnΛ` model.
* `cfl` = 0.35, `particle_shape` = 2, ppc 2000 — the production settings.
* `laser.intervals = 0`. (That is the only way to disable the operator: an
  `IntervalsParser` period contains step 0, so a huge period still fires.)
* Measurement is the `EP` reduced diagnostic's **per-particle mean energy**, so
  `T = (2/3)⟨E⟩`. Verified at step 0: it reads back 13.214 / 12.037 eV against the
  13.2 / 12.0 requested.

**Matrix** — 6 points × 3 arms = 18 runs, `n_e` = {1, 0.1, 0.01} `n_cr` ×
`T_i` = {12, 120} eV:

| arm | meaning |
|---|---|
| `coll_off` | collisions disabled — the **grid-heating control** |
| `c1` | `ndt_supercycle` = 1, collisions every PIC step |
| `c10` | `ndt_supercycle` = 10 — **the production cadence** |

The `coll_off` arm is not optional. `dz/λ_D` = 98 in the dense cold cases, so numerical
grid heating is expected, and it would masquerade as equilibration. The two have different
signatures — grid heating raises *both* species, equilibration moves energy from `e` to `i`
at fixed total — but the control measures it instead of assuming it away, and it also
supplies the **measured** temperature noise floor.

## Prediction (written before running)

Both species relax to `T_eq` = (Z·T_e0 + T_i0)/(Z+1), i.e. `T_i` rises by exactly **9.29 %
of `T_i0`** in every case, following Eq. (B1)

    T_i(t) = T_i0 + [Z(T_e0 − T_i0)/(Z+1)] · [1 − exp(−((1+Z)/Z)·ν_ie·t)]

whose structure I re-derived from energy conservation rather than trusting the PDF: with
`n_e = Z n_i` and `dT_e/dt = −(1/Z) dT_i/dt`, the difference `T_e − T_i` decays at
`((1+Z)/Z)·ν_ie` exactly as printed. The rate itself is the standard SI energy-relaxation
expression (`make_variants.py:nu_eps_ei`), **validated two independent ways**: hydrogen at
1 keV / 1e26 m⁻³ gives τ = 1.00e-8 s, and it reproduces `(m_i/2m_e)·τ_e` from the
Braginskii electron collision time to 0.1 %. The paper's own Eq. (8) is *not* used — the
two-column PDF extraction of it is garbled, and reconstructing it would have been guesswork.

| `n_e/n_cr` | `T_i` [eV] | τ [ps] | `ν_ei·dt` | `ν_ei·dt_coll` (production ×10) | steps | `t_run/τ` |
|---|---|---|---|---|---|---|
| 1.00 | 12 | 0.0197 | 0.483 | **4.83** | 400 | 2.00 |
| 1.00 | 120 | 0.6237 | 0.015 | 0.153 | 12 620 | 2.00 |
| 0.10 | 12 | 0.1972 | 0.048 | 0.483 | 3 991 | 2.00 |
| 0.10 | 120 | 6.2374 | 0.002 | 0.015 | 120 000 | 1.90 |
| 0.01 | 12 | 1.9724 | 0.005 | 0.048 | 39 907 | 2.00 |
| 0.01 | 120 | 62.374 | 0.0002 | 0.002 | 120 000 | 0.19 |

**What I expect:**

1. `c1` **matches Eq. (B1)** at all six points, to within the noise floor the `coll_off`
   arm measures. If it does not, WarpX's `BinaryCollision` does *not* handle our reduced
   mass ratio and the entire Phase-4 kinetic leg is void.
2. `c10` matches `c1` everywhere **except** `n_e = n_cr, T_i = 12 eV`, where
   `ν_ei·dt_coll` = 4.83 and the paper predicts an **underestimate**. This is the one point
   where I expect our production cadence to be measurably wrong.
3. `coll_off` shows no `e→i` energy transfer, and a *common* drift in both species that
   bounds the grid heating.

**The gate passes** if (1) holds, and if (2) confines the `c10` deficit to conditions the
production run does not spend meaningful time in. `P4_lez_kin_bg`'s plume — where every
Phase-4 measurement is made — sits at `n_e` ≤ 1 `n_cr` and `T_e` ≳ 250 eV, i.e. *hotter and
more tenuous* than every point in this matrix, so a deficit confined to the cold dense
corner would not invalidate it. **That conditional is the thing to check, not to assume.**

## Cost and device

890 754 steps total. **Run on CPU, not GPU** — the opposite of the production run's 12.7×
GPU advantage, and for the same underlying reason: this box is 40 cells, so on a GPU it is
kernel-launch-latency bound (21 `FillBoundary` calls per step; collisions are only 2.8 % of
the step) and measures **0.133 s/step**, against **0.011 s/step** on 8 CPU threads. ≈2.7 h
sequential, ≈40 min at 4-way parallel.

## Files
```
config.base.yaml    the base config; every variant is this with 6 keys overridden
make_variants.py    writes scratch/<variant>/{config.yaml,README.md}; --table prints the matrix
run_variants.sh     launches the ladder via scripts/launch.sh, with --verify after each
analyze.py          fits each arm against Eq. (B1) and emits the verdict table + figure
scratch/            the 18 variant run dirs (gitignored)
```

## What is NOT covered

* **Appendix C (electron thermal conductivity) is not in this study.** D3 names both. The
  conductivity test needs an imposed temperature gradient in a non-periodic box and a
  different diagnostic; it is a separate study and is still outstanding. This one covers the
  `e–i` thermalisation half only, and the gate should not be described as fully closed
  until Appendix C is done too.
* Reduced `c`. PSC also sets `m_e c²` = 60 keV; WarpX has real `c` and cannot. So this
  validates the module at *our* reduced-mass-ratio parameters, which is what the production
  run uses, not at PSC's.
* `i–i` and `e–e` rates are enabled (matching production) but are not themselves measured;
  they cannot move energy between species and so do not enter Eq. (B1).

## Result — ran 2026-08-18, 15 runs. **The e–i half of D3 PASSES.**

`media/b1_decay.png`. Rates are the fitted decay of `T_e − T_i`; `lnΛ` = 6.3 pinned in both
the deck and the analytic reference.

### WarpX reproduces Eq. (B1) exactly where its cross-section cap is inactive

| `n_e/n_cr` | `T_i` | cap-touched % of `f(v)` | `ν_ei·dt_coll` | `c1` ratio | `c10` ratio |
|---|---|---|---|---|---|
| 0.1 | 120 | **1.5 %** | 0.002 | **1.005** | 0.875 |
| 1 | 120 | 4.6 % | 0.015 | 0.890 | 0.637 |
| 0.01 | 12 | 12.9 % | 0.005 | 0.552 | 0.538 |
| 0.1 | 12 | 32.5 % | 0.048 | 0.250 | 0.225 |
| 1 | 12 | 65.2 % | 0.483 | 0.082 | 0.030 |

**The `c1` ratio is a clean monotonic function of the cap-touched fraction and is
UNCORRELATED with `ν_ei·dt_coll`** — the 0.01 `n_cr` / 12 eV point has `ν·dt_coll` = 0.005,
utterly resolved, and still reads 0.552. That decorrelation is the proof of mechanism: the
deficit is the cross-section cap, not the time step.

### The mechanism, read out of the source

`ElasticCollisionPerez.H` computes `σ_max = 1/(max(n₁,n₂)·r_min)` with
`r_min = (4πn/3)^(−1/3)`, and `UpdateMomentumPerezElastic.H` applies

    sigma_eff = min(pi * b0^2 * lnLmd, sigma_max)

i.e. a collision may not have a mean free path shorter than the distance to the next
particle (Perez et al., Phys. Plasmas **19**, 083104 (2012) §II.C; Angus et al., JCP **531**,
113927 (2025)). A pinned `CoulombLog` **is** honoured — line 181, `if (L > 0) lnLmd = L` —
but the cap is applied afterwards regardless. Because `σ_C ∝ v⁻⁴`, the cap engages below
`u_cap = (σ_max/σ_C(v_th))^(−1/4)`, so it bites on the slow tail even where the
thermal-speed ratio looks safe.

**Where the cap binds, the plasma is strongly coupled and the Spitzer rate at `lnΛ` = 6.3 is
not a physical target.** At `n_cr` / 13.2 eV the self-consistent `lnΛ` is **0.60**, and
0.60/6.3 = 0.095 against the measured 0.082. Those are exactly the conditions the paper
flags as "the `lnΛ` < 1 regime" in its Fig. 11(a). So the apparent 12× discrepancy is the
REFERENCE being wrong, not the operator.

### The confirmation run settles the input question independently
`D3_confirm_lnL20_n1_Ti120_c1`: `lnΛ` pinned at **20** at conditions where the cap is
inactive (`σ_max/σ_C` = 2.90). Measured ratio **0.669** against the **0.20** that would
follow if WarpX had silently used its own `lnΛ` = 4.06. The pinned value is used. (The
residual below 1.0 is the cap still touching 10 % of the distribution.)

### Controls are clean
Every `coll_off` arm gives `R_off/R_pred` ≤ 0.014 — **no measurable `e→i` transfer without
collisions**, despite `dz/λ_D` = 98 in the dense cold cases. Grid heating is not
contaminating this. Total energy conserves to **0.15 %** everywhere.

### Verdict for `P4_lez_kin_bg`
Evaluated **cell by cell on the production run's own profiles**, density-weighted, over the
underdense plume (1e-2 ≤ `n_e/n_cr` ≤ 1) where every Phase-4 measurement is made:

| τ | cap-touched (p50 / p90 / max) | `ν_ei·dt_coll` (p50 / p90 / max) |
|---|---|---|
| 6.7 | 1.03 / 1.71 / 1.71 % | 0.021 / 0.051 / 0.051 |
| 13.5 | 0.77 / 1.11 / 1.41 % | 0.014 / 0.028 / 0.039 |
| 20.3 | 0.73 / 1.35 / 1.46 % | 0.013 / 0.038 / 0.046 |
| 27.0 | 0.69 / 1.13 / 1.30 % | 0.013 / 0.028 / 0.038 |

The plume never exceeds **1.71 %** capped or **0.051** in the cadence parameter, and the
ladder measures **1.005** at 1.5 % capped. **So the production run's collisional transport
sits inside the regime where WarpX is exact.** The risk D3 was written to catch — that
WarpX lacks PSC's reduced-mass-ratio correction and distorts transport invisibly — is not
present.

The `t` = 0 cold dense target (10 `n_cr`, 100 eV) is at 18 % capped, so the *startup
transient* is under-collisional; it relaxes as the plume heats and rarefies.

### One real caveat, and a cheap fix
`c10/c1` = 0.87, 0.98, 0.72, 0.90, 0.37 in increasing `ν_ei·dt_coll`. Below `ν·dt_coll` ≈
0.5 the scatter is comparable to the effect, so **no trend is resolvable there** — the
honest statement is that the production cadence costs **of order 10–15 %** in the `e–i`
rate, rising to **63 %** at `ν·dt_coll` = 4.8. That is an uncertainty worth removing rather
than carrying: collisions are **10.4 %** of a production step at `ndt` = 10
(`doCollisions` 224 s of 2158 s), so `collisions.intervals: 1` roughly doubles the run to
~72 min and eliminates it. **Recommended for any future Phase-4 kinetic run.**

### What was dropped, and why
* **(0.01 `n_cr`, 120 eV)** — `τ` = 62 ps needs ~237 000 steps for S/N = 10; at an
  affordable 24 000 it is S/N ≈ 1.2, which would look like a measurement and be none. Its
  0.5 % cap fraction is bracketed by the (0.1 `n_cr`, 120 eV) point at 1.5 %.
* **The two 120 eV low-density families were shortened** from 120 000 to 24 000 steps
  (0.38 τ and 1.20 τ). Their rates come from the initial ramp; fit uncertainties are
  ≤ 0.5 %, but they carry more systematic risk than the 2 τ points.
* **Appendix C (electron thermal conductivity) is NOT covered**, so **D3 is not fully
  closed.** It needs an imposed gradient in a non-periodic box and a different diagnostic.

### Also found, before any run
`P4_lez_kin_bg`'s `collisions.pairs` cover **only the target species** — `amb_electrons`
and `amb_ions` are collisionless and there are no target↔ambient pairs. At 1e-3 `n_cr` the
ambient is 0.35 % of the mass so the effect is small, but it was undeclared.
