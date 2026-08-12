# Phase 4 — cross-code validation against Lezhnin 2025

Three runs of the **same physical problem** through three different models, to find out
whether they converge:

| Run | Model | Electrons | Ions | Who runs it |
|---|---|---|---|---|
| `P4_lez_flash` | FLASH rad-hydro | fluid, conducting | fluid | **collaborator** (we have no FLASH build) |
| `P4_lez_kin` | WarpX full PIC + ray tracing | kinetic | kinetic | us |
| `P4_lez_hyb` | WarpX hybrid + ray tracing | fluid (Ohm's law) | kinetic | us |

Spec: `TEST_PLAN.md` §12. Reference: Phys. Plasmas **32**, 022701 (2025);
PDF in the repo root.

---

## The unit map — read this before plotting anything

The paper carries two different `d_i0` and never says so in one place.

| | value | where it appears |
|---|---|---|
| `d_i0` **reduced** (`m_p/m_e` = 100) | 10 `d_e` = 1.693 µm | inside PSC's deck; the 1000 `d_e` box "= 100 `d_i0`" |
| `d_i0` **real** (proton at `n_cr`) | **7.256 µm** | the mm axis of Fig. 3; what makes the box comparable to FLASH's 800 µm |

Those two are **not compatible in physical units** — the gap is exactly the mass-ratio
reduction, `√(1836/100)` = 4.29. Our convention (`src/laserprod/units.py`) is *real electron,
light ion*: `m_i = mass_ratio · m_e` at the real `m_e`, so `d_e,cr = λ₀/2π = 0.1693 µm`
always, and a 1000 `d_e` box is **169.3 µm** of physical length — not the 726 µm the paper's
mm axis implies. FLASH, which has no such freedom, really is 800 µm.

**Rule: compare in NORMALISED units — `(z/d_i0, t/(d_i0/C_S0))`, each code using its OWN
`d_i0`. Never overlay two codes on a µm axis in this phase.**

Densities in `n_e/n_cr`. Temperatures in **absolute eV** — temperature is the one
absolutely-scaled quantity, and it is absolute because the laser pins it. That is the whole
reason this benchmark bites, and it is why a scale-free heater run could never do this job.

Anchors, all derived in `TEST_PLAN.md` §12.1:

```
lambda0 = 1.064 um     n_cr   = 9.848e26 m^-3     d_e,cr = 0.1693 um
I0      = 1e13 W/cm^2  = 1.0e17 W/m^2             pulse  = 1 ns
T_e,SS  = 823 eV       C_S    = 195 km/s          d_i0/C_S = 37.2 ps
1 ns pulse = 26.9 ion response times
```

`T_e,SS` = 823 eV comes from the paper's Eq. (15) **with `Z^(-1/3)`** — the exponent is
negative and a text extraction of the PDF drops the minus sign. It matches the ~800 eV
plateau in Fig. 3(b). Any run whose underdense `T_e` plateau is not within a factor of
order one of 823 eV has a setup error, not a physics result.

---

## Decision register

Eight decisions. Each states the options, the cost of being wrong, and what is currently
configured. **Everything here is a `config.yaml` edit** — nothing is baked into code — so
steering is cheap right up until the runs launch.

Status key: **[SET]** configured as shown · **[OPEN]** needs your call before that leg runs.

---

### D1 — Initial condition: FLASH snapshot, or a common analytic ramp? **[OPEN]**

**The problem.** The paper does *not* start PSC from a cold solid. A sharp solid edge gives
either `n_e >> n_cr` or `n_e` = 0 along a ray, so the tracer fully reflects and nothing
ablates — the "initial plasma problem". FLASH dodges it with a *slow start* (`dt` = 10⁻¹⁵ s,
numerical diffusion builds an ablation layer). PSC dodges it by **initialising from the
FLASH `t` = 0.1 ns snapshot**.

If we copy the paper exactly, both WarpX runs **block on the collaborator's FLASH output**.

| | Option | Consequence |
|---|---|---|
| **a** | Paper-faithful: FLASH cold-solid + slow start → snapshot at 0.1 ns → both WarpX runs read it | Most faithful. Blocks us entirely until FLASH output lands. Needs a snapshot→WarpX initialiser (new code). |
| **b** | Common analytic IC: all three start from the same analytic rarefaction (Eqs. 16–17) at the 0.1 ns-equivalent state | Unblocks us today. Cleanest 3-way comparison — no "did they start from the same thing?" ambiguity. FLASH deck becomes non-standard (it wants to start from solid). |
| **c** ← **recommended** | Both: collaborator runs FLASH **twice** — once cold-solid (paper-faithful) and once from the analytic IC. WarpX runs from the analytic IC. | Costs the collaborator one extra 1D run (minutes). The cold-solid run *validates the analytic IC* by comparison at 0.1 ns; the analytic-IC run is the true apples-to-apples partner. |

**Why (c).** It buys the thing (a) and (b) each lack: (a) can never separate "the codes
disagree" from "they started differently", and (b) can never check that our analytic stand-in
is a fair representation of a real ablation layer. (c) gets both for one extra cheap run,
and it unblocks our two runs immediately.

**Currently configured:** analytic ramp (option b/c path), so `P4_lez_kin` and `P4_lez_hyb`
are launchable without waiting. Switching to (a) later is a config edit plus an initialiser.

---

### D2 — The hybrid has no electron thermal conduction. Accept, or implement? **[OPEN]**

`hybrid_pic_model.electron_energy_mode = conducting` **aborts as unimplemented**. The
available `advected` mode carries advection + compression + the laser source and **no
∇·q_e**.

This is not a detail for *this* benchmark: FLASH's ablation front is *set* by Spitzer
conduction with a Larsen flux limiter (`α_ele` = 0.06), and the paper's §III.C is entirely
about heat flux.

| | Option | Consequence |
|---|---|---|
| **a** | Run `advected` and report the gap as the finding | Zero code. Likely outcome: hybrid reproduces the rarefaction, fails the ablation front. That is a *publishable limitation statement*, not a failure. |
| **b** | Implement `conducting` (Spitzer `κ_e` + Larsen limiter) first, then run | Makes the hybrid a genuine rad-hydro competitor. Real code: a flux-limited diffusion solve on `T_e`, implicit or sub-cycled. Days, not hours. |
| **c** ← **recommended** | **(a) then (b)** — run `advected` as the control, measure exactly where and by how much it fails, then implement `conducting` and re-run | The control run is nearly free and it *justifies* the code. Without it, an implementation of `conducting` has nothing to be measured against. |

**Note:** (b) is the single highest-value code item this phase could produce — it is the
difference between "our hybrid can drive shocks" and "our hybrid can model ablation". But
doing it before (a) means building a solver with no baseline to prove it changed anything.

**Currently configured:** `advected` (the control leg of c).

---

### D3 — Validate WarpX's collision module before trusting the kinetic run? **[SET: yes]**

The paper: *"auxiliary simulations with either collisions or laser heating turned off
demonstrated drastically different plasma evolution."* Collisions are load-bearing, so
`P4_lez_kin` is meaningless without them.

**The risk.** PSC implements a *special correction* to keep `e-i` and `i-i` rates right
under reduced `m_p/m_e` and reduced `c` (their Ref. 47). WarpX's `BinaryCollision` is not
known to have an equivalent. If it does not, transport is distorted **invisibly** — nothing
crashes, the numbers are just wrong.

**Set:** reproduce the paper's Appendix B (`e-i` thermalisation vs their Eq. B1, in a
2 `d_i` periodic box) and Appendix C (conductivity) **before** `P4_lez_kin` is believed.
Cheap — small periodic boxes, seconds each — and it is the gate on the whole kinetic leg.
This is the same discipline as CLAUDE.md's "run the phase-space diagnostic before any shock
claim": the cross-check that stops a plausible-looking wrong answer.

