# RESULTS.md — LaserProdShock lab notebook

**One dated entry per substantive run or finding.** This is how context survives between
sessions; read it first to learn current state. Newest entries at the bottom.

Conventions: quote densities in `n_cr`, lengths in `d_e,ref` (say which), speeds in `c` or
`v_A` (say which), times in `ω_ci0⁻¹` for shock runs and `ω_pe⁻¹`/ps for ablation runs.
Report the gates (G1–G7, `TEST_PLAN.md` §6) for every run. **Retractions get their own
dated entry** — do not silently edit an earlier one.

---

## 2026-07-28 — Project created; inherited state

Repository scaffolded as a sibling of `KinShock2020`, following its architecture: config as
single source of truth, `scripts/launch.sh` as the only launcher, sidecar progress logger,
per-run `README.md` (newly enforced by `launch.sh`).

**Built and working**: `scripts/launch.sh` (ported; now picks `warpx.1d`/`warpx.2d` from
`geometry.dims`, and refuses to launch a run with no `README.md`),
`scripts/run_progress_logger.py` (ported; additionally parses the operator's `LASERDEP`
lines and reports `Pabs` as a fraction of its running peak, so the **self-limiting
absorption shutoff** is visible live).

**Not built**: everything else — `src/laserprod/*`, `make_inputs.py`, `run_checks.py`,
`laser_report.py`, `phase_space.py`, `tune_shock.py`, `make_figures.py`, `make_movies.py`,
`sweep.py`. That is Phase 0 (`TEST_PLAN.md` §5.1, §11).

**Inherited from `warpx-cda/laser_deposition/`** (not to be re-derived — `TEST_PLAN.md`
§1.1). The operator is validated against analytic IB/WKB theory to 0.02–1.6 % across five
CI tests plus eight research-scale accuracy runs: uniform-slab deposition profile exact to
0.000 % in cells 2…510, ramp profile overlaying the closed form across 8 decades with the
turning point at the analytic position, `z_m` tracking `z_crit cos²θ₀` to ~1 cell out to
60°, and a coefficient audit flat to 1e-5 over a 275× range of `K` (exponents
2.018 / 0.9999 / 0.9999 / −1.4999 / 2.028 on `n_e`, `Z_eff`, `lnΛ`, `T_e`, `I`). Local-`T_e`
mode tracks an imposed 10× ramp to 0.05 %. PSC cross-validation (Test C) is blocked
upstream: Hyder et al.'s PSC ray-tracing module is not public.

**Three inherited open issues**, carried into this project's gates:
1. **Exit-boundary overshoot** — the ray takes a partial extra arc-length step past the far
   boundary and *creates* energy in the final cell (+24.9 % at default `ray_cfl`). ≤ 0.04 %
   of total absorption upstream, but a vacuum-ablation target sits near that boundary.
2. **`ray_cfl = 0.25` is not asymptotic** for turning-point problems (non-monotonic
   convergence, default near a 2.5 % excursion). Uniform slabs are exact at any `ray_cfl`.
3. **`coulomb_log` is a fixed input**, so the model is not fully self-consistent — though
   logarithmically, not as a power law.

**The retracted shock claim** (`warpx-cda/laser_deposition/run_laser_shock/`, RESULTS there
2026-07-27) is the campaign's motivating result and is treated as established:
compression ~2 in `B` and `n_e` with a real diamagnetic cavity and a front at 2.63 `v_A`
were **not** a shock. Phase space showed 0.00 % ion reflection, upstream/downstream
`f(u_z)` differing only by a −0.83 `v_A` shift and 0.56 → 0.72 `v_A` broadening, and a
piston at only ~1 `v_A` — *slower than the compression it had launched*, and subsonic at
`v_ms = 1.15 v_A`. It was a freely-propagating fast magnetosonic pulse from a genuine
laser-driven ablation. Hence the third project rule: **phase space decides what is a
shock.** The identified fix, to be the starting point for `P2_mag`: lower `B₀` to ~100 T
*and* the ambient electron temperature to `θ = 5×10⁻⁴` (the ambient sound speed was
0.57 `v_A` and dominates `v_ms` once `B₀` drops, so `B₀` alone buys little) → `M_ms ≈ 2.6`.

**Also inherited as hard constraints**: `ω_pe dt < 2` is the binding stability limit and the
grid CFL cannot see it (`cfl = 0.75` → `ω_pe dt = 1.91` initially, 2.43 after the target
self-compressed, 21× spurious energy growth, everything past `t ≈ 0.1 ω_ci0⁻¹` invalid);
periodic fields force periodic particles, so a 0.20 c runaway ablation front wraps and
pollutes the upstream and **no vacuum gap is large enough**; `Z_eff·lnΛ` 25 → 91 coupled
**16×** more energy. See `CLAUDE.md` for the full list.

