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

## Result

_To be filled in by `analyze.py` once the ladder has run._
