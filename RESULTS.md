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
the front arriving and being absorbed. `media/P0/P0_boundary_decision/compare.png`.

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

---

## 2026-07-28 — Phase 0 complete: all five boundary runs, and the boundary decision

Wall times at 4 threads (machine was at load 28/32 — another user's GPU jobs plus
`KinShock2020/R1_coll`): 6, 6, 9, 8, 22 min; ~51 min total. `make_inputs.py --verify`
reports **OK for all five**, so config → deck → WarpX → `warpx_used_inputs` closes.

| run | dims | axis BC | t / ps | particles lost | f_abs(0) | f_abs(end) | E_abs |
|---|---|---|---|---|---|---|---|
| `P0_bc_periodic` | 1 | periodic | 2.348 | **0.000 %** | 1.000 | 0.147 | 3.774e5 J/m² |
| `P0_bc_open` | 1 | open | 2.348 | 0.227 % | 1.000 | 0.092 | 3.719e5 J/m² |
| `P0_bc_open_B` | 1 | open + B₀ | 2.348 | 5.84 % | 0.283 | 0.069 | 2.155e5 J/m² |
| `P0_bc_inject` | 1 | open + B₀, target near face | 2.348 | 17.05 % | 0.283 | 0.050 | 2.106e5 J/m² |
| `P0_bc_2d` | 2 | open ∥ / periodic ⊥ | 0.791 | 4.61 % | 0.247 | 0.108 | 0.780 J/m |

### THE BOUNDARY DECISION — `open` on the propagation axis, periodic transverse

**`open` = pec fields + absorbing particles is adopted as the default.** The evidence:

1. **Periodic really is disqualified.** Macroparticle count under periodic boundaries is
   *exactly* constant, 52418 → 52418 (0.000 %). Nothing can leave, so the runaway
   ablation front has nowhere to go but around. `open` sheds 0.23 % (vacuum) rising to
   17 % (target near the face) — the absorbing boundary fires.
2. **`pec` fields carry a uniform applied B₀ exactly.** Field energy at t = 0 is
   **74496 J/m²** against the analytic `B₀²/(2µ₀)·L = 74496` — **ratio 1.000000**, with
   B₀ = 74.74 T. The projection div-B cleaner runs without complaint and the run
   completes. This was the central Phase-0 question and the answer is yes.
3. **The boundary does not perturb the drive.** `P0_bc_periodic` vs `P0_bc_open` differ in
   nothing but the boundary: `f_abs(t)` overlays for the whole run and `E_abs` agrees to
   **1.5 %** (3.774e5 vs 3.719e5). So the pair is a controlled comparison.

Rejected, with reasons: **periodic** (1); **`absorbing`/Silver–Mueller** — incompatible
with the div-B cleaner that runs whenever an external B is set, which accepts only
periodic/pec/pmc/neumann and where pmc/neumann would zero the tangential B₀ (not run;
the incompatibility is structural and `validate()` warns on it); **`reflecting`** — a
wall, not an outlet, so it cannot absorb the runaway front.

Transverse: **periodic** for planar work. `P0_bc_2d` ran clean with `periodic pec` tokens
and B₀ out-of-plane on y. The transverse-`open` variant (`P0_bc_2d_open`) remains the
declared follow-up, needed before any finite-spot physics.

### Two findings that change how the tooling reads absorption

**(a) A hot ambient suppresses absorption 3.6×, through the group temperature.**
`f_abs(0)` is **1.000** in the vacuum runs but **0.283** with an ambient — and this is
*not* a 1D/2D effect (1D `P0_bc_open_B` gives 0.283, 2D gives 0.247). The mechanism:
`laser_deposition.species` lists every electron population that is heated **and** that
defines `n_e`; the operator does not let those be separated. So the ambient electrons
must be included for a correct refractive index, and in `temperature_mode = local` their
temperature necessarily enters the *group* `T_e` that `K ∝ T_e^{−3/2}` sees. With the
ambient at θ = 5e-3 against a target at θ = 1e-4, the group θ in the **corona** — where
the τ = 1 surface actually sits — is ~25× the target's, and **K falls 43–129×**.
This is a real property of the model, not a bug, but it is a trap: a target that looks
optically thick in isolation is 3.6× less absorbing once a hot ambient surrounds it.

**(b) The pre-run absorption predictor was wrong twice, and is now right.** It first
evaluated `K` at the target's cold θ everywhere (→ f_abs ≈ 1.000, wrong by 3.6×), and
integrated τ through the **whole flat top** — but the ray turns at
`n_e = n_cr cos²θ₀` and never enters the overdense interior. Fixed to (i) use the
density-weighted group θ per point and (ii) integrate only to the turning point, taking
the double pass `1 − exp(−2τ_turn)`. It now predicts **0.229 vs 0.283 measured** with an
ambient and **0.982 vs 1.000** in vacuum — from ~260 % error to ~19 % and 2 %.

### Gate G6 needs a boundary-loss term — correction to §6

G6 as originally written (tracer `E_abs` vs `ΔKE + ΔE_field`) is **only valid when
boundary losses are negligible**. It closes to **+0.55 %** for `P0_bc_periodic` (0 %
lost) and **+1.5 %** for `P0_bc_open` (0.23 % lost) — confirming grid heating is *not*
significant even at `dz/λ_D = 61`. But it reads **+218 %** for `P0_bc_open_B` and
**+235 %** for `P0_bc_inject`, where 5.8 % and 17 % of particles left carrying their
energy out: total KE actually *falls* (2.448e6 → 2.178e6 J/m²) while the laser adds
2.16e5. That escaped energy is not in the sum and WarpX does not report it directly.
**The gap may only be called a grid-heating budget when the particle-loss fraction is
small**; `compare_runs.py` now prints the loss fraction beside it and its panel title
says so.

### Other numbers worth keeping

- **Self-limiting shutoff, measured**: half-peak at **19.7 fs** (vacuum) and **210 fs**
  (with ambient — slower because absorption starts 3.6× weaker, so the corona heats more
  slowly). `f_abs` floors near 0.05–0.15 rather than reaching zero, so `E_abs` keeps
  climbing — **H2's "coupled energy saturates" is not what happens** (recorded above).
- τ = 1 sits at z = −29 d_e, i.e. **11 d_e in front of** the flat-top face at −40 —
  absorption is in the coronal ramp, as the model says it should be.
- `Tlocalfrac` rises 0.54 → 1.000 by 0.45 ps: the plasma heats above the floor
  everywhere, so G5's floor is not doing the work after the first ~0.5 ps.
- `P0_bc_inject` loses **17 %** of its particles — the plume reaches the injection face
  early, as intended. Its `f_abs(0)` matches `P0_bc_open_B` exactly (0.283), so moving
  the target did **not** change the drive at t = 0; the divergence is later and physical.

Next: the exit-boundary overshoot measurement (the one Phase-0 item left), then Phase 1
(`P1_vac_1d` + its laser-off control, `P1_vac_2d`). Note Phase 1 must decide whether to
keep the ambient out of the heated species list while a vacuum run has no ambient anyway
— finding (a) means the Phase-2 ambient temperature is now a *drive* parameter, not just
an upstream one.

---

## 2026-07-28 (later) — Spatial diagnostics, the exit-overshoot measurement, and three corrections

### New tooling

`scripts/plot_fields.py` ((z,t) streaks of n_e, B_y, E_z + lineouts + a 2D x–z snapshot),
`scripts/phase_space.py` (ion (z,u_z) — the arbiter), and
`laserprod.config.geometry_diagram()`, which renders an ASCII geometry sketch **from the
config** so a run README's diagram cannot drift from what the deck builds
(`make_inputs.py <run> --diagram`; now required in every run README and checked by
`tests/test_structures.py`). 78 tests pass.

Two colour-mapping errors were found and fixed by looking at the output. The B_y/B₀
diverging map was centred on the **data midpoint** (1.9 for a 0.5–3.3 range), so an
undisturbed B/B₀ = 1 rendered blue as if it were already a cavity; it is now centred on
1.0. And E_z was scaled by its extremes, which are grid noise.

### What the pictures show

**The pec wall builds a growing B pile-up, and it is now bounded.** `|B_y/B₀ − 1|` at the
wall goes 0.00 → 0.17 → 0.76 → 1.55 → **2.39** at t = 0, 0.59, 1.17, 1.76, 2.35 ps —
monotonic, not saturating. It penetrates **6–9 d_e (12–18 cells)**, against an interior
99th-percentile deviation of 0.46. **Practical rule: exclude the outer ~10 d_e from
analysis, and re-check the reach for longer runs, because the artifact grows.**
`plot_fields.py` now shades that exclusion band automatically.

**E_z is not usefully resolved at these parameters**: raw rms **4.3×10⁹ V/m**, comparable
to or above the ambipolar field itself, so the map is boxcar-smoothed over 9 cells and the
panel says so. Any E_z-based conclusion here would be a conclusion about grid noise.

**The ablation is a textbook isothermal rarefaction fan.** Phase space shows the linear
u_z(z) ramp developing, with the target-ion front (99.9th percentile) accelerating
3.27 → 3.83 → 5.97 → **9.17 C_s** over 0 → 2.35 ps. This is the cleanest confirmation so
far that the laser is driving the ablation the model says it should.

