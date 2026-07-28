# TEST_PLAN.md — Testing the WarpX ray-tracing laser-deposition module as a shock driver

**Project.** `LaserProdShock` — a systematic test campaign for the WarpX
`LaserDeposition` operator (`warpx-cda/Source/Particles/LaserDeposition/`) used as a
**shock driver**: an actual ray-traced laser ablating a target, replacing the prescribed
`ParticleHeater` + `TargetInjector` piston surrogate that `KinShock2020` used to replicate
Schaeffer et al. 2020.

**Status.** **Phase 0 is complete** (2026-07-28): tooling built, all five boundary runs
done, and the boundary decision recorded (`open` on the propagation axis + periodic
transverse; B₀ uniform to 1.000000 under pec).
The config schema (§3), the deck renderer, gates G1–G7, the laser diagnostics and the
cross-run comparison all work in 1D and 2D from one code path; 71 tests pass. The three
source-code questions of §5.1 are resolved. Phases 1–3 remain as written.

**The one-sentence question.** *Can a ray-traced laser drive a piston that produces a
verifiable collisionless shock in WarpX, and what does the laser have to be for that to
happen?*

Companion documents: `OVERVIEW.md` (the physics and the operator's model),
`RESULTS.md` (the running lab notebook — read it first to learn current state),
`runs/README.md` (run-ID and per-run-README conventions).

---

## 1. Scope, and what is already settled

### 1.1 Do not re-derive the operator's correctness

The module has already been implemented and validated against **analytic theory** in
`warpx-cda/laser_deposition/` (see `LASER_DEPOSITION_PLAN.md` and `ACCURACY.md` there).
That work is upstream of this project and is **not** to be repeated:

| Already established | Result |
|---|---|
| Uniform-slab absorbed power vs Beer–Lambert IB | 0.36 % (CI test A) |
| 1D ramp + turning-point reflection vs closed-form WKB | 1.6 % (CI test B1) |
| 2D 30° oblique refraction, turning point at `z_crit cos²θ₀` | 1.3 % (CI test B2) |
| Gaussian beam profile weighting + sub-cell sampling | 0.1 % |
| Converging (focused) beam, per-ray directions | 0.02 % |
| Per-cell deposition profile vs analytic march (uniform) | 0.000 % (cells 2…510) |
| Ramp deposition profile across 8 decades | overlays closed form |
| Coefficient audit: exponents on `n_e`, `Z_eff`, `lnΛ`, `T_e`, `I` | 2.018 / 0.9999 / 0.9999 / −1.4999 / 2.028 |
| 3D circular footprint | 0.10 %, `w_x/w_y = 1.000001` |
| Local-`T_e` mode tracks an imposed 10× ramp | 0.05 % |

**What is not established is exactly this project's subject**: whether the operator,
coupled self-consistently to a magnetized ambient plasma in a PIC run, drives a *shock* —
and how the shock's properties depend on the laser. The one attempt so far
(`warpx-cda/laser_deposition/run_laser_shock/`) produced a **freely-propagating fast
magnetosonic pulse, not a shock**, and an earlier "marginally supercritical shock" reading
from it was **retracted** (RESULTS 2026-07-27 there). That retraction is the reason this
project exists as a structured campaign rather than a single run.

### 1.2 Inherited hazards — the reason for the phase ordering

Five facts from the prior work drive the whole plan and are treated as **known hazards, not
open questions**:

1. **The laser pins the absolute density scale.** The heater surrogate is scale-free; IB
   absorption is measured against `n_cr = ε₀ m_e ω²/e²`, so λ₀ fixes the density in m⁻³.
   A target at `KinShock2020`'s `n0 = 10¹⁸ m⁻³` is `2.5×10⁻⁸ n_cr` and perfectly
   transparent. **Every density in this project is quoted in `n_cr`.**
2. **`ω_pe·dt < 2` is the binding stability condition, and the grid CFL cannot see it.**
   At `cfl = 0.75` the `run_laser_shock` deck sat at `ω_pe dt = 1.91` and went unstable as
   its own ablation compressed the target — inflating total particle energy 21× and
   invalidating every number measured past `t ≈ 0.1 ω_ci0⁻¹`. The check must be made at the
   **peak compressed density the run will reach**, not the initial one.
3. **Boundary conditions are not free.** WarpX forces particle boundaries periodic whenever
   the field boundaries are periodic (`Source/Particles/ParticleBoundaries.cpp`), and a
   free expansion has a runaway ion front (measured at 0.20 c) that then *wraps* and
   pollutes the upstream. No vacuum gap is large enough. This is Phase 0.
4. **Absorption is self-limiting**, because `K ∝ Z_eff lnΛ n_e² T_e^{-3/2}`: a cold target
   absorbs ~90 % and shuts itself off within ~0.05 gyroperiods as its corona heats and
   rarefies. Coupled energy is therefore set by the target electrons' heat capacity at
   shutoff and is nearly *independent of intensity*. `Z_eff·lnΛ` is a very strong knob
   (25 → 91 gave **16×** the coupled energy).
5. **Phase space is the only arbiter of a shock claim.** The B and density streaks of the
   `run_laser_shock` pulse looked shock-like on their own. What disproved the shock was the
   phase space: 0.00 % ion reflection, upstream/downstream `f(u_z)` differing only by a
   drift and a mild broadening, and a piston (~1 v_A) *slower than the compression it had
   launched* (2.63 v_A). **No run in this project may be called a shock without a
   phase-space diagnostic.**

### 1.3 Explicitly out of scope

- Re-validating the ray tracer against analytic IB / WKB (done upstream; §1.1).
- Cross-validation against PSC — blocked upstream because Hyder et al.'s PSC ray-tracing
  module is not public (`LASER_DEPOSITION_PLAN.md`, 2026-07-27).
- Mesh refinement: the operator asserts `finestLevel() == 0`. One uniform grid must resolve
  both the near-critical target and the tenuous ambient; that scale separation is a central
  difficulty, not something to be engineered away.
- 3D. The operator has a verified 3D path, but nothing here needs it. Revisit only if the
  Phase 3 geometry sweep shows a 2D→3D-sensitive result.

---

## 2. Physics and the quantities to be measured

`OVERVIEW.md` carries the full model. What matters for the test design:

### 2.1 Units — everything hangs off λ₀

With `n_e = n_cr` by definition of critical density, `ω_pe = ω₀`, so the electron skin
depth at critical density is exactly

```
d_e,cr = c/ω₀ = λ₀/2π
```

For λ₀ = 1.053 µm: **`n_cr = 1.005×10²⁷ m⁻³` (= 1.005×10²¹ cm⁻³), `d_e,cr = 0.1676 µm`.**
This is a genuinely convenient regime: Schaeffer's Table I ablation density
(6×10²⁰ cm⁻³) is **0.6 n_cr** at 1 µm and its upstream (4.8×10¹⁸ cm⁻³) is
**0.0048 n_cr** — so the paper's experiment-relevant densities are natural for a 1 µm
laser, and no unphysical stretch is needed to place a real laser in the Schaeffer regime.

**Length convention.** Configs express lengths in `d_e,ref`, where
`reference.length_scale` selects `critical | target | ambient`. Default `ambient` for runs
that have one (continuity with `KinShock2020` and `run_laser_shock`), `critical` for vacuum
runs. `laserprod.units` reports all three. *This is the single most confusable thing in the
project* — see the two-different-"20"s trap that `KinShock2020`'s `CLAUDE.md` documents for
collisionality, and do not repeat its shape here.

**It is also a cost decision, not just a label.** All five Phase-0 runs use `critical`, so
their geometry is directly comparable and a vacuum run needs no ambient to reference. But
`d_e,cr = 0.1676 µm` is **4× finer than `d_e,amb`**, so at the same `dz_over_de` the cell is
4× smaller and `dt` 4× shorter — 16× the cost for the same physical box. The upside is that
`ω_pe·dt` and `dz/λ_D` both improve by the same factor (G1 = 0.21 rather than 1.88;
`dz/λ_D` = 61 rather than 245). Phase 1's vacuum runs keep `critical`; Phase 2 switches to
`ambient` for gyro-scale boxes, where the cost matters more than the resolution does.

Worked example for the `run_laser_shock` parameters (target 1.5 n_cr, ambient 0.06 n_cr,
25:1 contrast, m_i/m_e = 100, v_A = 0.003 c):

| | value |
|---|---|
| `d_e,amb` | 0.684 µm |
| `d_i,amb` | 6.84 µm |
| `d_e(target, 1.5 n_cr)` | 0.137 µm |
| `B₀` | 74.7 T |
| `ω_ci0⁻¹` | 7.61 ps |
| `ρ_i0` at `v_p = 0.0196 c` | 44.7 µm = **65 d_e,amb** |

The last line matters: `ρ_i0` is only ~65 `d_e,amb`, not the ~1040 of `KinShock2020`'s
`R1_*`, because `B₀` is large relative to the density. A 3200 `d_e` axial box is ~49 `ρ_i0`,
and a transverse extent of ~1 `ρ_i0` is only ~65 cells at `dz = 0.5 d_e`. **A genuinely
2D magnetized laser-driven shock is therefore affordable here** — an important difference
from the `KinShock2020` regime, and the reason 2D is in this plan as physics rather than as
a smoke test.

### 2.2 The measured quantities

Every run reports, through `laserprod.metrics`:

- **Laser side** (from the operator's own `LASERDEP step <n> t <s> Pabs <W> Eabs <J>` line,
  plus `Tlocalfrac`): incident power, absorbed power `P_abs(t)`, absorbed fraction
  `f_abs(t)`, cumulative `E_abs(t)`, shutoff time `t_s` (when `f_abs` falls below half its
  peak), and the per-cell deposition profile from `profile_intervals`.
  *These come straight from the ray tracer and are immune to grid heating* — which is why
  they, not particle energies, are the primary laser diagnostic.
- **Target / piston side**: electron temperature history `T_e(t)` in the target, target
  peak density (for the `ω_pe dt` gate), ion phase space, **piston speed `v_p`** measured
  from the ion front and from the magnetic-cavity peak, piston momentum, and the fraction
  of `E_abs` that ends up as directed ion kinetic energy (the drive efficiency).
- **Shock side** (Phase 2 onward): `n_e/n_e0` and `B/B₀` compression, ramp scale in `d_i0`,
  front trajectory and speed `v_sh`, `M_A` and `M_ms`, reflected-ambient-ion fraction
  `G(t)` and profile `F(z,t)`, and piston–shock separation in `ρ_i0` — i.e. Schaeffer's
  **seven criteria** and **three timescales** (`t* ≈ 1, 2.5, 5 ω_ci0⁻¹`), ported from
  `KinShock2020/src/kinshock/metrics.py`.
- **Numerical health**: `ω_pe dt` at peak density, `dz/λ_D` per region, energy closure
  (`E_abs` from the tracer vs the particle KE gain), and the laser-off control's spurious
  heating rate.

### 2.3 The scaling hypotheses the sweeps are meant to test

These are *predictions to be falsified*, written down in advance so the sweep is a test and
not a fishing trip. Let `N_e = n_t w_t` be the target areal electron density.

**H1 — shutoff temperature.** Absorption shuts off when the optical depth through the
absorbing layer falls to ~1, so `T_e,shutoff ∝ (Z_eff lnΛ n_e² L)^{2/3}`.

**H2 — coupled energy is intensity-independent.** `E_abs ≈ (3/2) N_e k_B T_e,shutoff`,
independent of `I₀`, with the shutoff *time* `t_s ∝ 1/I₀`.

**H3 — piston speed.** `v_p ≈ α c_s(T_e,shutoff)`, `c_s = √(Z k_B T_e/m_i)`, α ≈ 1–3, hence
`v_p ∝ (Z_eff lnΛ)^{1/3}` and `v_p` roughly independent of `I₀` **and of target thickness**
(thickness raises `E_abs` and the mass in step, so `v = √(2E/m)` is unchanged — it buys
piston *momentum* and drive distance, not speed).

**H4 — low intensity may drive shocks better.** If H2 holds, then raising `I₀` shortens the
drive rather than strengthening it. Schaeffer found ≳ 1 `ω_ci0⁻¹` of drive is needed for
formation, so there should be an *optimum* `I₀`: high enough to reach a supercritical `v_p`,
low enough that `t_s ≳ 1 ω_ci0⁻¹`. **This is the plan's most consequential prediction** and
Phase 3A is built to find that optimum.

**H5 — planarity.** A 2D run stays quasi-1D on axis while the plume's lateral expansion
stays inside the spot: `c_s t ≲ w₀`. For formation at `t ≈ 2.5 ω_ci0⁻¹` and `v_p ≈ 3 c_s`,
this needs `w₀ ≳ 0.8 ρ_i0` — for the §2.1 parameters ~52 `d_e,amb` ≈ 36 µm. Narrower spots
should degrade the shock; wider ones should reproduce 1D.

**Known tension to resolve.** H1–H2 predict `E_abs ∝ (Z_eff lnΛ)^{2/3}`, i.e. a factor 2.4
for the observed 25 → 91 change in `Z_eff·lnΛ`. The measurement was **16×**. So the static
shutoff picture is wrong or incomplete — plausibly because absorption stays near 100 % long
enough that `E_abs ≈ f_abs I₀ t_s` is drive-limited rather than capacity-limited, which
would also break H2. **Explaining that discrepancy is a named deliverable of Phase 3A**, not
a footnote.

---

## 3. Architecture and working rules

Identical in spirit to `KinShock2020`; see `CLAUDE.md` for the enforced version.

- **`runs/<ID>/config.yaml` is the single source of truth.** It holds intuitive primaries
  (densities in `n_cr`, temperatures as `θ = kT/m_e c²`, lengths in `d_e,ref`, speeds in
  `c`, intensity in W/m²). `scripts/make_inputs.py` renders the WarpX deck from it.
  **Never hand-edit a deck**; edit the config and regenerate. `--verify` diffs
  `warpx_used_inputs` against the config after a run.
- **Every run directory carries a `README.md`** describing what it is, what question it
  answers, what was expected, and — after it runs — what happened and what is retracted.
  `launch.sh` refuses to start a run that has no `README.md`. This is a hard rule: the
  retracted shock claim is exactly what an unwritten run README costs.
- **`scripts/launch.sh` is the only way to start a run.** It cd's into the run dir (so
  `diags/` cannot be shared and clobbered), picks `warpx.1d`/`warpx.2d` from
  `geometry.dims`, applies the benchmarked OMP settings, and refuses to overwrite a
  populated `diags/`. `-b` detaches, `-L` also starts the progress logger.
