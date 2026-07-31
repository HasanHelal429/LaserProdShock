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
mode tracks an imposed 10× ramp to 0.05 %. PSC cross-validation at the **operator level is
done** (2026-08-03, upstream): the module is in hand, builds, and its compiled routines are
called directly — lnΛ agrees to 0.000e+00 and the coefficient to 6.7e-16, the whole residual
being two constants PSC rounds. Test C (the coupled expanding-plasma case) still awaits a
matched PSC PIC run.

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

---

## 2026-07-31 — Phase 1.5 validation re-runs: the spot result reproduces on the optimised operator; the planar comparison is VOID because its parent predates the clamp fix

`P1_vac_2d_omp` and `P1_vac_2d_spot_omp` are `P1_vac_2d` and `P1_vac_2d_spot` re-run on
`build_cuda_omp` with `laser_deposition.ray_threads = 8` — the same `config.yaml` but for that one
knob, which cannot change the answer. The question is not a new physics question: **does a 1.96×
faster operator reproduce a result the campaign already has?** Full suite on both (`run_checks`,
`laser_report`, `plot_fields`, `phase_space`, `make_movies`, plus `spot_report`, `g3_spot`,
`spot_isolation` on the spot run). Gates unchanged: G1 = 0.214, G4 = 0.25, G5 = 36 ppc, all PASS.

### The spot pair reproduces on every number that is allowed to be compared

| | `P1_vac_2d_spot` | `_omp` | |
|---|---|---|---|
| `E_abs` final, J per absent dim | 31.01 | 30.95 | **0.19 %** |
| `Tlocalfrac` end | 0.860 | 0.860 | — |
| G3, illuminated columns | −12.93 % | −12.86 % | 0.07 pp |
| G3, whole box | −13.17 % | −13.20 % | 0.03 pp |
| restriction changes the verdict by | ×0.98 | ×0.97 | — |
| `dark/lit` at ~1 ps | 0.135 | 0.136 | — |
| `dark/lit` at ~10 ps | 0.946 | 0.939 | — |
| contrast lost after | 1.99 ps | 1.99 ps | — |

`g3_spot`'s whole-box column reproduces `ParticleEnergy` to **0.000 %** on the re-run as well,
which is what makes the restricted number quotable at all.

`f_abs` final moved 0.5193 → 0.5284, and the planar pair's 0.5400 → 0.5848. **Neither is a
discrepancy and neither may be quoted as one** — that is the instantaneous fraction, which carries
10.4 % 1σ across RNG seed alone. `E_abs` is the comparison, and it holds.

So both of `P1_vac_2d_spot`'s findings survive the operator change intact: the run stops
representing a finite spot after ~2 ps, and its G3 is −13 %, 4× the planar run's −3.09 %.

### End-to-end speedup, measured on the real runs rather than a 40-step slice

| | parent | `_omp` | |
|---|---|---|---|
| `P1_vac_2d_spot` | 20 308 s (5.64 h) | 11 311 s (3.14 h) | **1.80×** |
| `P1_vac_2d` | 18 418 s (5.12 h) | 8 483 s (2.36 h) | 2.17× |

The spot number is the honest one: its parent ran post-clamp-fix on `build_cuda`, so 1.80× isolates
Phase 1.5. Against the 40-step benchmark's 1.96× and its "~2.9 h instead of 5.6 h" forecast — the
5.64 h was right and the 3.14 h is 8 % over, which is what a shared box costs. **The planar 2.17×
conflates Phase 1.5 with the clamp fix and should not be quoted.**

### The planar comparison is VOID, and `E_abs` is exactly the check that cannot see why

`P1_vac_2d` ran 00:49:56–05:56:54 and `P1_vac_2d_off` 01:11:56–03:08:42 on 2026-07-29. The
transverse-clamp fix is `c817b6342`, **2026-07-29 11:12:30**, and `build_cuda/bin/warpx.2d` was
rebuilt at 11:13:39. Both parents therefore ran to completion **entirely on the clamped binary** —
they are the two runs already marked invalid. `media/omp_vs_parent_planar/compare.png` is a
comparison against an invalid run and is evidence of nothing.

The trap is worth stating plainly, because it looked like a pass: `E_abs` agreed to **0.03 %**
(66.81 vs 66.79 J). It cannot be a reproduction result. **The clamp relocated energy without
creating or destroying it** — step-0 total `P_abs` agreed to 7 digits across the fix — so an energy
budget is precisely the quantity blind to this bug, exactly as all five CI tests passed throughout
it. A matching `E_abs` across the clamp fix is the expected outcome whether or not the physics
matches.

`P1_vac_2d_omp`'s declared G3 control is `P1_vac_2d_off`, also pre-fix, so its G3 is not usable
either — `run_checks`' G3 [PASS] only asserts that a control has been *declared*.

**But `P1_vac_2d_omp` itself is valid** (fixed binary, 2026-07-31), which makes it the only sound
planar 2D driven run on disk. What is missing is not the driven run — it is a matched control. The
cheap path to closing planar Phase 1.5 is therefore to **re-run `P1_vac_2d_off` alone on
`build_cuda_omp`** (~2 h) rather than re-running both; the driven half already exists. Backend
matching is the reason it must be `build_cuda_omp` and not `build_cuda`.

### The clamp regression test passes on the re-run

`spot_report`'s wall/interior column ratio — the check that is *not* an energy budget — goes 0.02
at t = 0 to **0.68 at 8.97 ps**, against the 20–25 the index clamp produced. Step-0 profile: mean
column ratio 1.00010, column-to-column spread 2.537 %. The operator deposits where it should.

### Tooling note

**Base anaconda no longer has `matplotlib`**, so `run_checks`, `laser_report` and `spot_report`
now need the `physics` env too. CLAUDE.md and `scripts/README.md` both still say the config/log
tools do not — that is now wrong for every script that draws a figure.

## 2026-08-02 — The PSC ray-trace module read against ours: **same physics to 0.46 %**, three defects in the PSC file, and PSC's unit map settles the `n_cr` question

Reference read, no runs. Sources: `psc-raytrace-master.zip` (the PSC Fortran original,
`src/PIC_part_heating.F90`, 846 lines, plus its `INIT_param.f` / `INIT_variables.f`
normalization) and Lezhnin et al., *Phys. Plasmas* **32**, 022701 (2025) — the PIC-coupling
paper our operator's header already cites. Ours is
`warpx-cda/Source/Particles/LaserDeposition/{LaserDeposition.H,LaserDeposition.cpp}`.

**The provenance matters: the zip is NOT the version the paper ran.** It carries a
`- D Petersen` attribution comment, `! CHANGED:` markers around the `l3n/l3x` z-window, and a
per-cell `get_lnlambda` that directly contradicts the paper's §II B statement that they "apply
a single value of the Coulomb logarithm to the whole simulation box" (`INIT_param.f:112` still
sets the now-dead `lnlambda = 6.0`). Read it as a later development branch, and do not attribute
its defects to the published results.