### CORRECTION — what was actually leaving through the open boundaries

The 2026-07-28 entry above attributed the `open`-boundary particle loss to "the runaway
front arriving and being absorbed". **That is wrong, and the per-species numbers say so:**

- `P0_bc_open` (vacuum): **0.45 % of target *electrons*** left; target ions lost **1
  macroparticle out of 26 209**. At 2.35 ps the target ions span z ∈ [−88, +22] d_e with
  **none** beyond |z| > 90 — the ion front never reached a boundary. What leaves is the
  fast *electron* tail.
- `P0_bc_open_B` and `P0_bc_inject` (with ambient): the target species lost **0.00 %** and
  the entire 5.84 % is **ambient** — electrons 15.67 % and ions 15.71 %, almost equal.
  Equal electron and ion loss is not a thermal tail, it is **bulk ambient drain at the open
  walls**: the ambient fills the domain up to the boundary, and any ambient ion within
  ~v_th,i·t of a face leaves. With θ_i = 5×10⁻⁵ (v_th,i = 2.1×10⁶ m/s) over 2.35 ps that is
  ~30 d_e of each 100 d_e half-width, and a simple flux estimate gives 3.2 %/ps against
  6.7 %/ps measured.

So the wrap hazard's **mechanism** is confirmed (nothing can leave a periodic domain), but
its **consequence** — the ion front wrapping and polluting the far side — has *not* been
demonstrated at these run lengths, because the ion front does not reach a boundary in
2.35 ps. The boundary decision stands on the mechanism plus the B₀ and drive results, not
on observed pollution.

### NEW PHASE-2 CONSTRAINT — the ambient drains at open walls

At ~6.7 %/ps for a 200 d_e domain, a Phase-2 run of 2.5 gyroperiods (≈19 ps) would drain
the ambient **many times over**. The drain fraction scales as v_th,i·t/L, so the levers are
a larger domain, a colder ambient, or particle-injecting/thermal boundaries. **This must be
resolved before `P2_mag`**, and it is a direct consequence of choosing `open` — periodic
would not drain, which is the one thing periodic is good at. Added to the Phase-2 checklist.

### The exit-boundary overshoot — MEASURED, and the upstream description is not reproduced

`studies/exit_overshoot/`: a uniform **underdense** slab (0.5 n_cr) filling the domain so
the ray transits and exits the far face — the Phase-0 runs cannot test this, because their
overdense target turns the ray and sends it back out the *injection* face. τ = 1.265,
400 cells, `temperature_mode: fixed`, a 10¹⁴ W/m² probe so the profile stays static, and
`max_step = 2` because only the step-0 dump is needed. Ten `ray_cfl` values, seconds each.

| ray_cfl | exit cell | interior mean | interior cell-to-cell rms | TOTAL absorbed |
|---|---|---|---|---|
| 0.05 | −26.4 % | +0.05 % | 0.73 % | −0.12 % |
| 0.10 | −19.3 % | +0.18 % | 1.45 % | +0.04 % |
| 0.25 | **−7.9 %** | −0.13 % | 3.64 % | −0.30 % |
| 0.50 | +11.1 % | −0.36 % | 7.30 % | −0.53 % |
| 1.00 | −24.7 % | −1.45 % | 19.95 % | −2.00 % |

**Findings.**

1. **The dominant per-cell error is not the boundary — it is cell-to-cell aliasing over
   the whole domain.** Deposition is lumped at each RK4 step's *endpoint*
   (`deposit` is called once per step at the current position), so with a step of
   `ray_cfl × dz` the number of endpoints landing in a given cell varies. The rms scatter
   is 0.73 % at `ray_cfl = 0.05`, 3.6 % at 0.25 and **20 %** at 1.0. The exit cell is one
   sample of that pattern, not a separate mechanism.
2. **The overshoot mechanism is real but is superposed on a deficit.** On the smooth branch
   `ray_cfl ≤ 0.25` the exit-cell error follows ≈ (−27 % + ray_cfl), i.e. the predicted
   `+ray_cfl` extra step *is* being added, on top of a systematic ~−27 % shortfall in that
   cell. Beyond 0.25 the alignment scatter dominates (−45 % at 0.75).
3. **No net energy creation was observed.** The total absorbed power is **low**, not high:
   −0.12 % to −0.30 % for `ray_cfl ≤ 0.25`, degrading to −2.0 % at 1.0. Independently the
   operator's own `LASERDEP Pabs`/I₀ = 0.7156 against the analytic 1 − e^−τ = 0.7178,
   agreeing to **0.31 %**. **This does not reproduce the upstream description** (+24.9 %
   high in the final cell, energy *created*, inflating total absorption by ≤ 0.04 %). The
   geometry differs from theirs, so this is a partial non-reproduction rather than a
   contradiction — but the upstream figure should not be quoted for this project's runs.

**Practical rules, which is what the measurement was for.** (a) Discard the boundary cell
in any spatial deposition analysis. (b) Keep `ray_cfl ≤ 0.25` for per-cell profile work
(alias ≤ 3.6 %) and ≤ 0.1 for ≤ 1.5 %. (c) Integrated absorption is safe to ≤ 0.3 % at
`ray_cfl ≤ 0.25` — so gate G4 matters for *profiles*, much less for *energetics*.

### Bug fixed in the profile-table reader

`read_profile_table` assumed the last three columns were `(n_e, H, P_abs)`. The dump
actually has **six** columns in 1D — `z, n_e, H, P_abs, theta_e, A` — so it was silently
returning `A` as `P_abs`. The `#` lines are prose, not a column-name row, so the layout is
now parsed positionally from the front and the columns are returned under names (`z`,
`n_e`, `H`, `P_abs`, `theta_e`, `A`). This affected `laser_report.py`'s profile figure for
every run made before this entry; those figures have been regenerated.

`runs/P0/P0_bc_2d_open` (transverse `open`, the declared follow-up) is running.

### Movies added, and the 2D planar flatness criterion is met quantitatively

`scripts/make_movies.py` produces three movies per run into `media/<ID>/`:
`movie_fields.mp4` (`n_e(z)` and `B_y/B₀(z)` lineouts with the full `f_abs(t)` history
below and a cursor on the current frame), `movie_phase.mp4` (ion `(z,u_z)`), and
`movie_map2d.mp4` (`n_e(x,z)`, 2D only). 11 movies over the five completed runs.

Axis limits are fixed across all frames — per-frame autoscaling would make a plume that
grows two decades look stationary — and the frame directory is cleared before writing so a
shorter re-run cannot splice stale frames onto the end.

**`P0_bc_2d` passes its transverse-flatness criterion, as a number.** Transverse relative
spread of `n_e` (std over x per z, where there is meaningful plasma): **0.00 % at t = 0,
median 5.0 % / max 14.9 % at 0.40 ps, median 5.3 % / max 13.2 % at 0.79 ps**, against a
per-cell shot-noise floor of `1/√32` = **17.7 %** (16 ppc × 2 electron species). The spread
is *below* the noise floor, so there is **no coherent x structure** — which is what a
uniform beam on a planar target with periodic transverse boundaries must give, and it is
the precondition for `P0_bc_2d_open` attributing any x structure to the transverse
boundary rather than to dimensionality.

---

## 2026-07-28 (later still) — `P0_bc_2d_open`: transverse `open` closes Phase 0

8000 steps (0.791 ps) in 20 min at 4 threads; `--verify` OK. Byte-identical to `P0_bc_2d`
except `geometry.boundary.transverse: periodic → open`.

**The comparison is controlled at t = 0, bit-identically.** The transverse `n_e` difference
against the planar run has an **interior median of 0.000 %** and is confined to **exactly
two columns per side**, at **0.365×** and **0.861×** the interior density. That is the
`particle_shape = 2` deposition losing its periodic wrap — a quadratic shape spans three
cells, so the outermost two are under-counted.

**New trap: the edge-column deficit changes the ray physics for a near-critical target.**
At 0.365× the interior value, a 1.5 n_cr target reads **0.55 n_cr — underdense** in the
outermost column, so the ray transits instead of turning. `f_abs(0)` is 0.2594 vs 0.2466,
a 5.2 % offset from four columns of eighty. **Rule for finite-spot 2D work: use a beam
profile that is negligible at the transverse walls** — which the physics wants anyway, and
which makes this artifact irrelevant — and exclude the outer two cells from analysis.

*(This also means the falsification criterion written in that run's README —* "`f_abs`
diverging from t = 0 means the boundary changed the drive" *— was wrongly framed. It did not
anticipate that a transverse boundary alters the density* deposition *in edge columns, and
hence their absorption, at t = 0. The interior-identity check is the one that matters.)*

**The axis stays usable.** The transverse deficit (>5 % from centre) reaches 1.0 d_e (2
cells) at t = 0, 2.0 d_e at 0.40 ps and **3.5 d_e at 0.79 ps** — growing, but only 3.5 of
the 20 d_e half-width, leaving **±16.5 d_e clean**; centre density falls just 3 %. The
transverse `pec` walls build a `B_y` excursion reaching **1.9**, comparable to the axial
walls.

**The energy drain is the headline, and it is severe.**