- **Shock kinematics come from `runs/<ID>/shock_fit.yaml`, fitted by eye**
  (`scripts/tune_shock.py`), never from auto-detection — the convention `KinShock2020`
  arrived at after automatic `v_sh` drifted between scripts.
- **`RESULTS.md` gets a dated entry per substantive run or finding.** That is how context
  survives between sessions.

### Proposed `config.yaml` schema

Sketch, to be finalised as the first task of Phase 0 (§5.1):

```yaml
meta:      {run_id, phase, description, reference, deck}
reference:
  length_scale: ambient        # critical | target | ambient  -> defines d_e,ref
  mass_ratio: 100.0
  charge_state: 1
laser:
  wavelength_um: 1.053         # pins n_cr and d_e,cr = lam0/2pi
  intensity: 1.0e18            # W/m^2
  direction: z
  inject_side: hi
  incidence_angle_deg: 0.0
  Z_eff: 5.0
  coulomb_log: 5.0             # NOT physical -- a knob; see hazard 4
  temperature_mode: local      # local | fixed  (local is the default and the right one)
  temperature_floor_theta: null # defaults to the target's initial theta
  intervals: 10                # also how a FINITE PULSE is expressed: start:stop:period
  ray_cfl: 0.25                # NOT asymptotic for turning-point problems -- see gate G4
  profile_intervals: 0         # per-cell (coords, n_e, H, P_abs) dump; analyse step 0
  beam:
    profile: uniform           # uniform | gaussian | super_gaussian
    waist_de: null
    order: null
    center_de: null
    rays_per_cell: 1
    focus_de: null             # converging beam; overrides incidence_angle
plasma:
  target:
    density_over_ncr: 1.5
    thickness_de: 40
    scale_length_de: 30        # coronal ramp L_n on the laser-facing side
    theta_e_init: 1.0e-4
    theta_i_init: 1.0e-6
    shape: planar              # planar | curved | finite_width (2D, via the density parser)
  ambient:
    density_over_ncr: 0.06     # null => vacuum (Phase 1)
    theta_e: 5.0e-3
    theta_i: 5.0e-5
field:
  orientation: perpendicular   # perpendicular | none
  vA_over_c: 0.003             # or B0_tesla
geometry:
  dims: 1
  normal_axis: z
  domain: {lo_de: -1000, hi_de: 600, transverse_halfwidth_de: null}
  dz_over_de: 0.5
  boundary: {lo: open, hi: open, transverse: periodic}
numerics:
  cfl: 0.35
  particle_shape: 2
  max_step: 128000
  ppc: {target: 400, ambient: 48}
diagnostics: {plotfile_intervals, reduced_intervals, field_intervals}
species: {...}
gates:                          # the run's own declared numerical budget, checked by run_checks
  omega_pe_dt_max: 1.2          # at the PEAK compressed density, not the initial one
  dz_over_lambdaD_max: 10       # per region; the target will violate this -- see gate G2
targets: {f_abs_initial, v_p_over_vA, M_A, M_ms}
```