### 1. The absorption physics is the same function, to 0.46 %

Different-looking formulas, one identity. Paper Eq. (10) is

    nu_IB = (4/3) sqrt(2 pi) n_e Z e^4 lnLambda / ( m_e^(1/2) (kB Te)^(3/2) )

which is **our `m_K_coeff` verbatim** (`LaserDeposition.cpp:537-548`, with the SI `(4 pi eps0)^2`),
used as `K = (A/n_cr) n_e^2 / sqrt(1 - n_e/n_cr)` per unit **arc length**. The PSC *code* instead
uses the NRL formulary's rounded CGS coefficient (`PIC_part_heating.F90:279, 718-744`)

    K0 = 9.74e-17 * Z_eff * lnLambda
    K  = -K0 * n_e^2 / ( N_c cos(theta_0) * sqrt(1 - n_e/N_m) * Te^(3/2) )   [1/cm]

per unit **axial** length, with `N_m = N_c cos^2(theta_0)`. Evaluated head-to-head
(`xcheck.py`, λ₀ = 1.064 µm, Z = 6, lnΛ = 6):

| n_e/n_cr | T_e = 100 eV | 1 keV | 4.7 keV | 39.9 keV |
|---|---|---|---|---|
| 0.01 | 1.0046 | 1.0046 | 1.0046 | 1.0046 |
| 0.10 | 1.0046 | 1.0046 | 1.0046 | 1.0046 |
| 0.50 | 1.0045 | 1.0045 | 1.0045 | 1.0045 |
| 0.90 | 1.0040 | 1.0040 | 1.0040 | 1.0040 |
| 0.99 | 0.9981 | 0.9981 | 0.9981 | 0.9981 |

(ratio K_PSC/K_ours). The residual is entirely the rounding in `9.74e-17` and in PSC's
`N_c = 1.115e21/λ_µm^2` — its n_cr is 9.8490e20 cm^-3 against our exact 9.8477e20, which is why
the ratio dips below 1 only where `sqrt(1 - n_e/n_cr)` is sensitive to it. **There is no physics
disagreement in the absorption coefficient.** PSC's oblique factors `1/cos(theta_0)` and
`1/sqrt(1 - n_e/N_m)` are the analytically exact 1D-stratified obliquity correction, and reduce
to ours at normal incidence.

**The near-critical singular layer is the identical integral**, independently derived. Both
evaluate ∫ r²(1-r)^(-1/2) dr = `2√w − (4/3)w^(3/2) + (2/5)w^(5/2)` with `w = 1 − r_prev`, and both
double it for the round trip. PSC parameterizes the linear ramp by the *z*-slope of n_e
(by the turning density over the density slope, lines 358-389); we parameterize it by `L_eff = 1/(dr/ds)` along the
actual ray (`LaserDeposition.cpp:1217-1236`). Same closed form.

**The kick is the same operator.** Both apply a drag-free isotropic Gaussian momentum kick
`du_i = sqrt((2/3) H dt_dep) N(0,1)` per component — PSC hand-rolls Box–Muller
(`PIC_part_kick`, lines 767-813), we call `amrex::RandomNormal` — so `<dE> = m_e H dt_dep` per
electron in both. Both subcycle on the same Wiener self-similarity (PSC `heating_every = 20`
hardcoded; ours `intervals` with `gap` measured from the last applied step). Call ordering also
matches: PSC `PIC_part_source → PIC_part_heating → PIC_bin_coll` (`VLA.f:52`), ours
`TargetInjector → ParticleHeater → LaserDeposition → doCollisions`
(`WarpXEvolve.cpp:284-301`).

### 2. What PSC has that we do not: **per-cell lnΛ**

`get_lnlambda` (lines 816-845) evaluates the NRL two-branch electron-ion Coulomb logarithm per
cell from the local n_e and T_e, floored at 1. Ours takes a single constant `coulomb_log`
(default **2**, validated only `> 0`). Given how much trouble lnΛ-as-a-knob has already caused
next door (`../KinShock2020/CLAUDE.md`, collisions gotcha: lnΛ = 7713 = 667× physical), a
`coulomb_log = physical` mode that inverts the NRL formula per cell is the one substantive
capability we are missing. Note the paper's own Eq. (14) prescribes a *different* lnΛ for IB
than for transport, and the PSC code implements neither — it uses the transport form for
absorption. Worth doing properly rather than copying.

That is the whole list. Everything else runs the other way.

### 3. What we have that PSC does not

1. **Actual refraction.** PSC does not bend rays *at all*: it marches column-by-column down the
   grid-aligned z index (`cntz = cntz-1`), and oblique incidence enters only as the analytic
   `cos(theta_0)` factors. The paper says so — §II B, "we consider **1D** laser ray propagation
   along [z]". Ours integrates the eikonal equation with RK4 in arc length over
   `AMREX_SPACEDIM`, so rays refract, self-focus, and reflect off the critical surface about its
   actual normal `grad n_ref`. Nothing in PSC can represent the 2D spot physics Phase 1 measured.
2. **Drift-subtracted temperature.** PSC forms its electron temperature from the trace of the second-moment
   tensor divided by the density (`PIC_moments_xyz.f:131-145`) — the **full** second moment, so the bulk
   flow is *not* removed. In an ablation plume at Mach several this reads the ram energy as heat,
   and since K ∝ T^(−3/2) it biases absorption **low** exactly in the flowing corona. The first
   moments (`NVxe`, `NPxe`) are already computed and sitting there unused, so the fix is one line.
   Ours subtracts it (`kT = m_e(<|u|^2> − |<u>|^2)/3`, `LaserDeposition.cpp:683-684`) and adds a
   temperature floor plus a `min_macroparticles_per_cell` guard against the convexity bias of
   T^(−3/2) in thinly-sampled cells — neither of which PSC has.
3. **An energy audit.** We report `LASERDEP ... Pabs Eabs` every application. PSC accumulates no
   scalar at all; only the `laser_heating` field is written out, so absorbed energy cannot be
   checked against the incident beam. Given §4 below, that is not a cosmetic gap.
4. Deterministic threaded march (accumulator buckets, thread-count-independent reduction),
   beam profile in **physical** units (waist / super-Gaussian order / center / converging
   `beam_focus`), sub-cell ray bundling, periodic transverse wrap, and the profile + ray-path
   dumps. PSC's transverse Gaussian is centred on the domain midpoint with widths of 10 and 1 **cells**,
   hardcoded next to a comment calling them "Currently placeholders".

### 4. Three defects in the PSC file (in the version we were given)

1. **A unit inconsistency that silently discards the near-critical absorption.** Positions are
   converted to **cm** at line 246, so the march's cell-spacing variable is in cm at lines 323
   and 458 (the "in code units" comments there are stale). But the turning-point branch sets
   that same spacing from the *code-unit* cell width at **line 403**, and a comment there marks
   that a dimensionally-correct line was replaced. The absorbed power density in the
   reflection cell is therefore low by the code-length→cm factor `K_length*1e2`, which for the
   paper's normalization (K_length = D_i0,phys/√100 = 7.26e-7 m) is **≈1.4×10⁴**. That is the one
   cell the analytic singular layer deposits into, i.e. most of the absorption at normal
   incidence. Both the deposited energy and the `laser_heating` diagnostic are wrong together, so
   an absorption-profile plot would show it — further evidence this branch postdates the paper's
   FLASH benchmark. **Check with the PSC authors before trusting anything from this zip.**