| | `P0_bc_2d` (periodic ⊥) | `P0_bc_2d_open` (open ⊥) |
|---|---|---|
| particles lost | 4.61 % | **30.83 %** |
| ambient electrons / ions | 6.51 % / 6.45 % | **47.74 % / 30.00 %** |
| target electrons / ions | 0.00 % / 0.00 % | 14.11 % / 7.82 % |
| total particle KE | −4.3 % | **−42.9 %** |

In 0.791 ps — **0.10 gyroperiods** — nearly half the ambient electrons and **43 % of the
total kinetic energy** are gone. The explaining scale: at θ_e = 5×10⁻³ the ambient electron
thermal speed is 0.0707 c, so an electron covers ~100 d_e in 0.79 ps against a transverse
extent of 40 d_e. A hot electron population is simply not confined by a box that small.

### This sharpens the Phase-2 drain blocker into a box-size requirement

The axial-drain figure recorded earlier (~6.7 %/ps for a 200 d_e axial domain) is the *mild*
case. With transverse `open` at ±20 d_e the loss is ~40 %/ps in particles and ~54 %/ps in
energy. Since the drain fraction scales as `v_th·t/L`, confining the ambient's *electron*
thermal excursion over a 2.5-gyroperiod (19 ps) run needs `L ≳ v_th,e·t` ≈ **2400 d_e** in
every open direction — utterly unaffordable transversely. **So Phase 2 must either keep the
transverse direction periodic (quasi-1D, as Schaeffer's own runs did with 12 transverse
cells), or use a colder ambient, or use particle-injecting/thermal boundaries.** A fully 2D
finite-spot magnetized shock with open transverse walls is not reachable by making the box
bigger.

That is a real constraint discovered in Phase 0 rather than in Phase 2, which is what
Phase 0 was for. Note it does **not** retract the `TEST_PLAN.md` §2.1 observation that
`ρ_i0 ≈ 65 d_e` makes a gyro-scale transverse box affordable — that box is affordable, it
just cannot have *open* transverse walls holding a hot ambient.

### Phase 0 is complete

Six runs, the boundary decision recorded, both transverse options characterised, the
exit-overshoot measured, and every run carrying a generated geometry diagram, a figure set,
movies and a gate table. `media/P0/P0_2d_transverse/compare.png` is the controlled 2D pair.

---

## 2026-07-28 (later) — Can the region behind the target be removed? Yes, with `open`. Plus a RETRACTION.

**The question.** The laser enters at +z and the ablation flows back toward +z, so the domain
behind the target looks like wasted resolution. Two variants of `P0_bc_open_B`, each with the
domain truncated at the target's initial rear face (`lo_de: −100 → −60`, **320 cells vs 400**)
and everything else byte-identical: `P0_rear_open` (`open` rear) and `P0_rear_reflect`
(`reflecting` rear). New `scripts/compare_frontside.py` compares only z > −40, because
`compare_runs.py` overlays whole-domain totals, which *must* differ when one run holds less
plasma.

**Two facts established before running.** (1) The laser genuinely cannot see behind the
target: peak `n_e/n_cr` *rises* 1.55 → 1.59 → 1.63 → **1.81** — the target **compresses**
rather than rarefying — so the ray always turns at the critical surface inside the slab and
never reaches the rear boundary; the exit-overshoot does not apply there either. (2) But the
rear is **not** quiescent: by 2.35 ps **6.95 %** of target ion mass sits behind z = −60,
reaching z = −87 at `u_z` = −8.7 C_s. So the question was empirical.

### `P0_rear_open` is a valid truncation

| front-side observable | vs `P0_bc_open_B` |
|---|---|
| target-ion count at z > −40 | **+0.1 %** |
| `n_e(z)` at z > −40, final time | median 5.6 %, 90th pct 12.5 % (ppc level) |
| `E_abs` integrated over the run | **−0.6 %** |
| total target-ion `p_z` | **−3.4 %** |
| plume front position | within **1.0 d_e** (2 cells) of 30 d_e travelled |
| cost | **20 % fewer cells**, 3.5 min vs 4.7 min |

### `P0_rear_reflect` is different physics, not a cheaper equivalent

It **flips the sign of the target's net momentum**: total target-ion `p_z` = **+0.0067**
against **−0.0315** (reference) and −0.0305 (`open`). In the full domain the rear blowoff
dominates and the target recoils away from the laser; a tamped rear returns that momentum.
Front-side density and count look fine (+0.3 %, median 4.8 %), so **had only the local plume
been checked this would have passed** — the momentum balance is the discriminator. Keep it as
the reference for a deliberately tamped target.

### RETRACTION — `f_abs(0)` is not a usable discriminator

Both truncated runs gave `f_abs(0)` = 0.3108 against 0.2827 for the reference, +9.9 %. Before
attributing that to the truncation I measured the noise floor: `studies/fabs_noise/`, six runs
of one identical config differing **only in `numerics.random_seed`** (a new schema field, so
the sweep is config-driven):

```
0.2925  0.3140  0.2740  0.2938  0.2837  0.2279
mean 0.2810   std 0.0292   relative std 10.39%   FULL SPREAD 30.64%
```

**`f_abs(0)` carries a ~10 % 1σ.** The step-0 profile dumps localise the mechanism precisely:
essentially the entire difference between any two runs sits in the **single cell containing
the critical surface** (P_abs there 1.176e24 → 1.511e24 W/m³ between runs whose densities
agreed to 0.0004 n_cr), because `K ∝ 1/√(1 − n_e/n_cr)` diverges there and the operator
integrates that layer over a *locally interpolated*, noisy density and gradient.

**Therefore I retract the claim, made in the `P0_bc_2d_open` entry above, that the
edge-column density deficit produces a measurable 5.2 % `f_abs(0)` offset.** That 5.2 % is
well inside a 10.4 % σ. What survives — because it was measured, not inferred — is the
deficit itself (outer two columns at **0.365×** and **0.861×** the interior density, interior
median difference 0.000 %), the fact that it puts a 1.5 n_cr target at 0.55 n_cr in the
outermost column, and the rule that follows. Only the absorption number is withdrawn.

**New working rule: quote `E_abs`, never `f_abs(0)`, when comparing runs.** `E_abs` integrates
hundreds of applications and agreed to 0.6 % between geometries whose `f_abs(0)` differed by
10 %. This also sharpens gate G4 — the `ray_cfl` non-asymptoticity at turning points is a
*noise-amplification* problem, not only a discretisation one — and it means Phase 3's
intensity sweep must average over time or seeds rather than read single-shot absorption.

*(Also: `compare_frontside.py`'s `p_z(front side)` column is a signed sum amounting to only
32–44 % of the gross flux, so it carries heavy cancellation noise — the total-momentum
comparison is the reliable one. A sign-formatting bug in that column was fixed.)*