Two schema notes worth arguing about in Phase 0: whether `coulomb_log` should be
`target:`-inverted the way `KinShock2020` inverts collisionality (probably not — here it is
an honest mid-Z stand-in, not a dialled quantity), and whether `intervals` is really the
right place to express pulse duration (it is the only place the operator offers).

### Tooling to build

| Script | Purpose | Phase needed |
|---|---|---|
| `make_inputs.py` | `config.yaml` → deck, `--verify`, `--check` | 0 |
| `run_checks.py` | derived scales + **all numerical gates** (§6) before/after a run | 0 |
| `laser_report.py` | parse `LASERDEP` history + profile dumps → `f_abs(t)`, `E_abs`, `t_s`, `Tlocalfrac` | 0 |
| `plot_ablation.py` | vacuum ablation: plume profiles, `v_p`, `T_e(t)`, energy budget | 1 |
| `tune_shock.py` | fit `v_sh` + front by eye → `shock_fit.yaml` | 2 |
| `make_figures.py` | Schaeffer criteria A–D + `criteria.json` | 2 |
| `phase_space.py` | **the arbiter**: `f(u_z)` upstream/downstream, reflected fraction | 2 |
| `make_movies.py` | density + phase-space movies | 2 |
| `sweep.py` / `plot_sweep.py` | launch + reduce a parameter sweep to scaling fits | 3 |
| `launch.sh`, `run_progress_logger.py` | **already ported and working** | — |