2. **Hardcoded transverse indices in the no-reflection branch.** Line 554 writes
   `laser_heating_big(i1n, i2n, l3n_local)` instead of `(cntx, cnty, ...)`, and lines 504-509 read
   `Sxxe(i1n,i2n,...)` / `NNe(i1n,i2n,...)` while testing `NNe(cntx, cnty, cnt3)` with `cnt3` a
   leftover loop variable (value `i3mx+1` after the moment loop). In 2D every column that fails
   to reach critical dumps its last-cell absorption into the `(i1n,i2n)` corner. Harmless in the
   1D runs the paper published.
3. **No temporal pulse shape.** `lsr_rise_time = 0.1e-9` is declared at `INIT_param.f:124` and
   **never read anywhere** — the operator applies a constant `I_0 = 1e20 erg/s/cm² = 1e13 W/cm²`.
   The paper's pulse is 0.9 ns flat-top preceded by a 0.1 ns linear rise. **We have the same
   gap:** our `intensity` is a constant-expression parser input, not a function of `t`. Shared,
   and a real one for matching an experiment.

### 5. PSC's unit map — the structural difference, and it settles the `n_cr` question

PSC's raytrace does **not** work in the PIC code's units. `INIT_param.f:150-158` builds an
explicit code↔physical map and the operator converts into CGS before touching absorption
(density scaled by `K_density` into cm^-3, temperature by `K_temperature` into eV, and
length by `K_length` into cm, lines 244-246):

| PSC | value | meaning |
|---|---|---|
| `K_density` = critical density | 9.85e26 m^-3 | **the code density unit IS n_cr** — code density 1.0 is the critical surface |
| `K_length` = proton skin depth ratio | 7.26e-7 m | proton d_i evaluated at n_cr |
| `K_temperature` = target T_e / reduced-c parameter | 3000/0.05 = **60 000 eV** | = **m_e c², the paper's reduced electron rest energy** (§II B: "m_e c² = 60 keV") |

`ReducedSoL = 0.05` is misnamed — it is not c_red/c but the target's θ_e, and the identity the
code actually uses everywhere is `K_temperature = m_e c²_code`. `INIT_param.f:543` confirms it:
the collision rate is corrected by `ReducedSoL^2 * (511000/temp_phys)^2 = (511/60)^2`, i.e.
exactly `(m_e c²_real / m_e c²_code)^2`.

**Two consequences for us.**

**(a) n_cr is a chosen parameter, not a wavelength.** PSC picks n_cr as the density unit and lets
λ₀ follow. Ours derives `m_n_cr` from `wavelength` alone with **no override path**
(`LaserDeposition.cpp:523-526`), so to place the critical surface at a chosen code density we
must solve backwards for λ₀. This independently confirms the corrected claim in
`../KinShock2020/README.md` ("n_cr is a dimensionless parameter, not 351 nm") and is the
strongest argument yet for the ranked change *accept `critical_density` directly*. The paper also
supplies the number that kills the density-contrast worry outright: real solid Al is
**n_e,solid ≈ 700 n_cr**, but PSC caps the target at **n_max,PIC = 10 n_cr** and Appendix A scans
**2–20 n_cr** with all runs converging. A few × n_cr is enough. There is no 10⁵ contrast
requirement.

**(b) Our T_e for the IB coefficient is ~8.5× too hot, and the fix is cheaper than the README
says.** WarpX has no reduced c, so `electron_temperature` is literal: R1_warm's θ_e = 0.078 means
T_e = **39.9 keV**, not the few keV a real ablation plasma has. At 0.5 n_cr the absorption length
is **6.6 cm at 39.9 keV vs 2.7 mm at 4.7 keV** — the difference between a transparent plasma and
an absorbing one. The `../KinShock2020/README.md` section derived a rescaling factor
s = √(39900/470) = **9.21** by targeting T_e,ab ≈ 470 eV. But the paper does not target 470 eV: it
runs m_e c² = 60 keV at I₀ = 1e13 W/cm² and matches FLASH. Adopting *the paper's own* reduced rest
energy gives

    s = sqrt(511/60) = 2.92 :  theta 0.078 -> 0.00916 (T_e = 4.68 keV),
                               vA_over_c / 2.92,  max_step x 2.92

— **2.9× the timesteps, not 9.2×** — and Appendix A scans m_e c² ∈ {20, 60, 200} keV and
m_p/m_e ∈ {100, 400} and finds convergence, so this is a *validated* reduction rather than a
guess. The README's 9.2× / 470 eV framing should be corrected to this.

**Caveat, not yet worked through.** Lowering θ at fixed m_e (what a WarpX config can do) is *not*
identical to raising m_e at fixed θ (what PSC does): both give T_e ÷ s² in eV, but PSC's d_e in
cm grows by s while ours does not, so the absorption length measured in d_e differs by s = 2.92
between the two routes. Since n0 is otherwise a free scale factor here, that is absorbable by
rescaling n0 (and B₀ ∝ √n0 with it), but the four knobs (θ, B₀, n0, λ₀) are coupled and the
algebra has **not** been checked. That coupling is the argument for a derived `laser.target`
block in `units.py` — PSC parameterizes by (n_cr, T_target, m_e c², µ) and *derives* its four K
factors; our config parameterizes by (n0, θ, B₀, λ₀) and derives nothing laser-facing. Writing
that map is the concrete next piece of work, and it is a prerequisite for any quantitative
PSC↔WarpX cross-validation.

**Bottom line for the campaign.** The operator is not the risk. Absorption coefficient, the
near-critical closed form, and the kick all agree with the reference implementation to rounding,
and on refraction, temperature measurement, and energy accounting ours is the stronger of the
two. The gaps worth closing before a validation campaign are, in order: **(i)** a physical
per-cell lnΛ, **(ii)** the temperature scale — either the rescaled config above or a derived
`laser.target`, and **(iii)** a temporal pulse profile, which neither code has.

## 2026-08-02 (later) — Per-cell Coulomb logarithm: `laser_deposition.coulomb_log_mode`, and lnΛ = 2 was ~3.6× too low

The one capability the PSC comparison above found us *missing*. Built, verified against the
C++ from an independent Python implementation, and against the pre-change binary for
bit-identity. No production runs.

### What it is

`laser_deposition.coulomb_log_mode`, four modes. The three per-cell ones evaluate lnΛ from
the local `(n_e, T_e)` — the **same** values, and the same sparse-cell fall-back, that set
`T_e` in the coefficient — floored at 1, and 1 where there is no plasma (as PSC's
`get_lnlambda` does; such a cell contributes nothing to `K ∝ n_e²` and is reached only
through edge interpolation).