**Adopt for Phase 1 and 2: truncate at the target's rear face with an `open` boundary**, for
free-standing-foil physics at 20 % lower cost. Verified for a 20 d_e / 1.5 n_cr target over
2.35 ps (≈ the rear rarefaction's slab-crossing time); re-check for a much thinner target or a
much longer run, where the two faces couple more strongly.

---

## 2026-07-28 (later) — Rear truncation re-tested at 4× thickness: it gets BETTER

The 20 d_e verification carried an explicit caveat — valid for *that* thickness over *that*
duration. `P0_thick_full` / `P0_thick_open` repeat it at **80 d_e,cr = 13.4 µm, 49 % of the
upstream `run_laser_shock` target** (163 d_e,cr), which is the setup this project actually
wants. Everything else is unchanged; the coronal scale length was deliberately left at 15 d_e
so thickness is the only variable (matching the upstream `L_n/w_t` = 0.75 is a Phase-1 item).

**The prediction, made before running.** The rear rarefaction crosses the slab in `w_t/c_s`:
**2.3 ps at 20 d_e** against a 2.348 ps run (**103 % crossed — fully coupled**, which is why
`P0_rear_reflect` flipped the momentum sign) but **9.1 ps at 80 d_e** (**26 % crossed**). So
the faces should decouple and the truncation should improve.

**Confirmed, by the mechanism rather than by luck.** Target-ion mass behind the initial rear
face, in the full-domain references: **6.97 % → 2.24 %**, a 3.1× reduction closely tracking
the predicted ~4× ratio of crossing fractions.

| front-side observable | 20 d_e pair | **80 d_e pair** |
|---|---|---|
| total target-ion `p_z` | −3.39 % | **−0.54 %** (6× better) |
| `E_abs` over the run | −0.67 % | **+0.88 %** |
| target-ion count at z > face | +0.10 % | **+0.11 %** |
| cost saved by truncating | 20 % of cells | 15 % of cells |

`p_z(total)` is the decisive column — it is the observable that caught `P0_rear_reflect`
flipping sign — and it improves **6-fold**. `E_abs` changes sign between the pairs but both
are sub-1 %, i.e. scatter; `f_abs(0)` cannot refine it, carrying a 10.4 % 1σ.

Both thick runs stay overdense (peak `n_e/n_cr` = 1.737 and 1.761), so the premise holds: the
ray turns inside the slab and the rear boundary is invisible to the laser.

`E_abs` is also nearly unchanged by quadrupling the thickness (2.117e5 vs 2.155e5 J/m², −2 %),
which is a first, incidental data point for **H3** — thickness buys piston *momentum*, not
coupled energy, because the drive shuts off on the corona's terms rather than the slab's.

**ADOPTED for Phase 1 and 2: truncate at the target's rear face with an `open` boundary.**
Verified at 20 d_e and 80 d_e, with fidelity improving toward the thicker, more realistic end.
The remaining step to the desired setup is the coronal scale length, not the truncation.

*(Tooling note: `yt` refuses a `covering_grid` flush against a non-periodic domain edge when
the right edge rounds a float ULP outside it — it hit the new domain sizes. `plot_fields` and
`make_movies` now call `ds.force_periodicity()` first, which only affects ghost-cell fetching
that a full-domain covering grid never needs. Also worth recording: `diag1` carries only the
total `rho`, not per-species — per-species densities are on `diag_fields`.)*

---

## 2026-07-28 — Phase 1 opens: `P1_vac_1d` + `P1_vac_1d_off`. **H2 is falsified**; the ablation is real; G6 closes for the first time

Two runs, both 102 400 steps = **10.018 ps**, each **8 min on one RTX 4070** (`--verify` OK,
zero errors, gates 4 pass / 0 warn / 0 fail on the driven run). First Phase-1 runs, and the
first GPU runs in this project.

**Setup.** `P0_thick_open` with the coronal scale length finally taken to the upstream ratio
— `L_n` 15 → **60 d_e**, so `L_n/w_t` = **0.75** — into vacuum, no `B₀`, 400 ppc, and 4.3×
longer than any Phase-0 run. Domain [−300, +700] d_e, 2000 cells, `open`/`open`.

### 1. `L_n` changed the absorption REGIME, exactly as predicted

Predicted before running, by integrating τ to the turning point at the group `T_e`:

| | `L_n` = 15 (`P0_thick_open`) | `L_n` = 60 (`P1_vac_1d`) |
|---|---|---|
| turning point | +10.2 d_e | +38.2 d_e |
| τ to the turning point | 0.14 — optically **thin** | 5.60 — optically **thick** |
| predicted `f_abs(0)` | 0.244 | 1.0000 |
| **measured `f_abs(0)`** | **0.248** | **1.0000** |

The step-0 deposition profile confirms the mechanism **to the cell**: predicted τ = 1 at
+53.6 d_e, measured peak deposition at **+53.8 d_e** (`n_e` = 0.672 `n_cr`); deposition spans
+38.2 → +182.3 d_e and **0.000 % of `P_abs` lands at or below the critical surface**. The
densest absorbing cell is at `n_e` = 0.9990 `n_cr` — right up to critical, never past. So this
configuration is a **pure coronal absorber**: the ray dies ~15 d_e short of the turning point,
which plays no role in the drive. (Corollary, untested: G4's `ray_cfl` sensitivity is a
turning-point effect and should be *weaker* here than in Phase 0.)

### 2. **H2 is falsified. Coupling is drive-limited, not capacity-limited.**

The decisive measurement, and unambiguous: **`E_abs` never rolls over.** `f_abs` falls from
1.000 to a **plateau ≈ 0.23** — not to zero — and keeps delivering for 97 % of the run.

| | value |
|---|---|
| `E_abs` final | **2.4626×10⁶ J/m² = 11.5×** `P0_thick_open`'s 2.135×10⁵ |
| incident energy absorbed | **24.6 %** (mean `f_abs` 0.2458) |
| late/early `dE/dt` | **0.41** — not 0 |
| 50 / 90 / 99 % of `E_abs` by | 3.98 / 8.86 / **9.90** ps |

Hence `E_abs ≈ f_abs·I₀·t` with `f_abs` quasi-steady, i.e. **`E_abs ∝ I₀`** — the negation of
H2. Absorption does not switch off, it **floors**. The half-peak "shutoff" (0.2505 ps) is the
fall onto the plateau, **not** a `t_s`; do not quote it as one. This also explains §2.3's
"known tension" (2.4× predicted vs 16× measured for the `Z_eff·lnΛ` change).
**H4 loses its stated mechanism** and Phase 3A must be re-planned around the plateau law —
see `TEST_PLAN.md` §2.4 (new).

### 3. The ablation is **99.93 % laser-driven** — gate G3 discharged

| | driven | laser-off control | ratio |
|---|---|---|---|
| net particle-KE gain | **+2.4212×10⁶ J** | **−1 696 J** | **−0.07 %** |
| weight lost | 0.0104 % | 0.0000 % | — |

The control's net energy change is negative and 4 orders of magnitude smaller, despite
`dz/λ_D` = 61. **G2 is now bounded.** Its internal motion is physical, not numerical:
electrons **−51.4 kJ**, ions **+49.7 kJ** — ambipolar transfer in a relaxing 51 eV corona,
cancelling to ≈ 0. Grid heating would instead show a net *gain* shared by both species.

### 4. Gate G6 closes for the first time: **−0.74 %** at **0.0104 %** boundary loss

`E_abs` 2.4626×10⁶ J vs particle-KE + field gain 2.4445×10⁶ J. Phase 0 could only report
+218 % / +235 % at 5.8 % / 17 % loss. **The generous vacuum cushions bought this**, and the
reason is worth recording: **0.68 % of macroparticles left the box but they carried only
0.0104 % of the weight** — a 65× difference, because the escaping population is the tenuous
corona tail. **Quote the weight loss, not the macroparticle count.**

### 5. The piston is weak in bulk, and **H3 is untested rather than falsified**

| target-ion `v_z` at 10 ps | driven | control |
|---|---|---|
| weight-weighted mean, forward-moving | **0.00144 c** | 0.00089 c |
| unweighted 99.9th pct ("front") | 0.0267 c | 0.0091 c |

With `c_s` = 0.003149 c (implied `T_e,ab` = 0.5068 keV; 0.7602 keV per target ion) the bulk
gives **α ≈ 0.46**, below H3's 1–3 — but that is a **lower bound**: at `c_s` = 5.6 d_e/ps the
rarefaction has crossed only ~70 % of the 80 d_e slab, so ~30 % of the mass is still cold and
is averaged in. A fair test needs `plot_ablation.py` to restrict to the ablated population;
**that is the next Phase-1 item.** Energy partition is **77.4 % electrons / 22.6 % ions**, so
only ~23 % of the coupled energy is directed ion motion.

**Read fronts with care.** The control's front reaches 0.0091 c unaided — only 2.9× below the
driven run's — so a percentile-front `v_p` is ~1/3 undriven thermal expansion. By mass the
separation is clean. **Use weighted bulk measures for piston speed, always against the control.**

### 6. GPU: 12.7×, and validated against CPU

No 1D CUDA binary existed (`WarpX_DIMS` is compile-time, so `build_cuda/` is 2D-only); built
`build_cuda1d/` with the **CUDA 12.9** toolkit in `~/opt` — the system `nvcc` is 12.0 and
AMReX requires ≥ 12.2. `launch.sh` gained `--gpu [N]` (pins `CUDA_VISIBLE_DEVICES`, forces
`OMP_NUM_THREADS=1`); the two 4070s carried both runs concurrently.

| backend | 2000 steps | projected 102 400 |
|---|---|---|
| CPU, 8 threads | 117.9 s | **100.6 min** |
| GPU, 1× RTX 4070 | 9.3 s | **7.9 min** (actual: 8 min) |

**Estimating by scaling was wrong by 4×** (predicted ~25 min CPU): cell count dominates far
more than a particles×steps scaling allows. **Benchmark a 2000-step slice when the grid changes
size.** CPU and GPU agree on `P_abs(0)` to **2×10⁻⁶** but on integrated `E_abs` only to ~2.5 %,
because the kicks use `ParallelForRNG` and the backends draw different streams — different
*realizations*, well inside the 10.4 % seed noise on `f_abs(0)`. **Run a physics run and its
`_off` control on the same backend**, or that lands inside the G3 subtraction.

### 7. Tooling: three crashes on the first-ever laser-off run

Every headline run is *required* to have an `_off` companion, but all Phase-0 runs were driven,
so `P_inc = 0` had never been exercised. `f_abs` becomes NaN and `P_inc·t` zero:
`laser_report.py` (NaN `set_ylim`), `compare_runs.py` (`ZeroDivisionError` comparing a run to
its own control), `make_movies.py` (NaN axis limit). All three fixed and the case annotated
rather than skipped silently. `make_movies.py` additionally **stranded 81 PNGs** — `encode`
only deleted frames after a *successful* ffmpeg run, so a crash while building them leaked;
now swept on any exception. And `laser_report.py`'s `f_abs` panel title hard-coded "then shuts
itself off", which this run disproves — now computed from the data, as the `E_abs` panel
already was. `geometry_diagram` also drew an incoming beam for a laser-off deck; now labelled
`LASER OFF (I = 0)`.

**Numerics.** `Tlocalfrac` 0.432 → **1.000** (saturated by ~1.5 ps): at 400 ppc every absorbing
cell has a measured `T_e`, so G5's ≤ 0.31 % bound is real. Raw `E_z` rms 1.2×10⁹ V/m at
`dz/λ_D` = 61 — mostly grid noise, hence the 9-cell boxcar on the streak. **Domain sizing was
well judged**: rear expansion reached the `pec` wall at **t ≈ 7.5 ps** vs a predicted ~8.3 ps,
and the bulk never approached z = +700.

**Media.** `media/P1/P1_vac_1d{,_off}/`: `checks`, `gates`, `laser_history`, `laser_profile`,
`fields_streak`, `fields_lineouts`, `phase_space`, `movie_fields.mp4`, `movie_phase.mp4`;
plus `media/P1/P1_g3/compare.png` for the G3 subtraction.

---

## 2026-07-29 — `P1_vac_1d_long` (100 ps): **the drive DOES decay, hydrodynamically, at ~40 ps** — and **H3 is confirmed**

`P1_vac_1d` + control re-run **10× longer** (1 024 000 steps = 100.18 ps) on a 2.7× larger
domain ([−3000, +2400] d_e, 10 800 cells). 3 h 45 m / 3 h 10 m on the two RTX 4070s, zero
errors, `--verify` OK, gates 4 pass / 0 warn / 0 fail. All four pre-run expectations confirmed,
**including the mechanism**.

### 1. The plateau closes, and the cause is the target going underdense

| t [ps] | mean `f_abs` | `dE/dt` [J/m²/ps] | peak `n_e`/`n_cr` |
|---|---|---|---|
| 0–10 | 0.256 | 2.27×10⁵ | 1.54 |
| 20–30 | 0.274 | 2.70×10⁵ | 0.93 ← crosses `n_cr` at **28.8 ps** |
| 30–40 | 0.189 | 1.81×10⁵ | 0.40 |
| 40–50 | 0.107 | 1.06×10⁵ | 0.25 |
| 90–100 | **0.044** | 4.39×10⁴ | 0.090 |

`f_abs` holds ≈ 0.24 to ~30 ps, then decays 5× to 0.042. **Peak `n_e` crosses `n_cr` at 28.8 ps
— exactly where the plateau breaks.** Smoothed `f_abs` is at half the plateau by **41.6 ps**,
a quarter by 68.9 ps. So the drive ends because the rarefaction thins the target below critical
and the beam punches through with no turning point — **not** because a shutoff temperature is
reached, and **not** never.

`E_abs` = **1.349×10⁷ J/m²** = 57 % of what a persistent 0.234 plateau would have given;
overall absorbed fraction 13.5 % (was 24.6 % over 10 ps); late/early `dE/dt` = 0.23.
**H2 stays falsified**, with the correct form `E_abs = ∫f_abs(t)·I₀ dt`, `f_abs` set by the
target's hydrodynamic state. `TEST_PLAN.md` §2.5 (new) re-scopes Phase 3A around a
**drive-duration law `t_drive(I₀)`** — and notes H4's optimum may survive by that route.

**For Phase 2 the margin is thin:** `t_drive` ≈ 40 ps against the `5 ω_ci0⁻¹` = 38 ps that
formation needs.

### 2. H3 CONFIRMED — α = 1.5–2.4

The bulk saturates (0.73 → 0.81 → 0.84 `c_s` over 50–100 ps), so this is a measurement, not the
lower bound the 10 ps run could offer. **Two ways to get it wrong, both now documented:**

- **`c_s` must come from the measured electron energy.** 66 % of the coupled energy is in *ions*
  by 100 ps, so `laser_report`'s implied `T_e,ab` = 2.775 keV (which assumes it is all electron
  thermal) overstates `c_s` by 2.3× and gives a spurious α = 0.84. From `<KE_e>` = 822 eV ⇒
  `T_e` = **548 eV** ⇒ `c_s` = **0.00327 c**:

| measure | v_p | α |
|---|---|---|
| control-subtracted bulk | 0.00498 c | **1.52** |
| bulk forward, weight-weighted | 0.00622 c | **1.90** |
| rms, weight-weighted | 0.00774 c | **2.36** |

- **Never a percentile front.** The control's own front reaches 0.0178 c, and the driven front is
  *boundary-truncated* late — 0.0536 c at 30 ps but 0.0245 c at 100 ps, because the fast ions
  left. Non-monotonic front ≠ deceleration.

### 3. Drive efficiency triples: 62 % of `E_abs` ends up in ions

| t [ps] | `E_e` [J] | `E_i` [J] | ion share | `T_e` [eV] |
|---|---|---|---|---|
| 10.0 | 2.37×10⁶ | 1.00×10⁶ | 29.7 % | 293 |
| 50.1 | 5.06×10⁶ | 6.15×10⁶ | 54.9 % | 625 |
| 100.2 | 4.38×10⁶ | **8.42×10⁶** | **65.8 %** | 548 |

`T_e` **peaks near 625 eV at ~50 ps then falls** as expansion cools it and energy transfers to
ions. Ion energy is 62 % of `E_abs` — the quantity Phase 2 spends.

### 4. G3 holds at 10× the steps — grid heating does NOT accumulate

Control net particle-KE gain **−7 962 J = −0.066 %** of the driven +1.1975×10⁷ J, statistically
identical to the 10 ps control's −0.07 %. Absolute grew 4.7× while the driven gain grew 4.9×, so
the **ratio is flat**. Still the ambipolar signature, not heating: electrons −221.8 kJ, ions
+213.9 kJ, net −8.0 kJ. **G2 (`dz/λ_D` = 61) is bounded for 1.024 M steps.**

### 5. G6 = −9.56 %, and the deficit is accounted for — but the domain was undersized

`E_abs` 1.3486×10⁷ J vs particle-KE + field gain 1.2196×10⁷ J at **1.1405 %** weight loss (10 ps
run: −0.74 % at 0.0104 %). The arithmetic is self-consistent: the missing 1.29×10⁶ J is 9.6 % of
`E_abs`, carried by 1.14 % of the mass ⇒ the escapers have ~8.4× mean specific energy, i.e. a
fast runaway tail; and the sign is right (WarpX does not report energy leaving with absorbed
particles). Loss is **entirely late** — 0.0000 % at 25 ps, 0.0127 % at 50, 0.2211 % at 75,
1.1405 % at 100 — so **use t ≲ 50 ps for any strict closure claim from this run.**

**My domain extrapolation was too conservative and this bounds the result.** Occupied cells went
526 → 4 508 (30 ps) → 8 059 (50 ps) → **pinned at 10 800 from ~60 ps**: the plume edge sits
against both walls for the last 45 % of the run. The 10 ps drift rates (~20 d_e/ps) understated
it because the target kept heating (`T_e` 293 → 625 eV); the edge actually advances at
**~50 d_e/ps** once `T_e` ≈ 600 eV. **A future 100 ps run needs ≥ ±5000 d_e.** The control, with
no drive, lost only 0.0014 % — so **the domain requirement is set by the drive, not the geometry.**

### 6. Why the runs took 1.8× their benchmark — two causes, separated

Benchmarked 123 min, took 3 h 45 m. **(a) Host CPU starvation**: 2882 % demand on 32 cores (16
`flash4` + an 8-thread CPU WarpX). A CUDA run is latency-bound on one host thread issuing kernel
launches, so preemption idles the GPU — utilisation 71 % → 53 %, power 47–56 W of a 200 W cap.
**Benchmarks assume an idle host.** **(b) Genuine plume spreading**: occupied cells 526 → 10 800
(20×) at *flat* particle count, so deposition scatters over 20× the memory footprint.
`warpx_rate` 0.0070 → 0.0132 driven and 0.0062 → 0.0111 in the control — **it slows with no
laser at all**, which is how the two were separated. Roughly 1.5× physics × 1.3× contention.
**`warpx.sort_intervals` is worth benchmarking on GPU** — `CLAUDE.md`'s "sorting is
neutral-to-negative" is an inherited *CPU* result.

### 7. Tooling

`laser_report`'s two computed titles **contradicted each other** on this run — panel 1 said
"SHUTS OFF", panel 2 said "the drive keeps delivering" — because panel 1 compared the late level
to the *peak* (a sub-ps cold-target transient at 1.000) rather than to the plateau. Both titles
now derive from one plateau/late pair and report three regimes (holds / decays N× / shuts off).
The `f_abs` panel also gained a **running-median overlay**: across 102 400 applications the raw
trace is a solid block, and the median is what makes the plateau's abrupt end at ~30 ps visible.

**Media.** `media/P1/P1_vac_1d_long{,_off}/` — `checks`, `gates`, `laser_history` (the headline),
`laser_profile`, `fields_streak`, `fields_lineouts`, `phase_space`, `movie_fields.mp4`,
`movie_phase.mp4`; plus `media/P1/P1_long_g3/compare.png`.

---

## 2026-07-29 — 2D planar validation **FAILS on a located operator bug**; `runs/`+`media/` regrouped by phase

Three runs: `P1_vac_2d` (2D planar, 5 h 07 m), `P1_vac_2d_off` (its G3 control, 1 h 57 m), and
`P1_vac_1d_thick` (the matched 1D baseline, 21 min). All 432 000 / 305 600 steps to 29.9 ps, zero
errors, `--verify` OK. Built to the user's spec: **rear side not simulated** (domain cut at the
target's rear face with the validated `open` boundary) and a **thick target** (400 d_e = 67 µm,
5× the 1D reference, 2.45× upstream).