`src/laserprod/`: `units` (λ₀ → `n_cr`, `d_e,cr`, all three length scales, IB coefficient
`K`, absorption depth, `ω_pe dt`, `λ_D`), `config` (load + validate + gates), `deck`
(config → deck; boundary-token map), `io` (plotfile/reduced-diag readers, `LASERDEP`
parser), `metrics` (piston/shock kinematics, Schaeffer criteria — port from
`kinshock.metrics`), `plotting`.

---

## 4. Phase overview

| Phase | Question | Runs | Cost estimate |
|---|---|---|---|
| **0** | What boundary conditions and geometry are even admissible? | 5 short | hours |
| **1** | Does the laser ablate a target correctly, in 1D and 2D? | 4 | ~1 day |
| **2** | Does the piston shock an ambient — unmagnetized (control) and magnetized? | 4 | ~2–3 days |
| **3** | How do `f_abs`, `E_abs`, `v_p`, `M_ms` depend on laser power and geometry? | ~30 short | ~3–4 days |

Cost estimates are order-of-magnitude, anchored on `run_laser_shock` (6400 cells,
4 species, 48–100 ppc, 128 000 steps ≈ 35 min at 8 threads) and scaled by cells × ppc ×
steps; 2D multiplies by the transverse cell count. They are to be replaced by measured
numbers from the progress logs as the campaign proceeds.

---

## 5. Phase 0 — boundary conditions and geometry (**the first step**)

**Why first.** Three of the five inherited hazards are boundary or geometry hazards, and
the prior work lost two whole deck versions to them. Nothing downstream is interpretable
until the box is right.

### 5.0 The problem, stated precisely

A laser-ablation run wants **three incompatible things** at once:

1. A **uniform applied `B₀`** across the domain. In `KinShock2020` this worked with `pec`
   field boundaries; `absorbing` (Silver–Mueller) is **incompatible** with the div-B
   cleaner that runs when a background B is set (`kinshock.config.validate` warns on
   exactly this).
2. **Absorbing particle boundaries**, so the runaway rarefaction ion front leaves instead
   of wrapping. Periodic *fields* force periodic *particles*, so periodic is disqualified
   the moment a free expansion exists.
3. A **laser injection face**. Rays launch from `inject_side` of the propagation axis, so
   that face is simultaneously a field boundary, a particle boundary, and the beam
   aperture. Nothing in the operator's documentation says what happens when plasma sits on
   that face, or when the plume flows out through it.

`KinShock2020`'s boundary-token map is the starting point (`kinshock.deck._BC_MAP`):

| config name | field token | particle token |
|---|---|---|
| `periodic` | `periodic` | `periodic` |
| `reflecting` / `symmetry` | `pec` | `reflecting` |
| `open` | `pec` | `absorbing` |
| `absorbing` | `absorbing_silver_mueller` | `absorbing` |

`open` = `pec` fields + absorbing particles is the combination that worked with a
background B there. **Phase 0's job is to establish that it works here too, and to
characterise what it costs.**

### 5.1 Deliverable before any run

Finalise the config schema (§3) and build `make_inputs.py` + `run_checks.py` +
`laser_report.py`. The boundary-token map is ported, but `transverse` faces and the
`inject_side` interaction are new and get their own map entries.

**Three questions settled by reading the operator source — RESOLVED 2026-07-28:**

1. **A finite pulse IS expressible.** `laser_deposition.intervals` is parsed by
   `ablastr::utils::text::IntervalsParser` (`LaserDeposition.cpp:255`), so
   `start:stop:period` works and pulse duration is a first-class knob. H4 can therefore be
   tested by varying duration at fixed `I₀`, without confounding it with the observation
   window. The config exposes it as `laser.intervals`.