| mode | lnΛ | why it exists |
|---|---|---|
| `constant` (default) | `coulomb_log` | the **knob**. Not a fallback: pinning lnΛ is the only way to hold collisionality fixed while something else varies. |
| `nrl` | NRL e–i, two branches at `T_e = 10 Z²` eV | the **transport** logarithm, *not* the absorption one. Exists solely to cross-validate against PSC, which uses it for IB. |
| `flash` | `ln(b_max/b_min)`, `b_max` = λ_D, `b_min` = max(classical, de Broglie) | Eqs. (11)–(13) of Lezhnin 2025, i.e. FLASH's IB logarithm. For reproducing that paper. |
| `ib` | the same with `b_max = v_th/max(ω_pe, ω_laser)` | **the physical one.** Correction (I) that Lezhnin et al. recommend over the FLASH operator they were constrained to use. |

**Why `ib` is the right default choice for physics.** Below critical `ω > ω_pe`, so `b_max`
becomes `v_th/ω` — a length with **no density dependence**. lnΛ therefore *saturates* at its
critical-surface value all the way out into the corona, instead of growing like
`½ln(1/n_e)`. That growth is the unphysical part: an encounter lasting longer than `1/ω`
is adiabatic and absorbs nothing from the wave. Above critical `ω_pe` wins and `ib` reduces
to `flash` exactly. Measured on `run_profile_ramp` (θ_e = 2e-3, Z = 1, λ₀ = 1.053 µm):

| n_e/n_cr | `nrl` | `flash` | `ib` |
|---|---|---|---|
| 0.9996 | 6.7499 | 7.3157 | 7.3155 |
| 0.2002 | 7.5539 | **8.1197** | **7.3155** ← saturated, to all 10 digits |

### Verification

1. **`constant` is bit-identical.** `run_profile_ramp` re-run against the *pre-change* binary's
   `run.log`: `Pabs` and `Eabs` match on **all 60 steps**. The warm/local-temperature path too
   (`run_te_gradient`, `Pabs 2.2216e+12 Eabs 0.022216 Tlocalfrac 1`, exact at OMP=4 and 8 —
   OMP=1 differs by the *known* thermal-RNG/thread-scheduling effect, not this change). The two
   constant-lnΛ expressions were deliberately left in their original floating-point form rather
   than factored, so this is guaranteed rather than measured lucky.
2. **Per-cell lnΛ matches an independent implementation** to **<4e-9** across all three modes
   and both `fixed` and measured-`T_e` paths, and `A = C0 lnΛ/(kB T_e)^{3/2}` round-trips to
   3e-9. `tests/test_units.py` now pins all four modes against values read out of these runs,
   so the Python mirror is checked against the C++, not against itself.
3. **`flash`'s b_max/b_min IS the paper's closed form** — `ln(λ_D/b_cl)` agrees with the code's
   `ln((v_th/ω_pe)/b_cl)` to **0.00e+00** at three (n_e, T_e). Note the classical `b_min`
   dominates only below **9 eV** (Z=1) / **327 eV** (Z=6), so at keV the de Broglie branch wins
   and citing Eqs. (11)–(13) rather than the classical-only Eq. (14) is the correct claim.
4. **All five WarpX CI decks pass** (1D, 1D-ramp, 2D gaussian/oblique/focus), worst relative
   error 1.6% against tolerances of 5–6%. 2D and `temperature_mode = fixed` both exercised,
   including the branch where component 2 is not gathered.
5. **213 tests pass** (was 202; 11 added).

### The number that matters

On `run_profile_ramp`, going from the deck's `coulomb_log = 2.0` to the physical value:

    lnLmean  2.0  ->  7.25 (ib) / 7.30 (flash) / 6.74 (nrl)
    Pabs     6.05e12 -> 9.66e12 W   (x1.60)

**lnΛ = 2 was understating absorption by ~1.6× on this deck, and the P1 runs used 5.0.**
τ_tot goes 0.446 → 1.63, i.e. absorbed fraction 0.59 → 0.96. Anything that was tuned against
absorbed fraction with a guessed lnΛ needs re-reading, and `Z_eff·lnΛ` is no longer one knob:
`Z_eff` stays a knob, lnΛ can now be physics.

### Three things fixed on the way

- **The profile dump's θ_e was inverted out of A** (`theta = (C/A)^{2/3}`), which is only valid
  while lnΛ is constant and would have *silently* misreported it in a per-cell mode. Component 2
  of the measured field now carries the measured θ_e itself instead of a 0/1 flag — `> 0` is the
  same test the flag satisfied, so `Tlocalfrac` is unchanged to its last digit — and the dump
  reads θ_e directly and derives lnΛ from it exactly. A new `lnLambda` column reports it per cell.
- **Appending that column made the positional `PROFILE_TAIL` scheme ambiguous**: 7 trailing
  columns is 1D-with-lnΛ or 2D-without, 8 is 2D-with or 3D-without. `io.read_profile_table` now
  names columns from the dump's **own header row** (the operator always wrote one; nothing read
  it), with the count-based scheme kept only as a fall-back, and `studies/ray_march_perf/
  compare.py` was routed through it instead of duplicating the logic. Old dumps stay readable.
- **`coulomb_log_mode` is emitted only when the config asks**, matching the ray-march knobs.
  Emitting it unconditionally would have rewritten **24 completed runs' decks** for a semantic
  no-op; the operator's default is `constant` and bit-identical to having no such option.
  `--verify` catches it in both directions (`tests/test_structures.py`).

### Still open from the PSC comparison

`lnLmean` is now on every `LASERDEP` line and per cell in the dump, so (i) is closed. Remaining,
in order: **(ii) the temperature scale** — our θ_e = 0.078 means a literal 39.9 keV where a real
ablation plasma is at keV, fixable either by the 2.92× config rescale to the paper's
m_e c² = 60 keV or by a derived `laser.target` block; and **(iii) a temporal pulse profile**,
which neither code has.

## 2026-08-03 — PSC cross-validation, run for real: the two modules are the **same function** to round-off, and PSC's coefficient is computed in single precision

The 2026-08-02 entry compared the PSC ray-trace module against ours *by reading it* and put
the agreement at "0.46 %". With `psc-raytrace-master` now in hand that estimate has been
replaced by a measurement, and the number is much better than 0.46 %: the residual is
**entirely** two constants PSC rounds, and once those are accounted for the two codes agree
to machine epsilon. This closes the `LASER_DEPOSITION_PLAN.md` checklist item *"Build PSC
reference data (uniform slab + density ramp) and analytic IB baselines"*, blocked since
2026-07-27 on module access.

### Two things that made this cheaper than expected

1. **PSC builds and runs unmodified here.** The zip is a complete autotools distribution
   (the Fortran PSC 1.90 — `VLI` initializes, `VLA` runs), not just the module. It compiled
   clean on the first attempt with gfortran 13: `h5pfc` supplies MPI + parallel HDF5 in one
   wrapper, and `-std=legacy -fallow-argument-mismatch -fallow-invalid-boz` are what a
   1.90-era tree needs from a modern compiler. Recipe in `psc_reference/README.md`.