---

### D4 — Mass ratio and charge state **[SET: `m_p/m_e` = 100, `Z` = 13, `m_Al/m_e` = 2698]**

The paper uses `m_p/m_e` = 100 and `m_e c²` = 60 keV, converged against 400 and 200 keV
(their Appendix A, Fig. 10). Aluminium is 26.98 `m_p`, so `m_Al/m_e` = 2698.

**WarpX cannot reduce `c`** — real `c`, real `m_e`. So we match the *dimensionless* physics
(`n_e/n_cr`, `T_e` in eV, `Z`, `m_p/m_e`) and accept `C_S/c` = 0.00279 against PSC's
0.00813. At 823 eV the flow is deeply non-relativistic, so `C_S/c` enters **nothing but the
step count**. It is a cost parameter here, not a physics one.

Cost knob if needed: dropping to `m_p/m_e` = 25 halves the step count. Only with a
convergence check, and the paper's Fig. 10 went the *other* way (100 → 400), so there is no
published support for going lower.

---

### D5 — Target density cap `n_max` **[SET: 10 `n_cr`]**

Real solid Al is ~700 `n_cr`. The paper caps PIC at 10 `n_cr` and its Appendix A scan
(2, 5, 10, 20 `n_cr`) finds **`T_e` matches FLASH only for `n_max` ≥ 5 `n_cr`**; lower caps
also give unphysical target recoil and boundary reflection.