2. **Rays launch EXACTLY ON the injection face**, not one cell inside it:
   `c0[m_axis] = m_inject_hi ? phi[m_axis] : plo[m_axis]` (`LaserDeposition.cpp:916`), with
   transverse positions at sub-cell centres. So the boundary cell's plasma is traversed and
   absorbs from the first RK4 step, and `deposit` clamps its index into the valid box.
   Nothing special happens at the face — which means **the beam is absorbed in whatever
   plasma has reached the launch plane**. Physically right (a real beam crosses its own
   blow-off), but it makes the drive a boundary quantity once the plume arrives, which is
   what `P0_bc_inject` measures. `config.validate` now warns when a target's corona is
   optically significant (> 10⁻³ n_cr) *at* the injection face.
3. **The exit-boundary overshoot is confirmed, and its mechanism is now known.** The
   domain-exit test
   (`if (c[m_axis] < plo[m_axis] || c[m_axis] > phi[m_axis]) break;`) happens **after** the
   step's deposit, so the ray always takes one full RK4 arc-length step past the far
   boundary and deposits it into the clamped final cell — energy is *created*, not
   misplaced. The affected cell is the last one at the **far** (non-injection) face. In the
   upstream slab tests this inflated total absorption by ≤ 0.04 % while reading +24.9 % high
   in that one cell. **Still to do**: quantify it for a target-near-boundary geometry, then
   decide whether to clip the last step upstream (fixing it is in scope — finding a bug is a
   valid outcome of a test campaign).

### 5.2 The runs

| Run | Setup | Question |
|---|---|---|
| `P0_bc_periodic` | 1D, target + vacuum, all-periodic. **Deliberate reproduction of the known failure.** | Confirm the runaway front wraps, and measure how fast — the control that makes every later choice defensible. |
| `P0_bc_open` | Same, `boundary: {lo: open, hi: open}`, `B₀ = 0` | Do the fast ions leave cleanly? What does the `pec` field wall reflect back — spurious E, charge accumulation, sheath at the wall? |
| `P0_bc_open_B` | Same + perpendicular `B₀` | Does `pec` + a uniform applied `B₀` + div-B cleaning coexist, as in `KinShock2020`? Is `B` uniform to machine precision at t = 0 and free of wall artifacts later? |
| `P0_bc_inject` | 1D, `inject_side` = the face the plume flows *out* of, vs the opposite face | Does the beam aperture care that plasma is leaving through it? Is `E_abs` unchanged? |
| `P0_bc_2d` | 2D, transverse `periodic` vs transverse `open` | Transverse periodicity makes the drive *exactly planar* (and a uniform beam infinite). Establish both, and the box width at which `open` stops mattering. |

All are short (≲ 2000 steps): these are boundary questions, not physics questions.

### 5.3 Pass criteria

- The all-periodic failure is reproduced and quantified (so it is never re-litigated).
- One boundary configuration is identified in which (a) fast ions are absorbed, (b) `B₀` is
  uniform and stable, (c) `E_abs` is insensitive to the choice, and (d) no wall sheath
  intrudes into the region where the shock will later form. That configuration becomes the
  **default** in the config schema, with the runners-up documented as rejected and why.
- The exit-boundary overshoot is quantified for a target-near-boundary geometry.
- `run_checks.py` reports every gate in §6 correctly on a real run.

**If no configuration satisfies all four**, that is a genuine finding and the plan forks:
either use a large sacrificial buffer region (costly) or accept a documented artifact with a
stated validity window in time. Decide it here, in writing, not later under pressure.

---

## 6. The numerical gates (applied to every run, all phases)

Not a phase — a checklist `run_checks.py` enforces. Each gate exists because it was
*violated* somewhere in the prior work.

| | Gate | Threshold | Why |
|---|---|---|---|
| **G1** | `ω_pe dt` at the **peak compressed** target density | < ~1.2 (hard < 2) | Hazard 2. `cfl = 0.75` → 1.91 initially, 2.43 after self-compression, and every result past `t ≈ 0.1 ω_ci0⁻¹` was a measurement of the resulting instability. The gate must extrapolate the compression, not read t = 0. |
| **G2** | `dz/λ_D` per region | ambient ≲ 7; target **will** be ~250 when cold | Finite-grid heating. `KinShock2020` documents `dz/λ_D ≈ 7` as already marginal, and halving resolution blew a laser run up. **The cold near-critical target is under-resolved by ~250×** — vastly worse than the ambient, and unavoidable at one uniform grid. G2 is therefore not a pass/fail but a *measurement*, made meaningful by G3. |
| **G3** | **Laser-off control** for every physics run | spurious `ΔE` ≪ `E_abs` | The only honest way to separate grid heating from laser heating given G2. An identical deck with the laser disabled, run for the same duration. Non-negotiable for Phase 1 and 2 headline results. |
| **G4** | `ray_cfl` convergence | non-monotonic; default 0.25 sits near a 2.5 % excursion | Documented upstream: the default is **not** in the asymptotic regime for turning-point problems (uniform slabs are exact at any `ray_cfl`). Any run whose target has an interior critical surface needs a `ray_cfl` check. |
| **G5** | ppc for `temperature_mode = local` | several hundred/cell for sub-% `P_abs` | `T^{-3/2}` is convex, so per-cell noise biases absorption **high**: ~3 % at 25 ppc, < 0.1 % at 800. The target needs high ppc; the ambient does not. Report `Tlocalfrac`. |
| **G6** | Energy closure | tracer `E_abs` vs (particle KE + field energy) gain | The `LASERDEP` accounting is immune to grid heating; the particle energy is not. Their difference is the grid-heating budget **only when boundary losses are small** — absorbed particles carry energy out and WarpX does not report it, so at 5.8 %/17 % particle loss the raw gap read +218 %/+235 % (RESULTS 2026-07-28). Always quote the loss fraction beside it. Measured +0.55 % at 0 % loss, so grid heating is *not* significant at `dz/λ_D = 61`. |
| **G7** | `dz` unchanged when economising | — | Savings come from ppc, domain and duration. Coarsening `dz` at fixed `d_e` raised `dz/λ_D` to 14 and blew a run up (ambient to `u ~ 0.15 c`, `B_y/B₀` to 82). The free parameter is `dz/λ_D`, not resolution in `d_e`. |