2. **Its routines are callable directly**, so **nothing was ported.**
   `laser_deposition/psc_reference/{psc_kref,psc_march}.F90` link PSC's compiled objects and
   *call* `get_lnlambda`, `absorption_calc` and `trapazoidal_int`. Every PSC digit below is
   produced by PSC's own code; the drivers only supply the caller's context (CGS-with-eV
   units, `Nc = 1.115e21/λ²`, `K0 = 9.74e-17·Z·lnΛ`), copied from
   `PIC_part_heating.F90:244-249,279`.

   Watch out: `src/Makefile.am` names `PIC_part_heating.f`, which does not exist — automake's
   suffix rule picks up the `.F90`. Confirmed with `nm` that it is what lands in `VLA`.

### The result

`scripts/compare_psc_coefficient.py`, over a 1681-point (n_e, T_e) map spanning 1e-3–0.999
n_cr and 1 eV–100 keV:

| check | result |
|---|---|
| lnΛ: PSC `get_lnlambda` vs our `coulomb_log_mode = nrl` | **0.000e+00**, all 1681 points |
| — coverage | both NRL branches (1600 / 81 points) **and** 81 points on the floor of 1 |
| IB coefficient, PSC's rounded constant accounted for | **6.7e-16** |
| PSC's `trapazoidal_int` vs the plain trapezoid | **2.2e-16** |
| PSC `9.74e-17` vs the exact `9.694430e-17` (Lezhnin Eq. 10) | **+0.4701 %** |
| PSC `1.115e21/λ²` vs `ε₀m_eω²/e²` | **+0.0131 %** |

**The `nrl` mode was worth building.** It was added on 2026-08-02 purely to be
PSC-comparable, on the argument that PSC uses the NRL *transport* logarithm for inverse
bremsstrahlung. That argument is now confirmed at the bit level — exactly zero difference,
including the `T_e = 10 Z²` eV branch switch and the floor.

### PSC's absorption coefficient is formed in single precision

The coefficient constant (`PIC_part_heating.F90:279`) is *written* as `9.74e-17`, but it is
assembled from literals that carry no double-precision suffix, so it is formed in **single
precision** and only then promoted to the double precision of everything around it.
gfortran folds it to **9.73999943499718752e-17**, i.e. **5.80e-8 below** the intended
`9.74e-17`. Established two independent ways — backed out of PSC's own output (constant to
1.1e-15 across the table) and by compiling the literal alone.

Physically this is nothing. It is recorded because it is the difference between explaining
the comparison's residual to 1e-15 and leaving 6e-8 of it unexplained; the script therefore
predicts with the value PSC *computes*, not the value it appears to write.

### The compiled C++, not just a Python mirror

`laser_deposition/run_psc_xcheck/` is a probe deck: 512 cells sweeping **0.013–0.911 n_cr and
279 eV–21 keV simultaneously** (density and temperature ramped anti-correlated), one step, no
field solver. Each cell's *measured* `(n_e, θ_e)` is read out of the operator's own profile
dump and handed to PSC, so particle noise in the temperature cancels exactly rather than
degrading the comparison.

| | |
|---|---|
| lnΛ, compiled C++ vs PSC | 4.7e-9 |
| `A = pref·Z·lnΛ/(k_BT_e)^{3/2}` self-consistency | 8.5e-9 |
| `A_PSC/A_C++` vs the predicted +0.4701 % | 7.8e-9 |
| optical depth τ, same trapezoid on both coefficient sets | **+0.4067 %** — the coefficient offset, nothing else |
| operator's own RK4 march vs midpoint quadrature of its own K | −0.291 % |

All the 1e-9s are the dump's ~9-significant-digit print precision, i.e. as tight as this
comparison can be made without a wider dump format.

### `psc_march` is sub-critical only — scope, not shortcut

PSC's turning-point branch (`PIC_part_heating.F90:350-478`) takes its cell spacing from the
PIC **code-unit** cell size at line 403, where every other length in the march — including
the same spacing variable at line 323 — is in **cm** (converted at line 246). That is the
dimensional inconsistency flagged on 2026-08-02, and it means the near-critical layer is not
a meaningful reference to compare against. `psc_march` therefore refuses to march past the
turning-point density and says so.

### Two traps worth keeping

1. **`laser_deposition.electron_temperature` is the FLOOR in local mode.** Set to the *top*
   of a temperature ramp rather than below its bottom, it binds in essentially every cell:
   `Tlocalfrac` collapses to 5e-5 and the run silently measures nothing, degenerating to a
   single temperature. Cost one wasted run here; now documented in the deck.
2. **Integrate the full domain when K peaks at a boundary.** On this profile K rises three
   decades toward the dense end, so the hi-end *half*-cell alone carries ~2.2 % of τ. A
   cell-centre trapezoid drops a half-cell at each end and makes the operator look 2 % off;
   the midpoint rule over all 512 cells gives −0.291 %. The code-to-code *ratio* is immune
   (both sides truncate identically), which is why (b) and (c) above use different bases.

### What Test C is now about

Not the operator. The coefficient and the march are both settled above, free of PIC
confounders — different pushers, different collision modules, and PSC's
`PIC_moments_xyz.f:131-145` doing **no drift subtraction** where ours does. Test C is now
specifically about the *coupled evolution*, and it is no longer blocked on access: PSC runs,
and already dumps its per-cell `laser_heating` (`OUT_moments.f:441`,
`dowrite_laser_heating = 1` at `INIT_param.f:803`). It is blocked on work — PSC is configured
at compile time (`INIT_param.f` + `CASE_nVT.f`, no runtime deck), so a matched case means
editing those, rebuilding, and reading its output format.

### Provenance caveat (unchanged, and now stronger)

This tree is **not** the version behind the published results: `INIT_param.f:379-411` carries
commented-out reads of `/home/klezhnin/flash_01_ns_I1e13_lb_{dens,etemp,itemp,veloc}.txt`,
the module carries `! CHANGED:` markers, and `get_lnlambda` computes lnΛ **per cell** where
the paper states a single value. Those FLASH-profile paths also identify it as Lezhnin's own
working copy. Nothing from this code should be attributed to the paper's results without
checking with the authors.

## 2026-08-03 (later) — Test C closed: a matched PSC PIC run says our absorption operator is right to 0.017 %, and it found a 27 % bug of ours on sharp density edges

The earlier entry today settled the *operator* against PSC (coefficient and march) by
calling PSC's compiled routines. This closes the **coupled** case — a real PIC-to-PIC
comparison, which is the part with no closed form and the only reason a matched PSC run was
needed. Upstream: `warpx-cda/laser_deposition/run_testC_match/`,
`scripts/compare_testC.py`, figure in `media/testC/`.

### Scored as a three-way, deliberately