### THE HEADLINE: 2D is blocked, and it is a bug with a line number

`P1_vac_2d` is *exactly planar* — uniform beam, periodic transverse — so it must reproduce 1D on
axis. It does not.

**Not a plumbing error.** At t = 0 the two agree on absorbed power per unit area to **2×10⁻⁵**
(1.0000×10¹⁸ vs 9.9998×10¹⁷ W/m²) and on boundary weight loss to **0.2 %** (6.133 vs 6.146 %). Ray
launch, power apportionment over 64 rays, deposition mapping and boundaries are all correct.

**The failure is an edge pile-up.** Column-integrated `P_abs` in units of the mean at 8.97 ps:
column 0 = **23.2×**, column 63 = **25.2×**, all 62 interior columns 0.10–0.51×. Share of all
absorption in those two columns:

| t [ps] | 0 | 2.99 | 8.97 | 26.90 |
|---|---|---|---|---|
| edge share | **3.2 %** (= 2/64, correct) | 73.0 % | 75.6 % | **98.8 %** |

`theta_e` (1.16–1.54× higher) and `n_e` (lower) in those columns respond, so the energy really
lands there. Net absorption is **+12.4 %** above matched 1D.

**The cause**, in `warpx-cda/Source/Particles/LaserDeposition/LaserDeposition.cpp`:

```cpp
// deposit(), ~line 739 -- clamps the cell index in EVERY dimension:
idx[d] = amrex::min(amrex::max(ii, lo3[d]), hi3[d]);
// ray-march exit test, line 893 -- checks ONLY the propagation axis:
if (c[m_axis] < plo[m_axis] || c[m_axis] > phi[m_axis]) { break; }
```

A ray that acquires transverse deflection and passes `xlo`/`xhi` is **neither wrapped periodically
nor terminated** — it marches on outside the domain and every further deposit is **clamped into
the edge column**.

**The deflection itself is benign.** The G3 control develops the same ~5 % transverse density
ripple with **no beam at all** (corona rms/mean 0.040 → 0.044 vs 0.056 → 0.063 driven), so it is
ordinary PIC shot noise; the start is quiet (`NUniformPerCell` → 0.06 % initial variation). At
t = 0 rays are exactly normal-incidence, which is why the artifact switches on only once structure
exists, then grows as more rays drift out and paths lengthen.

**It will NOT converge away** — ppc, `rays_per_cell` and field smoothing are irrelevant to a
deterministic index clamp. Fix upstream (wrap periodic dims via `geom.periodicity()`, terminate on
non-periodic transverse faces), then re-run this pair as a **regression test** with a sharp
criterion: edge share ~3.1 %, and `E_abs` matching the 1D baseline instead of exceeding it by 12 %.

**1D is unaffected** — no transverse dimension for rays to drift into, which is exactly why the
1D↔2D comparison isolated it.

### A wrong mechanism I asserted first, and what corrected it

My initial reading was *refractive self-channelling*: rays bending away from density maxima and
concentrating in valleys over long paths. **That was wrong**, and it would have cost a pointless
ppc convergence study of a deterministic bug. The summary statistic (rms/mean = 4.17) fits both
stories equally; only the **spatial pattern** distinguishes them — two hot edge columns and 62 flat
ones is a boundary signature, not channelling. **Diagnose non-uniformity from the profile, never
from its variance.**

### Also: median vs mean across dimensionalities

The 5–25 ps **median** `f_abs` differs 1D vs 2D by **48 %** (0.260 vs 0.385) where the
energy-integrated figure differs by **12.4 %**. 2D sums 64 rays so its distribution is smooth and
median ≈ mean; 1D's single ray is spiky and median ≪ mean. **Compare energy-integrated `E_abs` or
the mean — never the median — across runs of different dimensionality.**

### Gate G3 at 36 ppc (the 2D-affordable value)