---

## 7. Phase 1 — laser ablation of a target into vacuum

**Question.** Does the operator, coupled to PIC, ablate a target the way ablation physics
says it should — and does 1D describe the 2D reality?

No ambient, no `B₀`: the cleanest possible coupling test, and the one where the ablation
scalings (H1–H3) can be measured without a shock confusing them.

### 7.1 `P1_vac_1d` — the reference ablation

Target at ~1.5 `n_cr` with a coronal ramp, vacuum on both sides, normal incidence, the
Phase-0 boundary configuration, high target ppc (G5).

Measure:
- `f_abs(t)` from ~90 % initial down through the **shutoff**, and `t_s`.
- `E_abs` and where it goes: target electron thermal energy, ion directed energy, energy
  lost through the boundaries. Close the budget (G6).
- The **deposition profile** vs the density profile: is absorption in the coronal gradient,
  at the critical surface, or both, and does the turning point sit where WKB says?
  (Analyse the **step-0** dump — later dumps drift as the kicks move electrons.)
- `T_e(t)` in the target, against H1's `T_e,shutoff`.
- The isothermal rarefaction: does `n(z,t)` follow the self-similar
  `n ∝ exp(−z/c_s t)` profile Schaeffer's Eq. 1 is built on, and is
  `v = (c_s/2)[1 − ln(n/n_t)]` recovered?
- `v_p` from the ion front and the bulk, against H3's `α c_s`.
- The runaway front: how fast, how much mass, and how much of `E_abs` it carries. This is
  the population Phase 0's boundary must absorb.

Paired with `P1_vac_1d_off` (G3, laser disabled) and a `ray_cfl` check (G4).

### 7.2 `P1_vac_2d` — the same target in 2D

Same target and laser, 2D, transverse extent from the Phase-0 finding. Two sub-cases:

- **Uniform beam, transverse periodic** — exactly planar. Should reproduce `P1_vac_1d` on
  axis to within noise. *This is the 1D↔2D validation, and it must pass before any 2D
  physics claim.* A discrepancy here is a bug or a boundary artifact, not physics.
- **Finite Gaussian spot, `beam_waist` scanned** — the real 2D physics: lateral rarefaction,
  a 2D plume, and rays refracting in *transverse* density gradients (which the 1D run cannot
  have). Measure the on-axis `v_p` degradation vs `w₀/ρ_i0` and test **H5**. Also: does the
  finite spot bend rays out of the plume, reducing `f_abs` below the 1D value?

`rays_per_cell` convergence belongs here — a structured beam on a structured plume is where
sub-cell ray sampling first matters.

### 7.3 Pass criteria

1D and 2D-planar agree on axis; the energy budget closes (G6); the deposition profile sits
where WKB predicts; `f_abs(t)`, `t_s`, `T_e,shutoff` and `v_p` are measured with the
laser-off control subtracted; H1 and H3 are either confirmed with fitted coefficients or
falsified with a stated replacement.

---

## 8. Phase 2 — the piston expanding into ambient plasma

**Question.** Does the ablation piston couple to an ambient plasma, and does a magnetized
ambient produce a *shock* by Schaeffer's criteria?

The ambient now sits on both sides of the target — **there is no vacuum gap**, which the
prior work established twice over (a gap gives the runaway front a path to wrap through and
pollute the upstream, and no gap is large enough). The ambient must also be tenuous enough
that the beam crosses it without pre-heating the upstream: at 0.06 `n_cr` the traverse cost
~0.04 % of the beam, which is the standard to hold.

### 8.1 `P2_unmag` — the unmagnetized control (`B₀ = 0`)

Schaeffer's own negative control. Expect: ambient ions accelerated by the ambipolar/in-plane
`E_z`, **no magnetic compression, no strong ion heating, no secondary compression, no
shock**. Interpenetrating flows only.

This run's value is calibration: it shows what a *non*-shock looks like in exactly this
diagnostic pipeline. Given that a fast magnetosonic pulse was once mistaken for a shock,
having the negative control in hand *before* the magnetized run is a deliberate ordering.

### 8.2 `P2_mag` — the magnetized perpendicular run

`B₀` along `x`, perpendicular geometry, the `run_laser_shock` regime as the starting point —
but **retargeted**, since that regime demonstrably fails to shock. The prior work's own
diagnosis: the piston reached only ~1 `v_A` while `v_ms = 1.15 v_A`, i.e. the piston was
*subsonic*, so no shock could form at those parameters however long the run. The identified
fix was to lower `B₀` to ~100 T *and* the ambient electron temperature to `θ = 5×10⁻⁴` —
because the ambient sound speed was 0.57 `v_A` and dominates `v_ms` once `B₀` drops, so
`B₀` alone buys little. Target `M_ms ≈ 2.6`.

Full Schaeffer analysis: seven criteria, three timescales, compression ratios, ramp scales,
`F` and `G`. **`phase_space.py` runs first, and if there is no ion reflection the word
"shock" does not appear in the run README.**

Expected difficulty, stated in advance: **scale separation**. The laser wants a
near-critical target; the magnetized shock wants a tenuous ambient; one uniform grid must
resolve both, and at 25:1 contrast the two `d_e` already differ 5×. This is exactly why Fox
2018 and PSC prescribe a heater instead of a laser. Practical levers, in the order the prior
work ranked them: thicken the target (coupled energy scales with areal electron number),
raise `Z_eff·lnΛ` (**in small steps** — 25 → 91 overshot by 16×, producing a 0.06 c piston
that crossed the domain in a fraction of a gyroperiod), lower `B₀` (diminishing below
~75 T, where the ambient sound speed floors `v_ms`).