Diffing two independent PIC codes' absorbed fraction conflates *do the operators agree*
with *did the particle loading produce the same plasma*. Running PSC's compiled march on
WarpX's **own measured profile** separates them:

| | |
|---|---|
| WarpX's march vs its own coefficient field | τ 0.428390 vs ∫K dz 0.427948 — ratio **1.00103** |
| **PSC's march on WarpX's own profile** | τ 0.429887 — ratio **1.00453** vs predicted **1.00470** → **0.017 %** |
| end to end, each code's own run at t≈0 | f_abs PSC 0.354490, WarpX 0.348443 — **+1.74 %** |
| — operators account for | **+0.28 %** |

So the operators agree to 0.017 % of the independently predicted coefficient offset, and
the remaining ~1.45 % is the two codes realizing slightly different plasma from the same
prescription — not different physics. Both show the expected `K ∝ T_e^{-3/2}` self-limiting
decay (PSC 0.3545 → 0.3515, WarpX 0.3484 → 0.3386 over ~320 fs).

### Test C found a real bug in OUR operator: 27 % over-absorption on a sharp edge

On a **top-hat** slab the operator reported **τ = 0.615 where its own per-cell coefficient
field integrates to 0.449** — the excess sitting at *both* slab edges (+56 %, +70 %) with
the interior slightly low — and recovered to **≤0.2 %** as soon as thermal motion smoothed
the edge over a few cells. Every later application in that run agreed to 0.2 %.

Ruled out, each by re-running and getting a **bit-identical** `Pabs`: `vacuum_skip`
(`=0` changes nothing) and the boundary condition (periodic → pec/absorbing changes
nothing). So it is the density discontinuity itself. A real target always has a finite
scale length, but a sharp-edged foil deck would hit this, and it should be fixed or
documented before any upstream PR. It is why the Test C profile is a tanh taper.

### Only t ≈ 0 is matchable, and the reason is the reduced parameters

PSC's code velocity unit is `K_length/K_time` = 2.397e7 m/s = **c/12.51**, and its mass
unit is `m_p/100` = **18.4 real electron masses** — together giving m_e c² = 60 keV. Two
consequences, both structural:

1. **`algo.maxwell_solver = none` is forced.** PSC's dt is **6.63× the real 1D Courant
   limit** (stable there only because its own c is 12.5× smaller), so a WarpX run at the
   matched cadence cannot also solve Maxwell. Test C as scored is a test of the
   absorption-and-deposition coupling, not of EM propagation.
2. **Only the first application is an exactly matched state.** PSC's electrons move 4.3×
   slower at the same 300 eV, so the profile evolves on a different clock. Both codes
   therefore heat *every* step so the first application lands on the prescribed initial
   condition; the later history is a trend comparison. The visible gap in the history is
   that mass ratio, not an absorption disagreement.

Matching absolute `n_e` in cm⁻³ and `T_e` in eV *does* match K, because PSC's absorption
routine works in real physical units internally even though its dynamics do not. This is
the reduced-parameter caveat of §II made concrete, and it is the same one that bites
`R1_coll` in KinShock2020: **the knob that buys both is µ_p = 1836, not a reduced c.**

### Particle noise had to be controlled before any of this meant anything

`K ∝ T_e^{-3/2}` is convex, so per-cell temperature noise biases K **upward** by
≈(15/8)σ². At the smoke test's 20 electrons/cell that is ~6 % on K and ~5 % on f_abs — an
order of magnitude larger than the effect being measured — and it moved PSC's own answer
visibly: **f_abs 0.3809 at 20 e/cell vs 0.3688 at 400.** Both codes now run 400
electrons/cell, so the residual bias is common to both rather than a difference between
them. Worth remembering for any absorbed-fraction number quoted from a thinly-sampled run.

### Practical notes on running PSC

Configured entirely at **compile time** (no runtime deck): `INIT_param.f` for grid, ranks,
`NNpart`, target density/temperature and `heating_every`; `CASE_nVT.f` for the profile.
`VLI` is the fresh-start program, `VLA` the restart path. Output goes to `./data`. `znpe`
must divide the z cell count (1250 = 2·5⁴, so 10 works and 8 does not). The reference
configuration targets **768 MPI ranks**; the workstation values are a deliberate reduction.
27 s for 100 steps with 3.4 M particles on 10 ranks.