10 `n_cr` is therefore the paper's value *and* comfortably inside the converged range.
Note this is far above the 1.5 `n_cr` used everywhere in Phases 0–3 — a Phase-4 config is
not a Phase-1 config with the laser turned up.

**Consequence to keep in view:** the overdense interior is a *different physical object* in
PIC than in FLASH. §12.6 excludes `n_e > n_cr` from the acceptance criteria for this reason.

---

### D6 — Particles per cell **[SET: ladder 500 → 2000 → 10000]**

The paper uses 10⁵ ppc at `n_cr`, which buys resolution down to 10⁻⁵ `n_cr`. For us that is
~18 GPU-h and it buys only the low-density tail.

| ppc(e) at `n_cr` | particles | GPU-h |
|---|---|---|
| 500 | 0.53 M | 0.09 |
| 2 000 | 2.13 M | 0.35 |
| 10 000 | 10.7 M | 1.8 |

**The ladder is the deliverable, not the largest run.** Stop where the A1–A8 quantities stop
moving. Gate G5 (`T^(-3/2)` is convex, so per-cell noise biases absorption *high*) means the
low-ppc rungs will over-absorb — that bias is a known, signed effect, and watching it shrink
up the ladder is itself the convergence evidence.

---

### D7 — Dimensionality **[SET: 1D, all three]**

The paper checks this both ways and finds no dimensional effect: FLASH quasi-1D (2D, 100 µm
transverse) "lead to identical plasma profiles with the 1D simulation", and PSC 2D at
`L_x` = 5 `d_i` and 40 `d_i` shows "no notable differences", *"primarily due to high plasma
collisionality"*.

1D also sidesteps every transverse-boundary hazard Phase 0 spent itself on. The caveat is in
the paper's own words — the null result is attributed to high collisionality, so it should
not be assumed to survive to higher intensity. At 10¹³ W/cm² we are squarely in the regime
where they verified it.

---

### D8 — Where the FLASH outputs land, and in what format **[OPEN]**

We need, per dump time (0.1, 0.2, 0.4, 0.6, 0.8, 1.0 ns), 1D profiles of:

```
z [um]   n_e [m^-3]   T_e [eV]   T_i [eV]   V_z [m/s]   P_abs [W/m^3]   Z_bar
```

Plain text with a header row is ideal and is what `scripts/xcode_compare.py` will expect.
Raw FLASH HDF5 plotfiles are also fine — `yt` reads them — but then the extraction is on us
and the column-naming trap from `io.profile_column_names` applies with full force.

**Open:** which the collaborator prefers, and the shared path. Note the repo convention
(memory: *cellar diag archive*) that finished diagnostics live on `/mnt/cellar/hhelal` with
symlinks left at the original paths.

---

## Sequencing

```
D1-D8 steered
  |
  +-- [code] deck.py: collisions block + hybrid block  (§12.3)
  |     |
  |     +-- D3 gate: Appendix B/C collision tests ------+
  |     |                                               |
  |     +-- P4_lez_hyb (advected)   <- cheap, no gate   |
  |                                                     v
  |                                              P4_lez_kin ppc ladder
  |
  +-- P4_lez_flash deck -> collaborator -> outputs in shared
                                              |
                                              v
                                     scripts/xcode_compare.py -> A1-A8 table
                                              |
                                              v
                                     D2(b)? implement `conducting`, re-run hybrid
```

The FLASH leg and the WarpX legs are independent under D1(c) — neither blocks the other.
The only hard ordering is **D3 before believing `P4_lez_kin`**.