### 8.3 `P2_mag_2d`

The magnetized run in 2D, exploiting the §2.1 finding that `ρ_i0 ≈ 65 d_e,amb` makes a
transverse extent of ~1 `ρ_i0` affordable. Quasi-1D (transverse periodic, uniform beam)
first, to confirm 1D; then a finite spot, to ask whether a real focal spot can drive a shock
at all, or whether lateral rarefaction kills the piston before `t*₂`.

### 8.4 Pass criteria

The unmagnetized control shows no magnetic compression and no reflected ions. The magnetized
run either satisfies criteria 1–6 (a shock **precursor**) and then 7 (a **shock**) with the
timescales in the right order — or it does not, in which case the deliverable is a
quantitative statement of *which criterion fails and by how much*, plus the parameter change
that would fix it. A negative result here is a real result; the retracted claim shows the
alternative is worse.

---

## 9. Phase 3 — sweeps: laser power and geometry vs the shock parameters

**Question.** What is the map from laser parameters to shock parameters?

Each sweep is a set of short runs (Phase 1-style vacuum ablation where the ablation scalings
are the target; Phase 2-style with ambient where `M_ms` is the target), reduced by
`plot_sweep.py` to fitted exponents and compared against H1–H5. Sweeps live under
`studies/` (heavier experiments that launch WarpX) with a runner script, following
`KinShock2020/studies/`.

### 9.1 Phase 3A — power (`studies/sweep_intensity/`)

| Sweep | Range | Predicts / tests |
|---|---|---|
| `I₀` | 10¹⁷ … 10²¹ W/m², ~5 points/decade | **H2, H4.** `E_abs` flat in `I₀`? `t_s ∝ 1/I₀`? Is there an optimum `I₀` maximising `M_ms` at `t*₂` — high enough for a supercritical piston, low enough that the drive outlasts a gyroperiod? |
| `Z_eff·lnΛ` | 25 … 91, **small steps** | **H1, H3**, and the 16× vs 2.4× discrepancy. Where does the static-shutoff picture break? |
| λ₀ | 1.053, 0.527, 0.351 µm | `n_cr ∝ λ₀⁻²`, so this rescales the entire absolute density map at fixed dimensionless setup — the cleanest test that the laser's role really is just to pin the scale. |
| target thickness `w_t` | 10 … 160 `d_e` | **H3**: `v_p` invariant, momentum ∝ `w_t`. If `v_p` moves, H3's energy-partition assumption is wrong. |
| coronal `L_n` | 5 … 60 `d_e` | Absorption region and turning-point depth; where the energy lands relative to the mass. |
| pulse duration (via `intervals`) | continuous vs `t_s`-matched vs short | **H4** directly, decoupled from `I₀`. Contingent on the §5.1 finding about `intervals`. |

Note on interpretation: "power" enters this operator only as `intensity` (W/m²) and the
`intervals` gate — there is no temporal pulse shape, and no focal-spot power integral except
through `beam_profile` × `beam_waist`. **A "laser power" sweep is therefore an
intensity × spot-area × duration sweep**, and those three must be separated deliberately
rather than varied together.

### 9.2 Phase 3B — geometry (`studies/sweep_geometry/`)