PSC-side patches (including a reporting-only absorbed-fraction diagnostic that emits
`LASERDEP` lines in WarpX's format) live with the PSC tree outside both repositories, since
the module is unreleased — see the sensitivity rules in
`warpx-cda/laser_deposition/psc_reference/.gitignore`.

## 2026-08-03 (later still) — the 27 % sharp-edge over-absorption: it was the temperature **floor** leaking through the coefficient interpolation

Fixed. Test C found this yesterday-in-the-same-day; this is the cause and the cure.

### Cause

`sample` interpolated the inverse-bremsstrahlung coefficient `A` **plainly** across the
plasma boundary. An empty cell's `A` is not meaningless-but-harmless — it is built from the
**temperature floor**, and

    A ∝ (k_B T_e)^(−3/2)

so a floor far below the plasma temperature makes it *enormous*: **0.511 eV against 300 eV
is a factor 2240**. Averaging that into a cell half full of plasma inflated K at both slab
edges by hundreds of times, and the operator reported **τ = 0.615 where its own per-cell
coefficient field integrates to 0.449**.

The in-code comment asserting this was "second order, since n_e² → 0" was wrong, and is
corrected in place: at a sharp edge the *interpolated* n_e is ~half the plasma density, so
it is a first-order error, not second.

**This inverts the stated purpose of the floor.** The header says the floor exists so that
"noise in a thinly-sampled cell cannot produce a wild coefficient" — but because
`A ∝ T^{−3/2}`, a *low* temperature floor is a *high* ceiling on A. A floor set well below
the plasma temperature does the opposite of what it is for. Worth remembering when choosing
`electron_temperature` in local mode: it is not a harmless "don't bind" knob.

### Why it hid

On any smooth profile every cell adjacent to plasma also *holds* plasma, so no
floor-temperature `A` is ever in the stencil. Even a run that starts sharp self-heals —
thermal motion smoothed the edge within one heating interval and the error fell from +37 %
to ≤0.2 % by the third application. Only a profile that is discontinuous *at the moment the
operator fires* shows it.

### How it was localised — three wrong guesses, each killed by measurement

1. **`vacuum_skip`** — re-ran with `vacuum_skip=0`: **bit-identical** `Pabs`. Not it.
2. **The boundary condition** (a ray wrapping through a periodic axis and re-traversing the
   slab) — re-ran with `pec`/absorbing: **bit-identical**. Not it. (`wrap[axis]` is
   unconditionally false, so the axis always terminates — the code is right there.)
3. **The quadrature / eikonal drift** — a Python model of the march reproduced **0.449**,
   not 0.615, and the `|T| = n_ref` invariant drifted only 0.998–1.003. Not it.

Then putting the floor-temperature `A` into the vacuum cells of that same model reproduced
**0.612** against the operator's 0.615, and the diagnosis was settled.

### Fix

Interpolate `A` **weighted by n_e**:

    A_out = Σ w·A·n_e / Σ w·n_e

`A` is a property of the electrons in a cell, so a cell with none gets no vote. Exact in
both limits that matter — uniform n_e reduces to the plain average, uniform `A` returns that
`A` — so it changes nothing except where **both** fields vary, which is precisely the edge.

| | before | after |
|---|---|---|
| sharp-edge τ vs its own coefficient field | **1.37** | **0.994** |
| Test C tapered case, f_abs | 0.348443 | 0.348431 |
| WarpX `laser_deposition` CI | 12/15 | 12/15 (same 3 pre-existing 2D checksum failures) |

The Test C number barely moving is the point: it confirms the taper never triggered the bug,
so **the Test C result against PSC stands unchanged**.

### Guard

`run_sharp_edge/` upstream keeps one deck whose density is genuinely discontinuous, with
`scripts/check_sharp_edge.py` comparing the operator's absorbed fraction against a
quadrature of its *own* dumped coefficient field — a ratio, so there is no analytic
reference, no PSC tree, and no hard-coded number to go stale. Its temperature floor is
deliberately pathological; a realistic one would mask the regression. Not yet a CTest —
that is the follow-up before any upstream PR.

---

## 2026-08-04 — `refraction = 0`: straight rays with the refraction carried analytically. It is *exact* for a stratified target, 3.2× cheaper, and it exposed a turning-point double count

For many of the applications this operator is for, the transverse ray deflection is not the
answer wanted — the absorbed power is. PSC's module already works that way, so the flag
`laser_deposition.refraction = 0` now does too. Landed on `warpx-cda`
`feature/laser-deposition`.

**PSC has no ray trace at all**, which is the finding that shaped the design. Its heating
routine walks straight down the grid axis, one column per transverse cell, and carries the
obliquity as a constant `1/cos θ₀` path factor with a turning point at `n_m = n_cr cos²θ₀`.
Reading that as "PSC neglects refraction" would be wrong, and building the flag that way
would have been a bug:

**For a plane-stratified target, a straight march carrying the Snell invariant is EXACT at
any incidence angle.** With `n sinθ = sinθ₀` and `n = √(1−n_e/n_cr)`,

```
cosθ = cosθ₀ √(1 − n_e/n_m) / n ,     n_m = n_cr cos²θ₀
dτ/dz = (A/n_cr) n_e² / ( cosθ₀ √(1 − n_e/n_m) )
```

and per unit **arc length** of the straight march (`dz = cosθ₀ ds`) the `cosθ₀` cancels. So
the entire change from the refracting mode is one substitution,
`√(1−n_e/n_cr) → √(1−n_e/n_m)`, in the absorption denominator, the turning test, and the
analytic near-critical layer. At normal incidence `n_m = n_cr` and the two modes coincide.

**Scored against an analytic reference, not against the other mode.** The linear-ramp closed
form `τ = A n_cr z_crit (16/15) cos⁵θ₀` — the same one `analysis_oblique.py` validates the
*refracting* mode against — is derived by integrating along the **curved** path, so a march
that never bends a ray has no obvious right to satisfy it:

| θ₀ | `refraction = 1` | `refraction = 0` | no Snell factor would be |
|---:|---|---|---|
| 0° | −0.60 % | **−0.22 %** | τ ×1.0 |
| 15° | +0.05 % | **−0.18 %** | τ ×1.2 |
| 30° | +0.13 % | **−0.14 %** | τ ×2.4 |
| 45° | +0.58 % | **−0.32 %** | τ ×8.0 |
| 60° | +1.99 % | **−0.17 %** | τ ×64.0 |

**The cheap mode is the more accurate one here.** It is flat in angle, while the refracting
trace drifts to +1.99 % at 60° where its RK4 has to resolve an increasingly bent path. The
last column is what the flag is *not*: a genuinely unrefracted ray keeps the `n_cr`
denominator, so nothing turns it before the true critical surface and it marches to a depth
it should never reach — overestimating τ by `1/cos⁶θ₀`, **64× at 60°**. That is the failure
signature to look for if this ever regresses.

**Cost: the ray march is 3.2× faster** (36.0 → 11.1 ms per application on a 256-ray bundle,
from the `LaserDeposition::rayTrace` timer rather than wall clock). Five field samples per
step become two, and each drops the density gradient — the expensive half of the
interpolation. The turning angle is taken per-ray from its own launch direction, the same
thing for a parallel beam and the right thing for a converging one.

**The limit is measured, not asserted.** A stratified sweep can only ever show this mode
agreeing, so `run_refraction/inputs_refraction_corrugated` breaks the stratification on
purpose: a corrugated density front, 12.5 % depth modulation, normal incidence.

| | total absorbed | transverse contrast of P_abs |
|---|---|---|
| `refraction = 1` (reference here) | 9.4078e10 W/m | 4.086 |
| `refraction = 0` | 1.0210e11 W/m (**+8.5 %**) | 0.089 |

The integral is the forgiving number; the pattern is not. Straight rays cannot be steered out
of the ridges, so every column absorbs the same and the corrugation is invisible to them —
the straight-mode total is 8× the flat-ramp 0° value to the digit, which is the check that
this is the mode behaving as designed rather than misbehaving. The figure shows it as the
operator's **own dumped ray paths**: the refracting bundle leans out of the ridges and
crosses itself into caustics over the valleys, the straight bundle is a picket fence that
turns at the corrugated surface and returns along its own path. **If the transverse
deposition pattern is what a run is for, this flag is the wrong economy.**

### What building it found: a turning-point double count, in both modes

The step that reaches the turning surface was absorbing **twice** — once by the step's own
midpoint rule, and again through the analytic near-critical layer, which covers exactly that
interval (`r_prev` up to the surface) and back. Worse, that step *overshoots* the surface, so
its midpoint denominator was the clamped `√n_floor2` rather than a physical one, inflating K
there by up to `1/n_floor` = 100.

It was worth **~5 % of the absorbed fraction** at the default `ray_cfl` on the oblique ramp
(+4.88 % before, −0.14 % after) and decayed only as **O(h)** — so recovering the accuracy by
refining would have needed an 8× smaller step, spending the entire 3.2× the mode exists for.
This is why the fix is part of the feature and not a follow-up.

**Why it hid.** In the refracting mode the branch fires only at near-normal incidence, on one
step of one ray, and the error sat inside the 6 % test tolerance *in both directions* —
measured −1.2 % to +2.5 % across `ray_cfl` on the 1D ramp, i.e. non-monotonic, which reads
as noise rather than as a bug. The straight-ray mode is what made it matter, by turning
**every** oblique ray at `n_m` instead of no ray at all.

**Fix**: decide whether a step reaches the turning surface *before* applying its absorption,
and let the analytic layer own that interval alone. Verification:

- refracting mode at oblique incidence — **bit-identical** (its branch never fires there)
- refracting mode, 1D ramp at default `ray_cfl` — **bit-identical**; at finer steps it
  improves toward the closed form (+2.53 % → +1.80 % at `ray_cfl` 0.0625)
- Test C `f_abs` **0.348431** and the sharp-edge guard **0.58 % PASS** — both reproduce to
  the digit, as expected since both are sub-critical and have no turning point
- `ctest -R laser_deposition` **14/17**: the new straight-ray test passes both stages, and the
  3 failures are the same pre-existing 2D checksums (`oblique`, `gaussian`, `focus`)

**In CI**: `test_2d_laser_deposition_straight` is the existing oblique deck plus the one
flag, checked by `analysis_oblique.py` **unchanged** — because both modes must satisfy the one
closed form, which is the property worth pinning. No checksum; the physics assertion is the
test.

**Still open, and pre-existing**: the refracting mode's near-critical layer at *normal*
incidence is now the weakest number in the operator — −1.2 % to +1.8 % across `ray_cfl`,
non-monotonic. That is the singular layer itself, where the ray genuinely reaches `n_cr`, and
it is separate from the double count fixed above.

Study: `warpx-cda/laser_deposition/run_refraction/` + `scripts/compare_refraction.py`
(figure: `media/refraction/refraction_modes.png`, gitignored/regenerable). Docs:
`laser_deposition.refraction` in `Docs/source/usage/parameters.rst`.

---

## 2026-08-04 (later) — WarpX vs PSC at **oblique** incidence: the cross-check `refraction = 0` unlocks. Coefficient exact to ten digits, march to 0.004 %

Every earlier PSC cross-check was at **normal incidence**, and not by choice. Away from it
the two codes were not computing the same quantity: WarpX bent its rays with an RK4 eikonal
trace and integrated K along the curved path, while PSC marches straight down the grid axis
with a `1/cosθ₀` path factor and turns at `n_m = n_cr cos²θ₀`. Both are right for a
stratified target, but they are different algorithms, so an oblique disagreement could not
have been attributed to anything. `refraction = 0` **is** PSC's algorithm, so the obliquity
treatment is now directly testable — and it was the part of the new mode that had only ever
been checked against a closed form.

**Sub-critical by design, not convenience.** PSC's turning-point branch sets `dzs = dz` in
PIC code units where every other length in its march is in cm, so **its near-critical layer
cannot be a reference** (`psc_march` refuses to run past `n_m` for that reason). Peak
density 0.18 n_cr stays below `n_m = 0.25 n_cr` even at 60°. The Snell denominator is still
properly exercised: `1/√(1−n_e/n_m)` runs **1.10 → 1.89** across the sweep. Fixed T_e, to
keep the `T^{-3/2}` convexity bias out of a measurement that is not about it; lnΛ still
per-cell (`nrl`), as PSC's `get_lnlambda` is.

### 1. Coefficient — reproduced to every digit printed, at every angle

PSC's compiled `absorption_calc` vs the straight-ray expression, 0–60°: deviation
**0.000000 %** at all five angles.

The target is **not 1.0** — PSC rounds two constants (IB prefactor `9.74e-17` vs the exact
`9.694430e-17`, and `n_cr = 1.115e21/λ²`), so the correct answer is a predicted **+0.457 %**
offset, and hitting 1.0 would mean something known-to-be-there had cancelled.

**The residual initially drifted with angle (−0.017 % at 60°), and chasing it paid off.**
PSC's rounded `n_cr` appears **twice** in K: once as the explicit `1/n_cr`, and again inside
`n_m` *under the square root*, so the codes evaluate `√(1−n_e/n_m)` at slightly different
arguments. That second appearance is amplified by `r/(2(1−r))` toward the turning point —
0.11× the n_cr error at r = 0.18, **1.29× at r = 0.72**. Including it collapses the residual
to zero to ten digits. Nothing about the oblique coefficient is unexplained.

### 2. March — the code-level test, ≤ 0.004 %

PSC's compiled march on WarpX's **own measured** profile, against the optical depth the C++
operator reported. Nothing on the WarpX side is a mirror of anything. Single pass, so
`τ = −ln(1−f_abs)` with no reflected leg.

| θ₀ | f_abs | τ_WarpX | τ_PSC | ratio | predicted | dev |
|---:|---|---|---|---|---|---|
| 0° | 0.112835 | 0.119724 | 0.120273 | 1.004582 | 1.004555 | +0.003 % |
| 30° | 0.133620 | 0.143432 | 0.144089 | 1.004578 | 1.004549 | +0.003 % |
| 60° | 0.330625 | 0.401411 | 0.403195 | 1.004445 | 1.004408 | **+0.004 %** |

The prediction is **profile-weighted** — the pointwise ratio varies along the march, so for
an integral the prediction is the ratio of the two coefficient fields integrated over the
same profile, not the peak value.

**The refracting mode agrees too** (≤0.017 %, worst at 0°). That is the control that keeps
the claim honest: both modes are right on a stratified target, so this shows
`refraction = 0` **reproduces PSC's algorithm**, not that it is uniquely correct. Its
residual is the flatter of the two — at 0° +0.003 % against the refracting mode's +0.017 %,
because the straight position update is exact where RK4 has truncation error.

### 3. Coupled Test C in both modes — the ray model is not what separates the codes

| | f_abs (ray-march total) | PSC/WarpX |
|---|---|---|
| `refraction = 1` | 0.348389 | +1.75 % |
| `refraction = 0` | 0.348125 | +1.83 % |
| PSC's matched run | 0.354490 | — |

The flag moves WarpX by **−0.076 %** against a ~1.8 % PSC-to-WarpX gap, of which the
coefficient constants are +0.46 % and the rest is the two codes realizing slightly
different plasma (Test C's finding). At θ₀ = 0 the modes coincide by construction, so this
is a check that the flag changes nothing it should not.

**Convention caught while doing this:** these are ray-march totals (`Pabs/I0`), which is
what PSC's own diagnostic reports. `compare_testC.py` quotes a different quantity for WarpX
— the deposited field integrated over the grid, `∫P_abs dz/I0` = 0.348431. They agree to
1.2e-4, so it is a self-consistency check on the deposition rather than a disagreement, but
they are not interchangeable and should not be compared across.

### What this does and does not establish

**Does:** the straight-ray mode reproduces PSC's absorption operator, *including both
obliquity factors*, to 0.004 % of an independently predicted offset from 0° to 60°, with the
residual coefficient difference attributed down to PSC's rounded literals.

**Does not:** say anything about the near-critical layer, where PSC's own implementation
carries a unit bug; or about non-stratified targets, which PSC's model cannot represent at
all — there the two WarpX modes differ by 8.5 % on the total and far more on the pattern,
and PSC is not available as a referee.

`warpx-cda/laser_deposition/run_psc_oblique/` + `scripts/compare_psc_refraction.py`
(figure: `media/psc_refraction/psc_oblique_xcheck.png`). The PSC-linked reference drivers
stay outside both repositories, with the PSC tree.