Control net particle-KE gain **−1.8615 J/m = −3.09 %** of the driven +60.258 J/m. Still
**negative**, so not grid heating, and G2 stays bounded — but 47× the −0.066 % measured at 400 ppc.
Quote it beside any few-percent 2D number. G6: −8.42 % at 6.15 % weight loss (the truncation's
price, matching the 1D baseline's −8.53 % / 6.13 %).

### Housekeeping

`runs/<phase>/<run_id>/` and `media/<phase>/<run_id>/`; `media_dir()` derives the phase from the
run-ID prefix. Also fixed **two stale falsified claims** in `CLAUDE.md` and `TEST_PLAN.md` §1.2
that still asserted the H2 "shuts off / intensity-independent" picture.

**Media.** `media/P1/P1_vac_2d{,_off}/` and `media/P1/P1_vac_1d_thick/` — `checks`, `gates`,
`laser_history`, `laser_profile`, `fields_streak`, `fields_lineouts`, `fields_map2d`,
`phase_space`, `movie_fields.mp4`, `movie_phase.mp4`, `movie_map2d.mp4`.


---

## 2026-07-29 — `studies/spot_leak_ppc`: the finite-spot "7 % leak" is **two** effects, one artifact and one real

`runs/P1/P1_vac_2d_spot` puts ~7 % of its absorbed power outside 2.5 beam waists, where the launch
profile has 0.2 %. The ppc pair (36 vs 144, everything else fixed; target thinned to 100 `d_e` and
`t_end` cut to 1 ps so 144 ppc fits in 12 GB) was launched to decide artifact-or-physics. It
decided both, because the single number contained two effects with different ppc scalings.

Full write-up and the reproducing command in `studies/spot_leak_ppc/README.md`. 36 ppc ran 14 400
steps in 1103 s, 144 ppc in 2331 s.

**Figure:** `media/spot_leak_ppc/spot_leak_ppc.png` — four panels, one per conclusion below
(`python studies/spot_leak_ppc/figures.py`).

### `t` = 0 is exact, and identical at both ppc

Before the plasma evolves, `T_e` and `n_e` are uniform, so the absorbed-power profile must be the
intensity profile. It is: `w_eff/w₀` = **1.0000**, `f_ax` = **0.9999**, `f(1w₀)` = **0.9973**,
`f(2w₀)` = **1.0009**, leak beyond 2.5 `w₀` = **0.00041** (the launch Gaussian's own tail). The
same five numbers at 36 and 144 ppc. A quantity that does not move when the particle count
quadruples is **geometry, not statistics** — so this is the first transverse measurement in the
campaign with no `1/√ppc` floor, and it is now the Tier-2 acceptance baseline for Phase 1.5
(`TEST_PLAN.md` §7.5.4). Third independent confirmation of `warpx-cda` c817b63.

### The far-wing leak: noise, and it scales as a POWER

| `t` [ps] | leak 36 ppc | leak 144 ppc | ratio |
|---|---|---|---|
| 0.249 | 0.0156 | 0.0039 | **×0.25** |
| 0.498 | 0.0466 | 0.0125 | **×0.27** |
| 0.747 | 0.0299 | 0.0146 | ×0.49 |

×4 particles halves a noise *amplitude* (the ripple at `n_cr` went 9.32 % → 4.56 %, ×0.49 against
×0.50 predicted; the peak `n_e` excess ×0.43). Weakly scattered *power* goes as that amplitude
squared, so ×0.25 — which is what the first two dumps give. Independently, the wings absorb
**4.1–4.3× the light incident on them** (`f(2w₀)` ≫ 1), and no column can absorb power that never
fell on it, so the pedestal is transported core light. The leak is an artifact.

**But do not extrapolate the saturated state.** By 0.75 ps the law breaks: the 36 ppc leak *turns
over* (0.0466 → 0.0299) while 144 ppc still rises. The saturated corona is not weakly scattering,
so the ppc at which `f_ax` converges is **bounded** by this pair, not predicted by it. Two points
cannot claim convergence.

### The ~1.5× broadening: real, thermal, and it must survive

`w_eff/w₀` is 1.000 at `t` = 0 and grows to 1.62 (36 ppc) / 1.52 (144 ppc) — it does not scale with
ppc, so it is not the noise. Cause, by elimination and then by direct measurement:

- **not density.** Transverse `n_e` stays flat to **0.6 %** at every dump. And 0.75 ps of
  `c_s` ≈ 1.7×10⁵ m/s is 0.13 µm = 4 % of a waist, so it *could* not have responded.
- **temperature.** `T_e` = **248 eV on axis vs 126 eV at two waists** (36 ppc; 271/115 at 144).
  Inverse bremsstrahlung goes as `T_e^{−3/2}`, so **the spot suppresses its own coupling where it
  is brightest**, and the deposition profile ends up ~1.5× wider than the beam that made it.

Two consequences for H5 that outlive this study:

1. **the heated radius is not `w₀`.** A waist-`w₀` spot heats a ~1.5 `w₀` profile, so
   `t_cross = w₀/c_s` *understates* the crossing time and the peak `T_e` is below what a
   `w₀`-wide deposition would give.
2. **`f_ax` is not `f_abs`.** 0.39 against 0.63 here. Quoting a whole-beam absorbed fraction for a
   finite spot overstates what the axis receives by **60 %**.

### What this costs the 36 ppc runs already taken

`f_ax` reads 0.329 where 144 ppc reads 0.393 — **36 ppc under-reports the on-axis coupling by 16 %
of its own value**. The *sign* settles the cause: the 36 ppc axis is **cooler** (248 vs 271 eV),
which alone would *raise* its absorption, so the deficit is scattering loss out of the core rather
than a thermal difference. The two effects push opposite ways, which is what makes them separable.
Only the **ratio** transfers to the headline run; the 0.329 does not (thinner target, 1 ps).

### An unplanned cross-check on Phase 1.5's premise

The march is independent of ppc, the particle work is proportional to it, so from 1103 s and 2331 s:
ppc-independent cost **694 s**, particle work at 36 ppc **409 s** → march share **62.9 % at 36 ppc**,
**29.8 % at 144**. The 694 s *bounds the march from above* (it also holds the field solve and
diagnostics), and it lands within three points of the **65.6 %** the profiler reported on the
physics run. Two independent routes to the same number, so §7.5 is resting on a measurement that
reproduces.

It also marks a limit Phase 1.5 cannot lift: **a faster march does not buy ppc.** 144 ppc at the
headline geometry does not fit in 12 GB — which is why this study had to thin the target — and that
is a memory bound the march has no bearing on. Phase 1.5 buys transverse extent and sweep points;
converging `f_ax` needs a bigger card or a smaller box.

### Verdict

Hypothesis (`the leak is a resolution artifact and falls with ppc`) **confirmed**. The lesson is
the one §2.8 already taught in a different costume: a single summary number — here 7 % "in the
wrong place" — held an artifact and a real physical effect together, and treating it as one thing
would have optimised the physics away with the noise.


---

## 2026-07-29 — `P1_vac_2d_spot` completes: the operator is validated, **H5 is not tested**, and a transverse box must be sized by `v_th,e` not `c_s`

144 000 steps, 9.961 ps, 20 308 s (5 h 38 m) on GPU 0, mean 0.1411 s/step. Control
`P1_vac_2d_spot_off` complete in 10 107 s. Full write-up in the run README; figures in
`media/P1/P1_vac_2d_spot/`.

### The run stops representing a finite spot after ~2 ps

`scripts/spot_isolation.py` (new) measures the transverse profile of the **net** absorbed energy —
driven particle-KE gain minus the control's boundary drain, per band:

| `t` [ps] | 1.0 | 2.0 | 3.0 | 5.0 | 7.0 | 10.0 |
|---|---|---|---|---|---|---|
| dark/lit (\|x\|>2.5`w₀` over \|x\|<`w₀`) | **0.135** | 0.408 | 0.544 | 0.712 | 0.823 | **0.946** |
| min/max across the box | 0.069 | 0.340 | 0.477 | 0.675 | 0.793 | **0.931** |

By `t_end` the deposited energy is **flat to 7 % across the whole box**, from a beam whose wall
intensity is **1.1×10⁻⁷ of peak**. Periodic transverse faces make the run an infinite *array* of
spots at 8 `w₀` pitch; once heat crosses half the pitch the array merges.

### The cause: `v_th,e` = 10 `c_s`, and the box was sized with `c_s`

The run's `expect` block predicted lateral flow would reach the wall at (80−20)/`c_s` = **14 ps**,
beyond `t_end`. Electrons carry the energy: at the measured coronal `T_e` = 227 eV,
**`v_th,e` = 37.7 `d_e`/ps against `c_s` = 4.0**, so 80 `d_e` is crossed in **2.1 ps** — and the
measurement says contrast was lost after **1.99 ps**. Prediction and measurement agree to 5 %; the
original estimate was optimistic by **7×** purely from the wrong speed. My own
`revision_2026_07_29` fixed the heated *radius* and repeated the same `c_s` error, so it was wrong
too.

**The rule, in sizeable form:** `L_t/2 ≳ v_th,e(T_e,corona)·t_end + w₀`. For this run that is
**396 `d_e`, 4.9× the 80 used** (1 584 transverse columns against 320) — or keep the box and stop
at **`t` ≲ 1.6 ps**.

This is the **third** time this campaign has been caught by `v_th,e`: the Phase-0 blocker
(confining the ambient electron excursion needs ~2 400 `d_e` per open direction), the O2 vacuum
measurement earlier today (the forward gap is consumed at `v_th,e`, not `c_s`), and now this. It
is the same physics each time and deserves to be the first question asked of any box dimension.

### What IS established

**The operator is exact at `t` = 0, on a spatial measure** (§2.8's rule): per-column mean ratio to
`I₀exp(−(x/w₀)²)` = **1.00010**, spread 2.537 % (36 ppc shot noise), residual lag-1
autocorrelation **−0.521** (negative ⇒ neighbour exchange, not boundary pile-up), total absorbed
**5.940787×10¹² W/m** against the analytic `I₀w₀√π` = 5.940916×10¹² (**2.2×10⁻⁵** apart),
`f_abs(0)` = 0.999978.

**c817b63 regression passes on all 10 dumps.** `wall/interior` = 0.02 → 0.95, peak 1.16 — never
near the clamp's **20–25**.

**Coupling:** `f_abs` peak 1.0000, final **0.5193**; `E_abs` = **31.01 J/m**; shutoff 1.227 ps;
`Tlocalfrac` 0.432 → 0.860 (14 400 applications to t = 9.961 ps). Time-integrated on-axis coupling **0.5240 vs the 1D baseline's
0.3034** (ratio 1.73), but that number mixes two opposite finite-spot effects — lateral
rarefaction lowers it, cooler wings (`K ∝ T_e^{−3/2}`) raise it.

**H5 is untested.** `f_ax/f_abs(1D)` is 1.09 at `t` = 0, then 0.80–1.01 through 7 ps *with no
trend*, then 0.62 and 0.56 at 8 and 9 ps — entirely inside the invalid window. And the periodic
images would push the answer *toward* planar (ratio → 1), so they do not explain a drop to 0.56:
the late fall is **unexplained, not attributed**, and must not be read either way.

### Two measurement lessons

**`w_eff` is not the heated radius.** It grows 1.000 → 2.39, past the ≥1.5 lower bound the ppc
study predicted — but the shot-noise leak (16 % here) inflates the second moment. And the two
temperature weightings differ by 3×: on-axis `T_e` ends at **243 eV absorption-weighted** (the
corona the rays cross) against **81 eV density-weighted** (the bulk mass). `c_s` differs by √3
between them. State the weighting.

**The wing heating is 71 % real.** Time-integrated, 9.5 % of absorbed energy lands beyond
2.5 `w₀` (±10 %, coarse 10-dump trapezoid). Against the dark region's 9.18 J/m KE gain that is
**29 % leaked light (a 36 ppc artifact) and 71 % genuine lateral transport**. So the loss of
isolation would *not* be fixed by more particles.

### `g3_spot.py`: the premise I built it on was falsified

Restricting G3 to the illuminated columns gives **−12.93 %** against **−13.17 %** whole-box —
**×0.98**, no meaningful change. I had argued the whole-box G3 must overstate the control by
roughly the inverse illuminated fraction (~4×). Wrong, and for the reason above: the dark region
is not dark, its per-band gain being 95 % of the lit bands'. The script still earned its place —
it is the only way this could have been known, and its whole-box column reproduces
`ParticleEnergy` to **0.000 %**, which is what makes the restricted number trustworthy.

G3 = **−13.2 %**: negative, so not grid heating, but 4× `P1_vac_2d`'s −3.09 %. G6 = **−16.86 % at
2.06 % weight loss** (6.81 % of macroparticles; 12.0 % of electron macroparticles) — a bigger
deficit at a *smaller* weight loss than the planar run, because the escapers are the hot tenuous
corona.

### Deliverable

`scripts/spot_isolation.py` — a reusable check that would have caught this before 5 h 38 m of GPU
time, and which prints the box a valid run of a given duration would need. It should become a
gate.

---

## 2026-07-30 — Phase 1.5: the ray march is 11.9× faster and threads; O2's threshold falsified

`TEST_PLAN.md` §7.5. One patch, `studies/ray_march_perf/patches/o123-ray-march.patch`, against
`warpx-cda` `c817b634`. Full acceptance tables and the benchmark ladder are in
`studies/ray_march_perf/README.md`; this entry records the findings.

### What was measured

March cost per application on the real `P1_vac_2d_spot` geometry (320 rays, 704 k cells, the
t = 0 vacuum gap), non-march floor subtracted, CPU build, shared box at load ~18:

| | per application | march only | speedup |
|---|---|---|---|
| pre-change | 0.912 s | 0.678 s | 1.00× |
| O3 (reuse the end-of-step sample) | 0.788 s | 0.538 s | 1.26× |
| + O2 (skip empty steps' samples) | 0.602 s | 0.351 s | 1.93× |
| + O1 (OMP over rays, 12 threads) | 0.307 s | 0.057 s | **11.9×** |

Predicted were O3 1.17×, O1 6–8×, O2 ~2×; measured 1.26×, 6.2×, 1.53×. **Combined 11.9×
against the ~10× best case the plan allowed** — the plan was right, which is worth saying
because §7.5.2's `n_th` in the same section was not.

### O2's density threshold is FALSIFIED, and the reason generalises

§7.5.2 chose `n_th` = 3×10⁻² `n_cr` by sweeping the **discarded optical depth** and jumping the
ray analytically to the entry plane. Built exactly as written, it moved the 1D ramp CI deck's
absorbed fraction **+6.13 %** — 1.2 % below the closed form → 4.9 % above it, against a 0.48 %
tolerance. Replicating the march in Python against the operator's own density field found why:

* the skipped region there is **sub-threshold plasma, not vacuum**, so it refracts;
* refraction means the discrete march does not advance by `h` per step — it **lags the straight
  line by 1.6×10⁻³ h over 16 steps** — so an analytic jump lands the ray *ahead* of the march;
* that lead flips the discrete near-critical trigger `n_ref ≤ n_floor && drds > 0`. Pre-change it
  never fires and the ray turns by refraction alone; after the jump it fires and the analytic
  layer deposits 4.6 % of the beam in one cell. Discrete, hence skipping **one** cell and
  **four** gave the identical +6.13 %;
* not general fragility: perturbing `ray_cfl` by 1 part in 10⁷ moves the same total by 9×10⁻⁶.

**The lesson is bigger than the threshold: τ_discarded was not the only error the skip could
make, and the sweep that chose the value could not see the one that mattered.** A cheap
approximation upstream of a discrete trigger is not bounded by its own smallness.

So O2 is now what §7.5.2's first sentence claimed it was — a **no-op removal, not an
approximation**. It skips only steps whose whole extent lies in *exactly* empty field, where
`sample` provably returns `(1, 0)`, and it takes those steps with the same arithmetic in the
same order, minus the five samples. **And it costs nothing where it was supposed to pay**:
`Vskip` on `P1_vac_2d_spot` at t = 0 is **0.47**, the same 0.471 the plan measured with a
10⁻⁴ `n_cr` contour — a vacuum-ablation run's forward gap is empty to the bit.

### The race O1 would have lost silently

`A_loc`, the interpolated IB coefficient, was a variable in the enclosing scope written by every
`sample()` and read "immediately after the call whose position you mean". Threaded, each thread
would have read another's absorption coefficient: no crash, no conservation violation, plausible
smooth wrong physics. It is now an out-parameter, so it is per-caller by construction.

The parallel loop is over **accumulator buckets, not rays**. With a ray-level `parallel for`,
rays `i` and `i + n_acc` share a bucket and land on different threads whenever the thread count
does not divide `n_acc` — 12 threads and 16 buckets — which brings back both the race and the
thread-dependent summation order.

### Acceptance

* Tier 1 exact (`n_accumulators=1`): **285/285 files bit-identical** across all five CI decks;
  oblique still exactly 1/8.
* Tier 1 at defaults: every profile dump bit-identical; only the oblique `EP.txt` moves, by
  **1.3×10⁻¹⁵** (6 ULP) from the accumulator reordering.
* Tier 2: `P1_vac_2d_spot` step-0 dump **byte-identical** with O2 active; `Pabs` 5.94085×10¹².
* Tier 4: every `LASERDEP` line byte-identical at 1/2/4/8/12 threads.
* The 2–5×10⁻¹⁵ `EP.txt` thread-dependence is **pre-existing** — the pre-change binary produces
  the identical numbers. Which is why Tier 4's criterion is the operator's output: `EP` cannot
  resolve a claim about the march.

### The march is no longer the operator's cost, on CPU

Running the same benchmark with `intensity=0` executes everything except the march: **0.250 s
per application, and it does not thread** (0.248 s at 12 threads). So **81 %** of what
`applyDeposition` now costs is grid machinery — the 6-component `n_meas` and its `SumBoundary`,
the `ParallelCopy` onto one full-domain box, the pinned copies, the redistribute — plus 17 ms of
accumulators and 14 ms of `pow(kT, 1.5)`. Measured at ppc = 1, and mostly device work on a CUDA
build, so it is a signpost rather than a result.

### GPU

`build_cuda` is `AMReX_OMP=OFF` with no `-fopenmp`, so `_OPENMP` is undefined and **O1 is inert
on the production 2D binary** — it gets O2 + O3, 1.93×. `build_cuda_omp/` was configured with
`-DAMReX_OMP=ON` (which puts `-Xcompiler=-fopenmp` in the CUDA flags) as a **separate tree**, so
`build_cuda/bin/warpx.2d` stays valid whatever happens.

---

## 2026-07-30 (later) — Phase 1.5 finished on the GPU: a driven 2D step is 1.96× faster

Continuation of the entry above, after benchmarking the CUDA build and decomposing what the
operator spends its time on. Detail in `studies/ray_march_perf/README.md`.

### The headline, measured end to end on the real deck and real config

40 steps of `P1_vac_2d_spot` (36 ppc, `intervals` = 10, diagnostics off), GPU:

| | s/step | vs the laser-off control |
|---|---|---|
| `build_cuda`, pre-Phase-1.5 | 0.1453 | +108 % |
| `build_cuda_omp`, `ray_threads = 8` | **0.0743** | **+6.4 %** |
| laser-off control | 0.0698 | — |

The 0.1453 reproduces the 0.140 s/step measured before any of this, so the comparison is sound.
**The operator is now 6.1 % of a driven step against §7.5.5's ≤ 10 % target, and the step is
under its ≤ 0.080 s target.** `P1_vac_2d_spot` would take ~2.9 h instead of 5.6 h.

O1 needs a binary compiled with `-fopenmp`. `build_cuda` is `AMReX_OMP=OFF`, so
`build_cuda_omp/` was configured `-DAMReX_OMP=ON` as a **separate tree**, leaving the production
binary intact. Per application, paired back to back at load ~18: ppc = 1, **0.797 → 0.084 s
(9.4×)**; ppc = 36, **0.624 → 0.100 s (6.2×)**.

### O4, which the plan did not anticipate: the coefficient was built in the wrong place

Decomposing the operator into profiler phases that tile it showed the per-cell IB coefficient
being formed in a **serial host loop with a `pow(kT, 1.5)` per cell** — 7.9 ms of an 80 ms
application at 36 ppc — on data that lives on the device. It also forced the full-domain gather
to move all **six** components to the host, because the temperature moments were consumed only
there.

Forming it on the device instead, into the measured field over the momentum moments (dead
afterwards) plus a "measured" flag, makes the gather move **3 components instead of 6** and
retires the pinned `A_host` allocation entirely. Worth **−18 % of the whole operator on CPU**
(0.1167 → 0.0953 s per application) and ~10 ms per application on GPU. It matters more with grid
size than these runs show: it was the last O(cells) serial host work in the operator, so it
would have grown ×10 on an H5-scale spot while the march grew but stayed threaded.

Bit-identical, and the check had to be built to reach it: all five CI decks use
`temperature_mode = local` but are cold enough that `Tlocalfrac` = 0, so **Tier 1 never
exercises the measured-`T_e` path at all**. The real check is `P1_vac_2d_spot` at 36 ppc
(`Tlocalfrac` = 0.430289, three dumps byte-identical) plus the two 1D decks re-run with
`temperature_mode = fixed` (160/160 identical), a path no Tier-1 deck covers.

### What is left, and what was deliberately not done

Per application at 36 ppc on GPU: **march 79 ms, density deposit 12, kicks 3.4, gather 2.4.**
The density deposit is a standard WarpX CIC pass — 6 components × 4 corners of atomics per
macroparticle — so making it cheaper means changing how WarpX deposits, for 15 % of an operator
that is now 6 % of a step. Not worth the bit-identity burden. Raising `P_min` from 10⁻⁸ would
cut march steps but has no bit-identical version. **The operator is done.**

### Two benchmarking mistakes, both of which produced confident wrong numbers

**Retracting the "0.250 s unthreaded floor, 81 % of the operator" from the entry above.** It was
an artifact of my own harness: `profile_intervals = 1000000` does not disable the per-cell dump,
because an `IntervalsParser` period contains step 0, so every benchmark run wrote a 74 MB table
from *inside* `applyDeposition` and it was amortised into the per-application cost as 0.118 s.
Only `intervals = 0` disables a diagnostic. The corrected floor is 0.057 s at ppc = 1 on CPU and
**0.009 s on GPU**. The march speedups in that entry are unaffected — the spurious time sat in
both the total and the subtracted floor and cancelled — and are now confirmed by direct
`rayTrace` timers rather than by subtraction.

**And TinyProfiler prints the exclusive table first.** Reading the first match of a region name
gives time-minus-children, which for an instrumented `applyDeposition` is ~0.0002 s. That is
what made the harness report an application as taking no time at all. Read after `Incl. Min`.

### A reproducibility trap worth knowing about

Checking O4 on `P1_vac_2d_spot` at 36 ppc with `OMP_NUM_THREADS=4` showed 365 k of 704 k cells
differing in **n_e**, a field the change does not touch. The same binary run twice, same deck,
same thread count, differs the same way (`Tlocalfrac` 0.43034 vs 0.430789): the thermal momenta
are drawn through `ParallelForRNG` and the draws follow the thread scheduling. At
`OMP_NUM_THREADS=1` the deck is exact. Production is unaffected (`--gpu` forces 1 thread), but
**any bit-level comparison of CPU runs must pin the thread count** — including a run against its
`_off` control, where this would land inside the G3 subtraction.