| Sweep | Range | Tests |
|---|---|---|
| dimensionality | 1D vs 2D-planar vs 2D-spot | **H5**; the cost of the 1D approximation. |
| `beam_waist` | 0.2 … 3 `ρ_i0` | **H5** quantitatively: the `w₀/ρ_i0` at which the shock survives. The single most experimentally relevant number in the project — real experiments have finite spots. |
| `beam_profile` | uniform / gaussian / super-gaussian(m) | Does a flat-top spot beat a Gaussian at equal total power? |
| `incidence_angle` | 0 … 60° | Turning point moves to `z_crit cos²θ₀`, so energy is deposited further out in the corona. Better or worse coupling to the piston? (Requires 2D.) |
| `beam_focus` (f/#) | converging vs parallel | Whether focusing geometry changes coupling once the beam is inside a refracting plume. |
| target shape | planar / curved / finite-width foil | Via the density parser expression. A curved target focuses or defocuses the plume; a finite-width foil lets the plume expand around it. |
| `inject_side` | plume-facing vs opposite | Interacts with Phase 0's finding; also the difference between "laser and shock on the same side" and opposite sides. |

### 9.3 Deliverable

A single **scaling summary**: fitted exponents for `f_abs`, `E_abs`, `t_s`, `T_e,shutoff`,
`v_p`, `M_A`, `M_ms` against `I₀`, `Z_eff lnΛ`, λ₀, `w_t`, `L_n`, `w₀`, θ₀ — each labelled
confirmed / falsified against H1–H5, with the working regime for a laser-driven
collisionless shock stated as a box in parameter space. That box, plus the reason for its
boundaries, is the project's headline output.

---

## 10. Risks and open questions

1. **The regime may not exist.** The near-critical-target / tenuous-ambient scale separation
   on one uniform grid may simply not admit a strong laser-driven shock at affordable cost.
   If Phase 2 and 3A converge on that, the deliverable is the **quantified impossibility
   argument** — which is genuinely useful, since it is the physics justification for why PSC
   and Fox 2018 prescribe a heater instead. It should be written up as such, not as a
   failure.
2. **Grid heating in the cold target (G2, ~250× under-resolved)** may contaminate `T_e`,
   which feeds back into `K ∝ T_e^{-3/2}` and hence into the absorption itself. G3's
   laser-off control bounds it; if the bound is not comfortably small, `temperature_floor`
   and `min_macroparticles_per_cell` become physics parameters rather than guards, and that
   must be stated.
3. **`coulomb_log` is a fixed input**, so the model is not fully self-consistent — though
   the dependence is logarithmic, not a power law. Worth restating whenever a `Z_eff·lnΛ`
   result is quoted.
4. **`ray_cfl` non-asymptoticity (G4)** could quietly shift turning-point deposition by a
   few percent in exactly the runs that matter (interior critical surface).
5. **The exit-boundary overshoot creates energy** (§5.1). Small upstream, possibly not small
   for a target near the boundary. If Phase 0 finds it matters, fixing it upstream in the
   operator is in scope — this project is a *test* of the module, and finding a bug is a
   valid outcome.
6. **`_off` controls double the compute cost** of every headline run. That is the price of
   G2 and is budgeted, not optional.

---

## 11. Checklist

**Phase 0 — boundaries and geometry**
- [x] Finalise `config.yaml` schema; decide the `length_scale` default and document the trap
- [x] `src/laserprod/{units,config,deck,io,plotting}` + `scripts/make_inputs.py`
      (+ `--verify`, `--check`) — dimension-general 1D/2D from one code path
- [x] `scripts/run_checks.py` implementing gates G1–G7, with a pre-run figure
- [x] `scripts/laser_report.py` (`LASERDEP` history + profile dumps)
- [x] `scripts/compare_runs.py` — cross-run overlay, the actual Phase-0 evidence
- [x] `tests/` — 71 checks: units identities, every gate firing on a violating config,
      per-run README presence, deck round-trip, boundary-token consistency
- [x] Read the operator source: `intervals` pulse gating (works), injection-face
      behaviour (rays launch ON the face), exit-boundary overshoot (mechanism confirmed) — §5.1
- [x] `P0_bc_periodic` — wrap failure reproduced: particle number **exactly** constant
- [x] `P0_bc_open`, `P0_bc_open_B`, `P0_bc_inject`, `P0_bc_2d` — all complete
- [x] **Decision recorded**: `open` (pec fields + absorbing particles) on the propagation
      axis, periodic transverse. B₀ verified uniform to **ratio 1.000000** against
      `B₀²/(2µ₀)L` with pec boundaries; rejected alternatives and reasons in RESULTS
      2026-07-28
- [x] Quantify the exit-boundary overshoot (`studies/exit_overshoot/`): the dominant
      per-cell error is cell-to-cell ALIASING from endpoint-lumped deposition (rms 0.7 %
      at ray_cfl 0.05, 3.6 % at 0.25, 20 % at 1.0), not the boundary; the total absorbed
      is LOW by 0.1-0.3 % for ray_cfl <= 0.25, so no net energy creation was seen and the
      upstream +24.9 %/energy-created description is not reproduced. Rules: discard the
      boundary cell, keep ray_cfl <= 0.25 for profiles, energetics are safe to 0.3 %.
- [x] `P0_bc_2d_open` (transverse open) complete: interior bit-identical to the planar
      run at t=0; the axis stays clean to +-16.5 of 20 d_e; but 30.8% of particles and
      42.9% of KE leave in 0.10 gyroperiods, and the outer TWO columns read 0.365x/0.861x
      density (particle_shape=2 losing the periodic wrap), which flips a 1.5 n_cr target
      to 0.55 n_cr underdense there
- [ ] **Phase-2 blocker found in Phase 0 -- now a box-size requirement.** With `open`
      walls the ambient drains at ~6.7 %/ps axially (200 d_e) and ~40 %/ps transversely
      (+-20 d_e). Confining the ambient ELECTRON thermal excursion over 2.5 gyroperiods
      needs L >~ v_th,e t = 2400 d_e per open direction -- unaffordable. So Phase 2 must
      keep the transverse direction PERIODIC (quasi-1D, as Schaeffer did with 12
      transverse cells), or use a colder ambient, or injecting/thermal boundaries. Not
      solvable by enlarging the box.

**Phase 1 — vacuum ablation**
- [ ] `P1_vac_1d` + `P1_vac_1d_off` (G3) + `ray_cfl` check (G4)
- [ ] Energy budget closes (G6); deposition profile vs WKB at step 0
- [ ] `f_abs(t)`, `t_s`, `T_e,shutoff`, `v_p` measured; H1/H3 confirmed or replaced
- [ ] Self-similar rarefaction / Schaeffer Eq. 1 recovered
- [ ] `P1_vac_2d` planar reproduces 1D on axis
- [ ] `P1_vac_2d` finite spot: `w₀` scan, `rays_per_cell` convergence, H5

**Phase 2 — ambient**
- [ ] `scripts/tune_shock.py`, `make_figures.py`, `phase_space.py`, `make_movies.py`
- [ ] `P2_unmag` (+`_off`) — negative control, calibrates the pipeline
- [ ] `P2_mag` (+`_off`) retargeted for `M_ms ≈ 2.6`; seven criteria, three timescales
- [ ] Phase space checked **before** any shock claim
- [ ] `P2_mag_2d` quasi-1D, then finite spot

**Phase 3 — sweeps**
- [ ] `studies/sweep_intensity/` — `I₀`, `Z_eff lnΛ`, λ₀, `w_t`, `L_n`, duration
- [ ] Resolve the 16× vs 2.4× `Z_eff lnΛ` discrepancy
- [ ] `studies/sweep_geometry/` — dims, `w₀`, profile, θ₀, focus, target shape, inject side
- [ ] Scaling summary: fitted exponents, H1–H5 verdicts, the working parameter box

**Throughout**
- [ ] Every run dir has a `README.md` before it is launched (`launch.sh` enforces)
- [ ] `RESULTS.md` dated entry per substantive run or finding
- [ ] Gates G1–G7 reported for every run