**Derived for this project** (`TEST_PLAN.md` §2.1, `OVERVIEW.md` §3): at λ₀ = 1.053 µm,
`n_cr = 1.005×10²⁷ m⁻³` and `d_e,cr = c/ω₀ = λ₀/2π = 0.1676 µm` exactly. Two consequences
worth having on record:
- **Schaeffer's Table I densities are natural for a 1 µm laser** — the ablation density
  6×10²⁰ cm⁻³ is 0.6 `n_cr`, the upstream 4.8×10¹⁸ cm⁻³ is 0.0048 `n_cr`. The absolute
  scale is not the obstacle; the ~125:1 contrast is.
- **`ρ_i0 ≈ 65 d_e,amb`** for the `run_laser_shock` parameters (`B₀ = 74.7 T`,
  `ω_ci0⁻¹ = 7.61 ps`, `v_p = 0.0196 c` → `ρ_i0 = 44.7 µm`), versus ~1040 `d_e` in
  `KinShock2020`'s `R1_*`, because `B₀` is large relative to the density. A transverse
  extent of ~1 `ρ_i0` is therefore only ~65 cells at `dz = 0.5 d_e` — **a genuinely 2D
  magnetized laser-driven shock is affordable here**, which is why 2D is in the plan as
  physics rather than as a smoke test.
- Corollary flagged as gate G2: the cold 1.5 `n_cr` target is Debye-under-resolved by
  **~250×** (vs ~7 for the ambient) at `dz = 0.5 d_e,amb`. Unavoidable on one uniform grid
  with no AMR, which is why the **laser-off control (G3)** is mandatory for every headline
  run rather than optional.

Next: Phase 0 (`TEST_PLAN.md` §5) — finalise the config schema, build
`units`/`config`/`deck` + `make_inputs.py` + `run_checks.py` + `laser_report.py`, then the
five short boundary runs, ending in a recorded decision on the default boundary
configuration.

---

## 2026-07-28 — Phase 0 tooling built; boundary runs launched; three source questions closed

### Tooling (all of `TEST_PLAN.md` §5.1 except the exit-overshoot measurement)

`src/laserprod/{units,config,deck,io,plotting}` plus `scripts/{make_inputs,run_checks,
laser_report,compare_runs}.py`. **71 tests pass** (`tests/test_units.py`,
`test_gates.py`, `test_structures.py`). pytest was not installed anywhere on this
machine — `KinShock2020/tests/` had never been runnable — so it was added to the
`physics` env. Note the scripts import matplotlib/yaml from base anaconda but **yt lives
only in the `physics` env**, so plotfile-reading tools (Phase 1+) must run under
`/opt/anaconda3/envs/physics/bin/python`.

**Dimension-general by construction.** 1D and 2D come out of one code path: every
list-valued input (`amr.n_cell`, `prob_lo/hi`, the four boundary-token lists,
`num_particles_per_cell_each_dim`, `beam_center`, `beam_focus`) is built from
`units.axis_names(dims)`, so 2D emits WarpX XZ ordering `(x, z)` with the propagation
axis last. `dz` is set by `dz_over_de` and the transverse cell by `dx_over_dz`;
`timestep()` applies the full Yee CFL `dt = cfl/(c√Σ1/dx²)`, which is why a 2D deck can
use a nominally larger `cfl`. Verified: the 2D deck renders `amr.n_cell = 80 400`,
`boundary.field_lo = periodic pec`, `ppc = 4 4`, and `B0` on **y** (out of the XZ plane —
the right choice for a 2D perpendicular shock, and why the 1D runs use y too).

**The gates reproduce the upstream failure and its fix to three digits.** At
`cfl = 0.75`, `dz = 0.5 d_e,ambient`, target 1.5 n_cr, G1 gives `ω_pe dt = 1.875` (deck:
1.91) and FAILs. At `cfl = 0.35` it gives 0.875 initially, **1.07** at the 1.49×
compression the target actually reached (deck: 1.07) and puts the hard limit of 2 at
**7.837 n_cr** (deck: 7.84). That agreement is what makes G1 a check on physics rather
than on an arbitrary threshold, and it is pinned in `test_gates.py`.

**Length-unit cost, now quantified.** All five P0 runs use `length_scale: critical`
(`d_e,cr = λ₀/2π = 0.1676 µm`) so their geometry is comparable and vacuum runs need no
ambient to reference. That is **4× finer than `d_e,amb`**, hence 4× smaller `dz` *and*
`dt` — 16× the cost for the same physical box — but it improves both gates by the same
factor: G1 = 0.214 rather than 1.875, and `dz/λ_D`(cold target) = **61 rather than 245**.
So the "~250× Debye-under-resolved" concern recorded on 2026-07-28 above is specific to
ambient-referenced `dz`; at critical-referenced `dz` it is 61. Phase 2 will switch to
`ambient` for gyro-scale boxes, where cost dominates.

### Three source-code questions closed (`TEST_PLAN.md` §5.1)

1. **A finite pulse is expressible.** `laser_deposition.intervals` is an
   `IntervalsParser` (`LaserDeposition.cpp:255`), so `start:stop:period` gates the drive.
   H4 can be tested by varying duration at fixed `I₀`.
2. **Rays launch EXACTLY ON the injection face** —
   `c0[m_axis] = m_inject_hi ? phi[m_axis] : plo[m_axis]` (`:916`), transverse positions
   at sub-cell centres. The boundary cell's plasma absorbs from the first RK4 step, so
   once the plume reaches the launch plane the beam is absorbed *in the plume*.
   `validate()` now warns when a corona exceeds 1e-3 n_cr at the face.
3. **Exit-boundary overshoot: mechanism confirmed.** The domain-exit test
   (`if (c[m_axis] < plo || c[m_axis] > phi) break;`) runs **after** the step's deposit,
   so the ray always takes one full RK4 arc-length step past the far boundary and
   deposits it into the clamped final cell. Energy is *created*. Affected cell = the last
   one at the **far** (non-injection) face. Still to measure for a
   target-near-boundary geometry.

### First results — `P0_bc_periodic` and `P0_bc_open` (both 24 000 steps, 2.35 ps, ~6 min at 4 threads)

**The wrap hazard is confirmed by the cleanest possible signature.** With all-periodic
boundaries the macroparticle count is **exactly** constant, 52418 → 52418
(0.000 % lost): nothing can leave, so the runaway ablation front has nowhere to go but
around. With `open` (pec fields + absorbing particles) the count is flat until
**t ≈ 0.9 ps** and then falls at an accelerating rate, reaching 0.23 % lost by 2.35 ps —
the front arriving and being absorbed. `media/P0_boundary_decision/compare.png`.

**The boundary change did not perturb the drive.** `f_abs(t)` overlays between the two
runs for the whole run, and `E_abs` agrees to 1.5 % (3.774e5 vs 3.719e5 J/m²). So the
pair is a controlled comparison, which is the precondition for reading anything into the
difference.

**Gate G6 closes to ~0.6 %, and that is the important number.** For `P0_bc_periodic` at
2.35 ps: tracer `E_abs = 3.774e5`, particle `ΔKE = 3.724e5`, `ΔE_field = 2865`, sum
`3.753e5` J/m² — a **+0.55 %** gap. `P0_bc_open` closes to +1.45 % (it also loses energy
through the boundary, which is not in the sum). **Grid heating is therefore not
significant here despite `dz/λ_D = 61`**, which is a materially better position than the
plan assumed and reduces (but does not remove) the pressure on the G3 laser-off controls.

**Absorption is self-limiting, measured.** `f_abs` starts at **1.000** (predicted: the
τ = 1 surface sits at z = −29 d_e, i.e. 11 d_e *in front of* the flat top, inside the
coronal ramp) and shuts off to ~0.12 within ~0.1 ps; half-peak shutoff at **19.7 fs**.
`Tlocalfrac` rises 0.54 → 1.000 by 0.45 ps as the plasma heats above the floor.

**H2 needs refinement — a first correction to the plan.** H2 predicts coupled energy
saturates once the drive shuts off. It does **not** here: `f_abs` falls to a **~0.12
floor rather than to zero**, so `E_abs` keeps climbing almost linearly (3.8e5 J/m² by
2.35 ps and still rising). The shutoff is a large drop, not an extinction. `laser_report`
now computes the late/early `dE/dt` ratio and states in the panel title whether the run
saturated, rather than asserting H2 — the first draft asserted it and would have been
wrong on the page.

Still executing: `P0_bc_open_B` (the central question — pec + uniform B0 + div-B
cleaner), `P0_bc_inject`, `P0_bc_2d`. The Phase-0 **boundary decision** needs all five
and is not yet recorded.
