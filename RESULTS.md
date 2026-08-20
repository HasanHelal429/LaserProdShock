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

---

## 2026-07-31 (later) — `P1_vac_2d_spot_long` completes: the AXIAL resize worked, the transverse box was never fixed, and the run is planar for ~93 % of its length

432 000 steps in 44 602 s (12.39 h) on `build_cuda_omp`, clean finalize, no error signatures.
30 ps at an axial box of 2000 `d_e` against `P1_vac_2d_spot`'s 700. Suite run except `g3_spot`
and `spot_isolation` — see the last section for why those two cannot be run on it.

### The axial extension did what it was for

| t [ps] | ion front, 99.9th pct |
|---|---|
| 0.00 | 3.11 `C_s` |
| 8.97 | 18.00 |
| 19.42 | 36.77 |
| 29.88 | **47.46 `C_s` = 0.0475 c** |

**Monotonic** — against `P1_vac_2d_omp`'s 51.35 `C_s` at 19.42 ps falling to 37.04 at 29.88 ps on
a 700 `d_e` box. A falling percentile front means the fast tail was absorbed at the wall, so the
2000 `d_e` axial box is what a 30 ps vacuum run needs, and confirms the sizing rule from the
`P1_vac_1d_long` entry rather than the 10 ps extrapolation.

### The transverse box was NOT changed, and 30 ps makes that worse, not better

`geometry.transverse` is still ±80 `d_e` — the identical extent that lost contrast after 1.99 ps.
By the campaign's own rule `L_t/2 ≳ v_th,e·t_end + w0`, at v_th,e ≈ 38 `d_e`/ps a 30 ps run needs
**≈ 1160 `d_e`** against the 80 used: **14.5× too small**, where the 10 ps run was 5× too small.
**Tripling the duration on an unchanged transverse box triples the violation.**

`spot_report` shows it directly, and needs no control to do so:

| t [ps] | `w_eff/w0` | `leak>2.5w0` | `core<w0` | `f_ax` | `n_e,ax` [`n_cr`] |
|---|---|---|---|---|---|
| 0.00 | 1.000 | 0.0004 | 0.843 | 1.000 | 1.4931 |
| 8.97 | 2.315 | 0.145 | 0.476 | 0.261 | 1.4399 |
| 17.93 | 2.956 | 0.276 | 0.263 | 0.144 | 1.2170 |
| 26.90 | **3.147** | **0.344** | **0.258** | 0.177 | **0.9987** |

The second moment of the absorbed power reaches **3.15 `w0`** inside a box whose half-width is
4 `w0`, with **34 % of absorption beyond 2.5 `w0`**. The deposition profile has filled the box.
**Nothing past ~2 ps in this run is finite-spot physics**, which is ~93 % of its 30 ps.

Two things it does establish, both of which needed the duration:

- **On-axis `n_e` crosses `n_cr` at ~27 ps** (1.4931 → 0.9987), independently reproducing the
  28.8 ps crossing `P1_vac_1d_long` measured — the hydrodynamic end of the drive, not a
  temperature shutoff.
- Whole-beam `f_abs` *rises* late (0.49 at 3 ps → 0.67 at 26.9 ps) while `f_ax` *falls*
  (0.32 → 0.18). The beam is increasingly absorbed in the spreading plume rather than on axis,
  which is the same `f_ax ≠ f_abs` warning as before, now with the two moving in opposite
  directions. `E_abs` = 102 J per absent dim at 30 ps against 30.95 J at 9.96 ps.

The clamp regression test passes: wall/interior column ratio 0.02 at t = 0 → **0.62 at 26.90 ps**
(the bug drove it to 20–25); step-0 mean column ratio 1.00008, spread 3.267 %.

### G3 and `spot_isolation` CANNOT be run on this run as configured

Its declared `controls.laser_off` is `P1_vac_2d_spot_off` — **700 `d_e` axial and 144 000 steps,
against this run's 2000 and 432 000.** Grid heating accumulates with step count and depends on the
grid, so that subtraction is meaningless, by exactly the argument `P1_vac_2d_spot_off`'s own README
makes for why it could not be inherited from `P1_vac_2d_off`. Running it anyway would produce a
confident number with nothing behind it.

**`P1_vac_2d_spot_long` needs its own matched `_off` control** (2000 `d_e`, 432 000 steps, same
grid and ppc, `intensity = 0`) before any G3, G6 or `dark/lit` figure from it is quotable. Until
then the run supports the `n_cr`-crossing time and the axial-sizing result, and nothing that
requires separating laser heating from grid heating.

---

## 2026-07-31 (later) — Ray paths become visible, and the CUDA build turns out not to be run-to-run reproducible

Two deliverables, and the second one is the more important finding.

### `scripts/plot_rays.py` and `laser_deposition.ray_intervals`

Nothing in the campaign drew a ray. Every laser diagnostic reports where energy *landed* —
which is why both operator bugs found so far, the transverse index clamp and the exit-boundary
overshoot, had to be inferred from spatial deposition profiles. There are now two independent
views of the paths themselves:

- **`scripts/plot_rays.py`** re-integrates the eikonal equation offline on the `n_e` a plotfile
  dumped, using the operator's own RK4 marcher, multilinear sampling, `n_floor` threshold and
  wrap/clamp index mapping. Works retroactively on every 2D run on disk.
- **`laser_deposition.ray_intervals`** (warpx-cda `7429eb276`) dumps the operator's actual
  marched positions, with `ray_stride` / `ray_step_stride` to thin what would otherwise be
  ~6e5 rows per application. Off by default, free when off, one buffer per bucket written in
  bucket order.

**They agree to 0.0047 `d_e` median, 0.0137 `d_e` max** on deepest penetration at step 0 of
`P1_vac_2d_spot_omp` — a hundredth of a cell, a tenth of a march step. That is a real
cross-check: the reconstruction says what the equations imply, the dump says what the march
did, and they are the same thing. Compare with `plot_rays.py --dump`.

Read at `ray_step_stride = 20` the same comparison gives 0.86 `d_e`; the whole of that is the
dump's own sampling coarseness. **Quote a path comparison only at `ray_step_stride = 1`.**

Two things the figures show that were previously only numbers: the outbound legs **fan out at
wide angles** while the inbound bundle is dead vertical, which is the ray wander `spot_report`
reports as a scalar; and in `P1_vac_2d_spot_long` at 30 ps there are **79 turning points for 25
rays**, i.e. rays bouncing ~3 times each inside the enlarged corona, against a clean
single-turn fan at 10 ps.

A caveat the script enforces in its own docstring: it carries **no absorption**, because the IB
coefficient needs the per-cell `T_e` the operator builds from the momentum moments and that is
not in the plotfiles. The outbound leg is the path a ray *would* fly. At `tau` = 1411 through
the flat top essentially none does. **Never read an `f_abs` off it.**

### The CUDA build is not run-to-run reproducible, and a control caught it

Accepting the dump meant showing the operator was unchanged. On `build_cuda_omp` the
old-vs-new comparison **failed** — and then the control failed identically: the pre-change
binary does not reproduce **itself**.

| gaussian CI deck, max rel `ΔPabs` | |
|---|---|
| old vs old (first pair) | 1.9e-5 |
| dump OFF vs dump OFF, same binary | **5.3e-4** |
| dump ON vs dump ON, same binary | **1.2e-3** |
| any old vs new comparison | 5.3e-4 – 1.2e-3 |

The within-configuration spread is as large as any between-configuration difference, so the
measurement has **no power at all** on this platform — and the tempting first reading, that
1.9e-5 was the noise floor and 5.3e-4 was my change perturbing the march, was wrong. It was one
lucky draw. This holds on the static-plasma CI decks, which evolve no particles, so it is not
the `ParallelForRNG` thread-scheduling effect already on record: it is atomic ordering in the
GPU density deposit, amplified by `K ∝ n_e²/√(1−n_e/n_cr)` near critical.

On `build/` (OMP/CPU) the same three 2D CI decks are byte-identical run to run, byte-identical
to the pre-change binary with the dump both off and on, and the dump file itself is
byte-identical across `ray_threads` 1/2/4/8. That is the acceptance.

**Consequences beyond this diagnostic.** Any bit-level claim in this campaign must be taken
from the CPU build; whatever produced "Tier 1 285/285 byte-equal" was not the CUDA build. And
`P_abs` from a GPU run carries a ~1e-3 run-to-run irreducible spread on top of the 10.4 % seed
noise on `f_abs(0)` — small next to the seed noise, but it is not zero, and it is not
reducible by re-running.

### Housekeeping

The Phase 1.5 operator work was **uncommitted** in `warpx-cda` — 779 insertions across 10
files, including the 512-line `LaserDeposition.cpp` diff that `build_cuda_omp/bin/warpx.2d`
was built from, i.e. the binary behind every result in the two entries above. Now committed as
`d1f007e90` (O1–O4), `9f981dea2` (a ParticleHeater CUDA build fix) and `b4e0cf57a` (ACCURACY
finding 4 and the `run_laser_shock` retune), verified byte-identical to the source that
produced the binary.

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


---

## 2026-08-06 — `P1_vac_2d_spot_abl`: a laser spot bores a **resolvable crater**, 46 d_e = 2.3 `w₀`. Open transverse faces are what made it possible, and a stale binary nearly invalidated the whole thing

The first spot run built to make the *ablation* visible rather than to test the operator.
216 000 steps to 14.94 ps, 640 × 2600 cells, 35.2e6 macroparticles, **two MPI ranks on two
RTX 4070s**, 4 h 49 m at 0.0805 s/step, 12 GB of diagnostics, zero errors, `--verify` clean.
Requested changes from the parent `P1_vac_2d_spot_long`: 10× the intensity, half the target
thickness, no vacuum behind the target, and `refraction = 0`.

### The result: the crater is real and close to prediction

| | measured | pre-registered |
|---|---|---|
| crater depth at `t_end` | **46.1 d_e = 2.30 `w₀` = 92 cells** | 48–71 d_e (2.4–3.5 `w₀`) |
| deepening rate | **3.56 d_e/ps** | 3.2–4.7 d_e/ps ✓ |
| `T_e` axis / unlit reference | **1.73** | — (1.00 would mean planar) |
| `T_e` absorption-weighted, whole domain | **355.9 eV** | 0.75–1.1 keV ✗ **falsified** |
| areal density, axis vs reference | **0.832 vs 0.973** | — |
| `E_abs` | **162.1 J/m** | — |
| `f_abs` | 1.0000 → **0.2264** | ~1.000 at t=0 ✓ |
| `Tlocalfrac` | 0.431 → **0.980** | must RISE ✓ |

The critical surface goes from a flat 37.7 d_e everywhere to **4.2 d_e on axis against 50.3 d_e
at |x| ≈ 90**, i.e. a `w₀`-scaled depression 92 cells deep — visible without any processing in
`media/P1/P1_vac_2d_spot_abl/fields_map2d.png`, `rays.png` and `movie_map2d.mp4`.

**`T_e` is nearly insensitive to intensity — the one clearly falsified prediction.** Like-for-like
on the same estimator (whole-domain absorption-weighted): **236.0 eV at 1e18 → 355.9 eV at 1e19**,
×1.51 for ten times the intensity, i.e. `T_e ∝ I^0.18` against the `I^(1/2..2/3)` assumed. That is
the self-limiting absorption asserting itself — `K ∝ T_e^{−3/2}`, so a hotter corona absorbs less
and thermostats itself against intensity. Report the weighting: on axis it is **370.4 eV**
absorption-weighted against **183.8 eV** density-weighted, the usual factor ~2–3.

**The crater nonetheless landed in its predicted band because two errors cancelled.**
`v_crit ∝ I_abs/kT_e`, so over-predicting `T_e` and under-predicting its flatness offset each
other — a weaker `T_e` response makes each absorbed joule ablate more mass. The depth agreement is
therefore *not* evidence for the temperature scaling; one of its two inputs was wrong by 2–3×. A 1D
intensity ladder would settle the exponent cheaply, and is the obvious next run.

**Mass is genuinely removed on axis, but the spot also acts as a piston.** Areal density falls
16.8 % on axis against 2.7 % in the unlit reference band — a 14-point net ablation signature.
Yet peak on-axis `n_e` *rises* slightly, 1.500 → 1.579 `n_cr`, and the fraction of each axial
column's mass still behind z = 0 goes **up** on axis (0.790 → 0.881) while falling in the
reference (0.790 → 0.739). So at this intensity the drive both blows mass off forward *and*
pushes the remainder inward. Ions hold **33.3 %** of the coupled energy at 15 ps (the 100 ps
1D run reached 62–66 %, so this is the same transfer caught early).

### Open transverse faces did the job they were chosen for — but only just

The whole geometry rests on one argument: a periodic box cannot host a spot that ablates a
visible depth at *any* intensity, because `L_t/2 ≳ (v_th,e/v_crit)·D` and the measured ratio is
23, intensity-independent since both speeds go as `√T_e`. Measured contrast of the deposited
energy **increment** (baseline-subtracted; the raw `E(x)` is dominated by the slab's initial
thermal energy and starts at ~1, meaning nothing):

| | dark/lit |
|---|---|
| this run, 1.5 ps | 0.116 (isolated) |
| this run, 9.0 ps | 0.394 (marginal) |
| this run, 13.4 ps | **0.523** |
| `P1_vac_2d_spot_long`, periodic, by 10 ps | **0.946** |

So the run is isolated for ~5 ps, marginal to ~12 ps, and crosses the pre-registered
"effectively planar" threshold of 0.5 **only in the final dump** — where the periodic
predecessor was at 0.946 by 10 ps. The open boundary bought roughly the whole run. `T_e`
axis/reference of 1.73 says it is still a spot thermally at `t_end`. **A longer run at these
parameters would go planar**, and the next lever is a wider box or a larger `w₀`, not the
boundary condition.

### What `refraction = 0` did, quantitatively

Accepted as an explicit accuracy trade. At `t = 0` the target is plane-stratified, where a
straight march carrying the Snell invariant is *exact* — and the aborted run below left a
matched refracting reference, so that is now measured rather than asserted:

    step-0 P_abs   refraction = 1 : 5.94077e+13 W/m
                   refraction = 0 : 5.94083e+13 W/m     -> 3.4e-6, the log's print precision

Three consequences, all clean decompositions of earlier refracting findings:

- **Step-0 transverse profile spread 0.000 %** (min/max 1.0000/1.0000) against **3.267 %** with
  refraction. The earlier scatter was ray wander; straight rays have none by construction.
- **`w_eff/w₀` peaks at 1.23**, against 1.5–1.6 measured with refraction (RESULTS 2026-07-29).
  So of that ~1.5× broadening, the part that survives without refraction — the `T_e^{−3/2}`
  self-suppression of coupling on the hot axis — is ~1.23, and the rest was refractive.
- **The transverse leak is 0.0008 and the wall/interior ratio 0.00**, against 0.62 in the
  refracting periodic parent. **Do not read this as a clean run:** straight rays *cannot*
  scatter transversely, so this run has no power to test the leak question at all. It is a
  property of the mode, not evidence about the physics.
- `f_ax`/`f_abs` = 0.886, against 0.39/0.63 = 0.62 refracting — the whole-beam absorbed
  fraction overstates the axis by 13 % here rather than 60 %.

What is *not* available: the crater's own refractive feedback. Straight rays cannot be steered
into or out of a 92-cell-deep depression, so the late-time crater **profile** is indicative,
not quantitative. A matched `refraction = 1` companion on this geometry is the clean bound and
is still worth running.

### Two process failures, both of the same shape

**1. A stale binary silently ignored `refraction = 0` and the run had to be killed and
restarted.** `build_cuda_omp` was built 2026-07-31; `refraction` landed 2026-08-04. WarpX
parsed the key, never queried it, said nothing (`amrex.abort_on_unused_inputs` defaults to 0),
and marched with **full refraction** while the README claimed straight rays. Nothing in the
run's own output looked wrong — `f_abs`, `Tlocalfrac`, every gate and both GPUs were healthy.
The only tell is the key being absent from `warpx_used_inputs`, which is exactly what
`--verify` reports. Caught at step ~2000 of 216 000: **7 minutes lost instead of 4.6 h.**
`--verify` is answerable seconds after launch because `warpx_used_inputs` is written at
initialisation — so run it *then*, not at the end. In CLAUDE.md now. The seven minutes are
kept as `studies/refraction_xcheck/`, which is where the step-0 comparison above comes from.

**2. A column mis-read that changed which quantity was being plotted.** The rebuilt operator
writes an 8th profile column (per-cell `lnLambda`). `spot_report.py` and `spot_isolation.py`
inferred the layout from the column *count*, and 7 columns is ambiguous — 1D-with-`lnLambda`
as much as 2D-without. **Every 2D dump written before `lnLambda` existed was read as 1D**, so
`P_abs` came out of the `theta_e` column. Fixed by factoring the header-reading logic into
`io.profile_column_names` and having both fast readers use it; `tests/test_profile_columns.py`
pins all six layouts and greps that the duplicate implementation is gone, since a drifting
duplicate *was* the failure mode. 236 tests pass.

Both failures are one shape: **a change absorbed silently instead of reported.** WarpX
ignoring an unknown ParmParse key; numpy accepting a name list shorter than the file.

### And a mistake of mine worth recording, because it inverted the conclusion

First pass measured the crater as **3.0 d_e** and read the prediction as falsified by 20×. That
was a bad reference, not a result: I used `|x| > 120 d_e` as "unilluminated", but those columns
sit against the open transverse wall and rarefy laterally into it — they lose **30.9 %** of
their areal density, *more* than the illuminated axis loses. Against the `z_crit(x)` plateau at
75–115 d_e, where σ stays at 0.973, the crater is 46.1 d_e. **With an open boundary, "far from
the beam" is not the same as "undisturbed"** — pick the reference from the data, and check that
the reference itself has not moved.

### Gates and what may not be claimed

G1 pass (`ω_pe dt` 0.214 at 2×), G2 info (61 target, by construction), **G3 WARN — no laser-off
control, by decision**, G4 pass, G5 pass (`Tlocalfrac` 0.980), **G6 −30.0 % against 13.4 %
weight loss** (25.7 % of macroparticles — quote weight), G7 info.

G6 cannot close on this run and was not expected to: the rear is truncated flush with the
target and all four faces are open, so escaping particles carry energy WarpX does not report.
With no G3 control, **no few-percent energy statement from this run is quotable**, in particular
no grid-heating-corrected `E_abs`; the lateral loss is a total, not decomposable into
laser-driven and grid-driven. And no shock, piston speed or Mach number — there is no ambient.

### Figure bugs fixed while doing this

`plot_rays.py` reconstructed the refracting march regardless of the deck, drawing paths a
straight-ray run never took; it now reads `laser.refraction` and validates at **9.8e-09 d_e**
against the operator at `t` = 0. `plot_fields.py`'s 2D-map caption asserted "the drive is
periodic in x" over a run with **open** transverse faces — three lines below a comment warning
that a wrong caption here is "how a figure caption turns into a retraction".

---

## 2026-08-06 (later) — H1 started: the optical-depth **mechanism** is right, the **τ ~ 1 threshold** is wrong by an order of magnitude, and it cost no GPU time

H1 was the last of H1–H5 still open. Testing it turned out to need **no new runs for the first
leg**: the per-cell `laserdep_profile` dump carries the IB coefficient `A` alongside `n_e` and
`theta_e`, so the optical depth is integrable directly off runs already on disk —

    tau = ∫ (A/n_cr) n_e² / sqrt(1 − n_e/n_m) dz   from the injection face to the turning point

| run | `I₀` | τ(0) | τ later | `1−e^{−2τ}` | measured `f_abs` |
|---|---|---|---|---|---|
| `P1_vac_1d` | 1e18 | 6.69 | 0.198 @ 5 ps | 0.327 | ≈ 0.24 plateau |
| `P1_vac_1d_long` | 1e18 | 6.64 | 0.119 @ 10 ps | 0.212 | ≈ 0.24 plateau |
| `P1_vac_1d_thick` | 1e18 | 4.85 | 0.112 @ 15 ps | 0.200 | — |
| `P1_vac_2d_spot_long` | 1e18 | 6.49 | 0.485 @ 15 ps | 0.621 | 0.68 final |
| `P1_vac_2d_spot_abl` | 1e19 | 6.38 | **0.131** @ 13.4 ps | **0.2305** | **0.2264** |

**The picture behind H1 is correct.** `1 − e^{−2τ}` — a ray that turns and comes back out —
reproduces the measured plateau to **1.8 %** on `P1_vac_2d_spot_abl` and to within ±40 % across
the 1D corpus. And the corona genuinely thermostats: τ collapses from ~5–7 to ~0.1–0.2 within
1–3 ps and then holds roughly flat *while `T_e` keeps climbing*.

**H1's threshold is not.** It holds at **τ ≈ 0.1–0.2, not τ ~ 1.** At τ = 1 the absorbed
fraction would still be `1 − e^{−2}` = **0.86** — nearly full absorption, nothing a reasonable
person would call a shutoff. So the numerical criterion is out by ~10×, and the constant in
`T_e,shutoff` with it. The `(Z_eff lnΛ n_e² L)^{2/3}` **form survives**, because it follows from
`τ = const` and `K ∝ Z lnΛ n_e² T_e^{−3/2}` for *any* constant. But τ is not universal either —
0.13 → 0.93 across the corpus, with the 2D spot at 1e18 sitting ~4× above the 1D runs — so no
single-number `T_e,shutoff` can hold across dimensionality.

**So H1 is restated, not rescued.** There is no shutoff temperature, exactly as 2026-07-29
retired the half-peak `t_s` for the same reason. What exists is the **plateau coronal
temperature** `T_e,plat`, the temperature at which the corona holds τ ≈ 0.1–0.2, and
`H1' : T_e,plat ∝ (Z_eff lnΛ n_e² L)^{2/3}` — **exponent untested**. Full statement, and the two
1D ladders that would test it (~8 min per run), in `TEST_PLAN.md` §2.9. Leg B varies
`Z_eff·lnΛ`, the one knob carrying a standing 16×-vs-2.4× tension that **this project has never
actually varied** — it is still inherited from upstream, not reproduced.

Method note worth keeping: **quote `T_e` absorption-weighted and say so.** It runs 2–3× the
density-weighted value here (370 vs 184 eV on axis in `P1_vac_2d_spot_abl`), which is a factor
√3 in every sound speed built on it.

`TEST_PLAN.md` §11 was also reconciled against what is on disk — nine items marked done or
partial with evidence, two corrected rather than ticked (the planar-vs-1D comparison is open only
because `P1_vac_2d_off` predates the clamp fix; `t_s` is retired rather than measured).

---

## 2026-08-12 — Phase 4 designed: three-way cross-code benchmark against Lezhnin 2025

**No runs.** This entry records a phase design, two paper-reading findings that would each
have produced a confidently wrong figure, and the code that closes the tooling gaps.

**The phase.** Replicate Lezhnin et al., *Phys. Plasmas* **32**, 022701 (2025) — long-pulse
(1 ns, 10¹³ W/cm², 1.064 µm) laser ablation of solid aluminium — as a **three-way**
comparison where the paper ran a two-way one. FLASH (rad-hydro, collaborator-run) and full
PIC are the paper's two models; the **hybrid** leg is new, and it sits exactly between them.
Because it differs from the kinetic leg in *only* the electron closure (verified
mechanically: the two configs agree on all 15 shared physics keys), a disagreement it shows
against both bracketing models localises to the closure. Full spec in `TEST_PLAN.md` §12.

**Finding 1 — the sign in Eq. (15) is negative, and a text extraction drops it.** The
Manheimer steady-state ablation temperature carries **`Z^(−1/3)`**, not `Z^(+1/3)`. With
`µ` = 26.98, `Z` = 13, `λ₀` = 1.064 µm, `I` = 10¹³ W/cm²:

```
T_e,SS = 823 eV
```

which matches the ~800 eV plateau in the paper's Fig. 3(b) and the dashed line in Fig. 4(b).
The positive exponent gives 4.6 keV — off by 5.6×, and *plausible-looking*, which is the
dangerous kind of wrong. Confirmed by reading the rendered PDF page rather than the text
layer. This is now the phase's cheapest correctness check: any leg whose underdense `T_e`
plateau is not within a factor of order one of 823 eV has a setup error.

**Finding 2 — the paper carries two incompatible `d_i0`, and the gap is the mass-ratio
reduction.** In PSC's deck `m_p/m_e` = 100, so `d_i0` = 10 `d_e` and the box is "100 `d_i0`".
But Fig. 3's top axis runs to 0.65 mm at `z/d_i` ≈ 85, i.e. `d_i0` ≈ 7.6 µm — the **real**
proton skin depth at `n_cr` (7.256 µm), which is what lets the paper set its box beside
FLASH's 800 µm. **These are not compatible in physical units.** Our convention gives a
1000 `d_e` box = **169.3 µm**, not 726 µm.

Two rescalings follow, with *different powers*, which is the part most likely to be got
wrong:

| quantity | factor | why |
|---|---|---|
| length | `√(1836/100)` = **4.29** | `d_i0 ∝ √m_i` |
| time | `1836/100` = **18.36** | `t ∼ L/v ∝ √m·√m = m` |

So `P4_lez_kin`'s **54.66 ps is the paper's 1000 ps**. Rule adopted: compare in normalised
units, each code with its own `d_i0`; densities in `n_e/n_cr`; temperatures in absolute eV.
Never overlay two codes on a µm or ps axis in this phase.

**Code — the §12.3 gaps are closed.** `deck.py` emitted neither collisions nor a hybrid
block. Both now exist and are in `--verify`. Four things found in the doing, each of which
would have produced a *running* simulation of the wrong problem:

1. The operator's tokens are `species` | `electron_fluid`, **not** `particles` | `fluid`.
   The schema now uses the operator's own spelling rather than a synonym.
2. A hybrid deck must emit **no electron macroparticles at all** — the Ohm's-law solver
   forms `J_e` by subtraction, so a stray electron species is counted as an ion and
   subtracted twice. Nothing crashes.
3. `laser_deposition.species` must be **omitted, not emptied**, in the fluid path: WarpX
   aborts on a list nothing reads, because a stale list is how a deck comes to claim it
   heats something it does not.
4. A collisions pair naming a species the deck never creates aborts at WarpX **startup** —
   after the queue has handed over the GPU. Pairs are now validated at config time against
   the species that will actually be emitted.

**Gates.** A hybrid run has no electron macroparticles, so the `ω_pe` and Debye constraints
do not *exist* for it. G1/G2 now report `n/a` rather than `pass` — `pass` would read as
"checked and fine", a different claim. G3 likewise, since grid heating is a macroparticle
effect.

**`P4_lez_kin_off` added, reversing an earlier decision.** The kinetic leg was first written
with G3 declared unnecessary, on the argument that a cross-code comparison is a stronger
attribution test than a laser-off control. That is wrong: G2 reports `dz/λ_D` = **113** in
the cold dense target, so numerical grid heating is a live threat to `T_e` — the one
quantity the whole benchmark turns on — and it would have corrupted both the measurement
*and* our reading of any disagreement. At ~0.09 GPU-h it is the cheapest insurance in the
phase. Its off-switch is `intensity = 0`, not `intervals = 0`: `config.py` detects a control
by the former, so the latter left the pair looking un-controlled to the gates.

**Also corrected before launch:** the `ray_cfl` ladder initially pointed at
`studies/exit_overshoot`, which was measured on a 1.5 `n_cr` target with **no interior
critical surface**. Phase 4 runs a 10 `n_cr` target (the paper's `n_max,PIC`), so the ray
turns *inside* the plasma — precisely G4's non-monotonic regime. A fresh ladder at this
density is required, and the deposition profile is acceptance criterion A5, so this is not
bookkeeping.

**State.** Four run directories written with geometry diagrams; three WarpX decks generate
and round-trip through `--verify`; all gates clean; `tests/test_phase4_schema.py` adds 13
checks, 271 in the suite. **Nothing launched** — D1 (initial condition), D2 (whether to
implement `conducting`) and D8 (FLASH output format/location) are open and need steering.

---

## 2026-08-12 (later) — `P4_lez_hyb` blocked, then unblocked, by a WarpX bug: no density floor on the electron-energy advection velocity

**A code fix, found by trying to run.** The hybrid leg would not run at any time step. The
cause is a real bug in `HybridPICModel::AdvectElectronInternalEnergy`, not a setup error.

**The bug.** The advection velocity is `u_e = (J_i − J)/ρ`, guarded only against `ρ <= 0`.
The E-solve floors exactly the same quantity for exactly the same `1/n` divergence
(`HybridPICSolveE.cpp`: `std::max(rho_val, rho_floor)`); the advection did not. `n_floor`
is documented as the vacuum guard for the `1/n_e` terms in Ohm's law, and the electron flow
velocity is one of them.

**Why it bites *this* problem specifically.** An ablation corona expanding into vacuum thins
continuously, so `u_e` grows without bound and the donor-cell advection CFL assert aborts
the run — at any `dt`. Measured on `P4_lez_hyb`:

| | advection CFL |
|---|---|
| step 0, `dt` = 10 `d_e/c` | 13.4 |
| step 68, `dt` = 0.35 `d_e/c` | **3080** (`u_e` ~ 154 c) |
| step 68, same `dt`, **with the floor** | **1.95** — a factor **1580** lower |

Confirmed it is not a step-size problem: `n_floor` at 1e-3 and 1e-2 `n_cr` gave CFL
identical to six digits *before* the fix, because the parameter never reached this term.

**Fix**: `warpx-cda` commit `9e9c4a75b` on `feature/particle-heater`, one floored divisor
plus the localisation of `rho_floor` out of the member (a device lambda cannot capture
`this`, which is why `q_e` is already localised two lines above).

**Two run parameters are now MEASURED, not estimated**, and one of my earlier estimates was
wrong by 29×:

- `const_dt_de_over_c` = **0.35**, not 10. The binding constraint is not the ion CFL (which
  would allow 179 `d_e/c`) but the electron internal-energy advection CFL.
- `n_floor_over_ncr` = **1e-3**, not 1e-4. `u_e` in the floored region scales as
  `1/n_floor`, and 1e-4 still left CFL at 1.95 > 1. Only the near-vacuum is affected, where
  there is no real plasma to misrepresent.

Consequence: **276 480 steps, not 10 240** — 27× more. Measured rate 0.0071 s/step on 8
threads, so the run is **~32 minutes**, not the "under 5 minutes" I estimated. The estimate
was wrong on its `dt` input, not its particle count.

**A provenance trap, avoided.** The first production launch used a binary built from
`feature/particle-heater` + the fix. But `feature/hybrid-laser` carries a *later* refactor
of this same function — it moves the `T_e` seeding into `InitializeElectronTemperature` so
the field is seeded **before** the first field advance, where the old code left everything
that read `T_e` in the first step looking at a flat field. This run reads `T_e` through
`temperature_mode = hybrid_fluid`, so that is physics, not cosmetics. The run was stopped at
step ~7500/276480 and relaunched from the merged binary. The merge conflicted for this
reason, and was resolved by keeping `hybrid-laser`'s refactor and adding the floor to it.

**The first full attempt still failed, at step 54801 (19.8 %), CFL 1.005** — the floor
bounds `u_e` but does not stop it growing as the plume fills the box. The diagnosis that
matters is a physical one: a real quasineutral flow at `C_S` ~ 0.003 c gives an advection
CFL of ~**0.007** on this grid. A CFL of order 1 therefore is *not* plasma motion — it is
`(J_i − J)` noise divided by a tiny `ρ` in the near-vacuum, and the implied `u_e` ~ 1.4 c
says so outright. So the floor, not `dt`, is the lever that addresses the cause; cutting
`dt` alone treats the symptom at 5–10× the cost.

Second attempt: `n_floor` 1e-3 → **3e-3** `n_cr` *and* `dt` 0.35 → **0.175** `d_e/c`,
which together put the CFL near 0.17 where it previously hit 1.005. 552 960 steps.

**A caveat this creates, recorded before the run finishes so it cannot be quietly
forgotten:** 3e-3 `n_cr` sits *inside* the underdense range the paper compares — PSC
resolves to 1e-5 `n_cr`. The plume tail below 3e-3 `n_cr` is floored in Ohm's law and
**must not be quoted against FLASH**. The A1–A8 criteria at and above ~1e-2 `n_cr` are
unaffected. If the tenuous tail turns out to matter for the comparison, the honest fix is
in the code — exclude sub-floor cells from the CFL reduction, since they carry no plasma —
not a further raise of the floor.

---

## 2026-08-12 (later still) — `P4_lez_hyb` FAILS, and the failure is physical, not numerical

Five attempts, none completing. The last is the informative one.

| attempt | setting | abort step | physical time (`d_e/c`) | % of target |
|---|---|---|---|---|
| 1 | `dt` = 10 | 0 | — | — |
| 2 | `dt` = 0.35, floor 1e-3 | 54 801 | 19 180 | 19.9 % |
| 3 | `dt` = 0.175, floor 3e-3 | 142 240 | 24 892 | 25.8 % |
| 4 | zero-below 1e-4 | 75 | — | — |
| 5 | zero-below **1e-2** | 116 894 | **40 913** | **42.4 %** |

Target 96 560 `d_e/c`. Attempt 5 is the best by 1.64x and still aborts (CFL 1.196).

**The decisive observation is not the CFL.** Laser absorption held at 0.42-0.53 of peak for
most of the run and then collapsed to **0.001** — a 500x drop — immediately before the
abort. In the paper, absorption persists through the full 1 ns pulse. So the corona had
thinned below critical everywhere and the laser was passing straight through; the CFL
runaway is *downstream* of that, since an evaporated corona is precisely where
`(J_i − J)`/tiny `n_e` diverges. **Four attempts were spent treating a symptom.**

Two candidate causes, not yet separated:

1. Zeroing transport below 1e-2 `n_cr` starves the ablation front — the CFL "fix" may have
   broken the physics it was protecting.
2. The hybrid genuinely cannot hold this target: with **no** `∇·q_e` (the §12.4 limitation),
   nothing carries heat back into the dense material, so the corona blows off once and is
   gone.

**Verdict, and it is the one §12.6 predicted in advance**: the hybrid leg fails this
benchmark on electron heat transport. What was NOT predicted is that it fails *twice* — the
conduction term it lacks, and the advection term it has proving unintegrable against
vacuum. For the three-way comparison this is a positive result about the method: the model
sitting between FLASH and full PIC cannot model laser ablation as configured.

**Operator changes that stand regardless** (`warpx-cda`, `feature/particle-heater` →
merged to `feature/hybrid-laser`): `9e9c4a75b` floored the divisor; `f8eb07e40` supersedes
it by zeroing `u_e` below `n_floor`, which is both bounded by construction and the honest
statement (no plasma, no advective transport). Both are real fixes to a real gap — the
E-solve floors this quantity and the advection did not — and neither is sufficient here.

**Not done**: the regression test `warpx-cda/CLAUDE.md` requires for a bug fix.
`feature/particle-heater` is 10 commits ahead of origin, unpushed.

**Recommended next**: run `electron_energy_mode = source_only` — comparing it against this
`advected` failure isolates whether advection-without-conduction is worse than no transport
at all — and treat implementing `conducting` (decision D2b) as now *justified by measurement*
rather than by assertion. The kinetic and FLASH legs remain the benchmark's backbone.

---

## 2026-08-12 (final) — the `P4_lez_hyb` blocker is the electron-energy ADVECTION, isolated by controlled experiment

Three mechanisms proposed and **all three falsified by cheap tests**, which is the useful
part of this entry. The answer came from a discriminating experiment, not from reasoning
about a correlated observable.

**Root cause found and fixed first (`deck.py`).** Ions were emitted with the ELECTRON
number density while carrying charge `Z e`. At `Z` = 1 that is correct — which is why 20
runs across P0/P1 never showed it — but at Phase 4's `Z` = 13 the kinetic deck carried
`12 e n_t` of uncompensated charge and the hybrid deck ran at `n_e` = 130 `n_cr` against an
intended 10. Found by rendering a movie to check an absorption-collapse claim: `max(n_e)`
opened at 130. Fixed; 3 tests pin it, including that every `Z` = 1 deck stays byte-identical.

**With the density correct, the ablation is right.** Density opens at exactly 10.000 `n_cr`;
absorption holds at 0.54–0.72 of peak with no collapse; and **A8 passes** — fitting Eq. 16
per frame gives `C_S` climbing from 0.39 to 0.90 of the 823 eV steady-state value, i.e. the
plasma starts colder than `T_e,SS` and heats toward it, exactly as the paper describes.

**Three wrong mechanisms, each killed by a test:**

| claim | test | verdict |
|---|---|---|
| corona thinned below critical, laser passed through | movie: `max(n_e)` stays 9.6 `n_cr`, cells above `n_cr` *rise* 211 → 1327 | **false** |
| plume outruns the paper's expansion | A8 fit: `C_S` is 0.39–0.90 of SS, i.e. *slower* than predicted | **false** |
| the front hits the wall and the bounce destabilises | enlarge 950 → 2450 `d_e`: aborted EARLIER, 15.8 ps vs 21.9 ps, plume nowhere near the wall | **false** |

The box result is the informative one: **more vacuum, earlier failure**. That is the
signature of `(J_i − J)` noise divided by small `n_e`, not of any boundary.

**The discriminating experiment.** Same deck, same box, same `dt`, only
`electron_energy_mode` overridden:

| mode | outcome |
|---|---|
| `advected` | aborts at step 80 145 (29 %), CFL 1.218 |
| `source_only` | **276 480 / 276 480 COMPLETE**, no CFL abort, no SIGABRT, 1858 s |

The `source_only` leg ran to completion, so this is not a "got further" comparison — it is
one mode failing and the other finishing the identical problem.

**So the electron internal-energy advection is the blocker**, independent of boundary
condition and box size. `u_e = (J_i − J)/ρ` is unusable in a tenuous plume: with `B₀` = 0
and quasineutrality a real flow gives an advection CFL ~0.007, so anything near 1 is noise.

**Operator changes that stand** (`feature/particle-heater` → `feature/hybrid-laser`):
`9e9c4a75b` floored the divisor; `f8eb07e40` supersedes it by zeroing `u_e` below `n_floor`.
Both close a real gap — the E-solve floors this quantity and the advection did not — and
neither is sufficient, because the noise lives in cells *above* any physically acceptable
floor.

**Next**: filter or damp `J` in sub-floor cells so noise never enters `u_e`. Now
evidence-backed rather than speculative. Until then the hybrid leg can run `source_only`
(no transport) but not `advected`. The kinetic and FLASH legs are unaffected.

**Still not done**: the regression test `warpx-cda/CLAUDE.md` requires for a bug fix;
`feature/particle-heater` is 10 commits ahead of origin, unpushed.

---

## 2026-08-13 — Phase 4 controlled comparison: **A1 passes, A2 fails**, confirming the §12.6 prediction

Both legs at 2500 `d_e`, **reflecting rear / open front**, 10⁻³ `n_cr` background, differing
in **one** thing: the electron closure.

| t [ps] | `n_e` kin | `n_e` hyb | **ratio** | `T_e` kin | `T_e` hyb | **ratio** | `z_cr` kin | `z_cr` hyb |
|---|---|---|---|---|---|---|---|---|
| 10.9 | 5.66 | 5.42 | **0.96** | 581 | 417 | 0.72 | 138 | 152 |
| 21.9 | 2.84 | 2.89 | **1.02** | 1036 | 537 | **0.52** | 238 | 279 |
| 32.8 | 1.92 | 2.09 | 1.09 | 1305 | 682 | **0.52** | 318 | 394 |
| 43.7 | 1.42 | 1.55 | 1.09 | 1346 | 817 | 0.61 | 294 | 500 |
| 54.66 | 1.23 | 1.32 | 1.08 | 1323 | 948 | 0.72 | 258 | 596 |

- **A1 (density) PASSES** — agreement 0.96–1.09, comfortably inside the paper's 20 %.
- **A2 (temperature) FAILS** — the hybrid runs **28–48 % cooler**, worst at mid-run.
- The critical surfaces diverge *qualitatively*: kinetic peaks at 318 `d_e` and **recedes**
  to 258; hybrid marches **monotonically** to 596.

**This confirms §12.6's advance prediction** — hybrid passes the advection-dominated
criteria and fails on temperature — and the mechanism is the one in
`warpx-cda/hybrid_electrons/ELECTRON_CLOSURE.md` §5.2: with no `∇·q_e`, absorbed heat cannot
reach the overdense material, so the front compresses instead of ablating, and the critical
surface runs away outward instead of settling.

### RETRACTION of the 2026-08-13 (earlier) comparison

The previous entry reported the **opposite** — A1 failing at ratio 0.35–0.46, A2 passing —
and concluded the prediction had inverted. **That was a boundary artifact, not physics.**

With an *absorbing* rear only 4.5 `d_e` behind the target, the laser-driven compression
piled against the wall: the global `max(n_e)` sat at `z` = −48.2 `d_e` from ~7 ps onward
(3.05 `n_cr` against a plume peak of 1.14), nearly charge-neutral, i.e. compressed target
material. The reported "hybrid holds only 35 % of kinetic density" was a wall feature
measured against a plume. Excluding `z` < −40 already gave 0.98; with a reflecting rear the
global and interior peaks now coincide at every dump.

**Found by watching the comparison movie** — no gate, gate-check or test caught it.

### Also this session

- **`deck.py` charge-neutrality bug**: ions carried the ELECTRON number density while
  charged `Z e`. Invisible at `Z` = 1 (all 20 prior runs), catastrophic at `Z` = 13 —
  12 `e n_t` uncompensated charge kinetic, 130 `n_cr` instead of 10 hybrid. 3 tests pin it.
- **Intra-species collisions** must name the species twice; the docs say once and this
  version aborts. Every kinetic deck was unstartable. The old test asserted the *docs*, so it
  passed while the deck was broken.
- **Background species** (this session's fix for the hybrid `u_e` divergence) converged:
  10⁻³ and 10⁻⁴ `n_cr` give the same answer (peak `n_e` within 0.1–5 %, `T_e` within 3–7 %).
- **`Te`/`Pe` now dumped** for hybrid runs — previously absent, so the closure diagnosis had
  to scrape `laserdep_profile`.
- **GPU memory**: the kinetic+background run reached 11 826 / 12 282 MiB and AMReX's managed
  memory silently paged — 0.0032 s/step for 70 % of the run, then 10×, then **40×**, ending
  at 3h26m instead of 28 min. Physics unaffected (0 errors). Set
  `amrex.the_arena_is_managed=0` to fail loudly, and cut the background ppc.

---

## 2026-08-14 — **The hybrid solver creates energy.** Two deck bugs fixed; the Phase-4 comparison is not yet quotable

Answering "why does the hybrid depart from the kinetic run so much more than before?" — the
answer turned out to be a solver bug that two deck bugs had been hiding.

### The deck bug that was masking everything

`deck.py` emitted `targ_ions.ux_std = sqrt(theta)` using the **electron** mass
normalisation. WarpX's `u_std` is the spread in `u = γv/c`, so an ion needs
`sqrt(theta · m_e/m_i)`. Ion thermal ENERGY was therefore too large by `m_i/m_e` —
**2698× here, 100× in every `Z` = 1 run this project has ever done.** Measured: 40.57 keV
mean initial ion KE against the 15 eV the config asked for, ratio 2704.6 against
`mass_ratio` = 2698. Fixed; two tests pin it (one on the expression, one on the implied
energy in eV, since a string check passes on anything containing `mass_ratio`).

**Why the legs used to agree.** Both carried an ion thermal reservoir **15.7× the total
laser energy**, so both targets exploded under their own ion pressure at 0.00443 c — 1.22×
the kinetic sound speed and 2.21× the hybrid's. Same driver, same rate, both runs. The
laser was a **6.4 % perturbation**, and the closure barely entered. The "A1 passes at
0.96–1.09" result of 2026-08-13 is **RETRACTED**: it was agreement for the wrong reason.

### With cold ions, the real problem is visible

| | kinetic | hybrid |
|---|---|---|
| `E_abs` supplied | 4.21e6 | 1.99e6 |
| ion energy gain | 69.1 % of `E_abs` | **461.8 %** |
| total particles | **100.9 %** | 462.8 % |
| electron fluid ΔU | — | +1.86e6 |
| **accounted / supplied** | **1.009** | **5.56** |

**The full-PIC run conserves energy to 0.9 %. The hybrid creates ~9e6 J from nothing.**
That surplus, not the missing `∇·q_e`, is what drives the hybrid's extra expansion (peak
density 0.40× the kinetic, critical surface 3.4× further out, `T_e` plateauing at 424 eV
against 1387 eV).

### Which term, isolated (40 000 steps, fixed IC)

| variant | `dE_ions` | fluid `dU` | sum/`E_abs` |
|---|---|---|---|
| `advected` | 1.936e6 | **7.242e6** | **50.5** |
| `advected`, `eta` = 0 | 1.936e6 | 7.241e6 | **50.9** |
| `source_only` | 1.971e6 | 3.881e5 | **8.7** |

- **Not Ohmic heating** — `eta` = 0 is identical to four digits.
- **The advection is implicated** — `source_only` is 5.8× better, and the difference is
  entirely in `dU` (18.7×). The ion gain is the same in all three, i.e. insensitive to the
  electron closure.
- **97.8 % of the excess appears in 219 cells at `n_e` > `n_cr`**, where `P_abs` is exactly
  zero. That is the opposite end of the density range from the `u_e` divergence chased on
  2026-08-12/13, so they are separate problems.

**Hypothesis, untested**: the equation is integrated in non-conservative primitive form for
`T_e` while `n_e` comes from the PIC ions, so `(3/2) n_e k_B T_e` is conserved by neither
discrete continuity, with the error largest where the compression term is largest — the
compressing overdense region, which is where the binning puts it. Full treatment in
`warpx-cda/hybrid_electrons/ELECTRON_CLOSURE.md` §5.1b.

### Retractions

1. **"A1 passes"** (2026-08-13) — agreement produced by the shared ion-IC artifact.
2. **"The hybrid creates energy"** was retracted on 2026-08-13 and is now **reinstated**.
   The retraction was wrong: the ion-IC bug was a *separate* real bug, and removing it left
   the energy creation intact and cleanly demonstrated against a conserving control.
3. **"Not Ohmic, not the advection"** (2026-08-13) — those tests had **no power**. With the
   ion reservoir dominating `dE`, neither knob could have shown up. Redone here with the
   fixed IC, the advection *is* implicated. Same trap as the CUDA-reproducibility control in
   CLAUDE.md: a control that fails identically proves nothing.

### Standing consequence

**No hybrid-vs-kinetic number is quotable as a closure result until the energy budget
closes.** The conduction proposal (D2b) is premature for the same reason. The kinetic leg
looks sound — it conserves to 0.9 % — but note it reaches 1387 eV against the 823 eV
Manheimer steady state and is still rising, which points at something both legs share, most
likely the analytic initial ramp (decision D1) that the paper replaces with a FLASH snapshot.

---

## 2026-08-14 (later) — **RETRACTION: the hybrid does not create energy.** It conserves to 4 %

The entry above claimed the hybrid solver creates energy at 5.56x the laser input. **That is
wrong.** The error was the baseline, and it is the trap this project already had written down.

`electron_temp_init = polytropic` seeds `T_e = elec_temp (n/n0_ref)^(γ−1)` on the **first
field advance** — 464 eV in a 10 `n_cr` target against the 100 eV `elec_temp`. The step-0
diagnostic is written *before* that, recording a uniform 100 eV field the run never
integrates. Differencing against it books the initialisation as a gain: measured, the fluid
energy jumps 2.77e6 → 1.178e7 J in the first dump interval and is **flat** thereafter.

| baseline | fluid `dU` | ion `dE` | sum | `E_abs` | ratio |
|---|---|---|---|---|---|
| step-0 dump (wrong) | +1.86e6 | +9.21e6 | 1.11e7 | 1.99e6 | 5.57 |
| **first post-init dump** | **−6.99e6** | +9.02e6 | 2.04e6 | 1.95e6 | **1.04** |

**The hybrid conserves to 4 %**, against 0.9 % for full PIC. The sign is the tell: with the
correct baseline the fluid term is **negative** — the electron fluid does PdV work on the
ions, which is the ablation mechanism, not a leak.

### What survives

The primitive-form advection **is** non-conservative in principle. Summed against the
density, `T^{n+1} = T − dt(u·∇T + (2/3)T∇·u)` telescopes only for uniform `n`; a minimal
200-step test with a uniform velocity (`∇·u` = 0) and fixed non-uniform `n` drifts **+12.9 %**,
while the same test with uniform `n` is exact to machine precision. The defect is real — it
is simply not what dominates, since the production budget closes to 4 % with it in place.

A conservative flux-form rewrite (advect `w = ρT_e`, carry `ρ` through the same operator so a
uniform temperature is preserved) was implemented, tested, and **reverted**: it drives the
advection CFL past 1 at step ~2293 where the primitive scheme reaches 40 000, with `T_e`
healthy throughout, and over the window both survive the two give **identical** budgets.
Full account in `warpx-cda/hybrid_electrons/ELECTRON_CLOSURE.md` §5.1b.

### Consequence

The hybrid's departure from the kinetic leg — peak density 0.40x, critical surface 3.4x
further out, `T_e` plateauing at 424 eV against 1387 eV — is **closure physics, not a solver
bug**. The missing `∇·q_e` is back as the leading explanation, so decision **D2b**
(implementing `conducting`) is live again rather than premature.

### Standing corrections from this session

1. The `deck.py` ion thermal-momentum bug (ions `m_i/m_e` = 2698x too hot) is **real and
   fixed** — that finding is unaffected.
2. "The hybrid creates energy" is now **retracted for the third and final time**. The
   resolution is clean: with a correct baseline the budget closes, and the fluid does work
   rather than gaining it.
3. The `eta = 0` and `source_only` comparisons that appeared to implicate the advection were
   all differencing the same bad baseline, which is why they seemed to discriminate.

---

## 2026-08-18 — Phase 4 three-way comparison: FLASH vs kinetic vs hybrid, and a corrected temperature reference

`scripts/xcode_compare.py` (new), `media/xcode/{profiles,history}.png`. FLASH legs are the
delivered Ploegstra runs (see `runs/P4/P4_lez_flash/DELIVERY.md`); WarpX legs are
`P4_lez_kin_bg` and `P4_lez_hyb_bg3`.

### The unit map closes, and it was worth deriving rather than assuming
Only the ION mass differs between the codes (m_Al/m_e = 49542 real, 2698 in WarpX), so
WarpX keeps real `c`, `m_e`, `λ₀`, `n_cr` and `d_e`. The flow is nevertheless rescaled:
`C_S ∝ m_i^(-1/2)`, `d_i0 ∝ m_i^(1/2)`, `d_i0/C_S0 ∝ m_i`. Measuring `z` in each code's own
`d_i0` and `t` in its own `d_i0/C_S0` absorbs all of it. Derived independently, FLASH's time
unit is 37.098 ps and WarpX's 2.0277 ps (ratio 18.30 against the mass ratio 18.363, 0.4%),
and **both codes independently land at τ = 26.96** — they span the same normalised duration
to 0.3%. That is a genuine validation of the run design, not a coincidence.

### RETRACTION: the 823 eV reference was wrong for the WarpX legs
`T_e,SS = 5.94 μ^(1/3) Z^(-1/3) λ^(4/3) I^(2/3)` goes as **μ^(1/3)**, and the WarpX legs run
μ 18.363× lighter. Their correct steady-state target is **823 / 18.363^(1/3) = 312 eV**, not
823 eV. Density-weighted `T_e` over the underdense plume (1e-2 ≤ n_e/n_cr ≤ 1) at τ = 27,
each against its OWN Manheimer value:

| leg | T_e | own T_e,SS | ratio |
|---|---|---|---|
| FLASH | 839.0 eV | 823 eV | **1.019** |
| kinetic | 347.1 eV | 312 eV | **1.113** |
| hybrid | 423.4 eV | 312 eV | **1.357** |

All three sit near their own prediction, FLASH to 2%. **The "hybrid reaches only 0.31× the
kinetic's T_e" and "the kinetic overshoots to 1387 eV" claims are both retracted**: they
compared raw eV against the real-mass value, and used unweighted maxima over a band that
includes the tenuous background where the kinetic's hot tail runs to 5.3 keV. The 823 eV
annotation is now corrected in `compare_movie3.py` and `compare_deposition.py`.

### What actually differs: the SHAPE of T_e, not its magnitude
FLASH's `T_e` is a **flat plateau across the whole plume**, cut off sharply at the front —
the signature of strong flux-limited conduction. The hybrid's is a localised **hump** peaking
near ζ ≈ 30–50 and falling either side; the kinetic's **rises outward** with a hot tenuous
tail. So the missing `∇·q_e` is real and visible, but it shows up as the absence of the
conduction plateau, **not** as a wrong peak temperature. Anyone judging the closure on peak
`T_e` alone will conclude the opposite of the truth.

### Plume hydrodynamics: the hybrid tracks FLASH, the kinetic does not
At τ = 27, as a ratio to FLASH: plume front `ζ(1e-2 n_cr)` kinetic **0.71×**, hybrid
**0.98×**; `v_z/C_S0` at 0.1 n_cr kinetic **0.64×**, hybrid **0.96×**; density scale length
kinetic **0.68×**, hybrid **0.83×**. In `history.png` the FLASH and hybrid front and velocity
curves overlay for the whole run. **This inverts the phase's working assumption** that the
kinetic leg is the arbiter and the hybrid the deficient one.

### …but the hybrid's agreement must not be quoted yet — two disqualifiers
1. **It absorbs 2.1× less laser and is still hotter and faster.** Time-integrated `f_abs`:
   FLASH 0.870, kinetic 0.769, hybrid **0.364**, and the hybrid's instantaneous `f_abs`
   *collapses* 0.940 → 0.369 over the run while the kinetic holds 0.953 → 0.935. A leg that
   couples half the energy yet expands faster has an energy-partition problem; `T_e,SS ∝
   I_abs^(2/3)` puts the hybrid at 2.7× its absorbed-flux expectation against FLASH's 1.12×.
   (Absorption is *not* the explanation for the FLASH↔WarpX temperature gap: 0.884^(2/3) =
   0.92, an 8% effect, against the mass factor's 2.6×.)
2. **It is not robust to the background density**, which was justified as a numerical crutch
   costing "0.35% mass loading". bg3 (1e-3) vs bg4 (1e-4) at τ = 27: plume front 92.4 → 168.1
   (**1.8×**), `L_n` 17.8 → 40.4 (**2.3×**), peak n_e 1.93 → 0.95, and bg4 loses its critical
   surface entirely. bg3's near-exact match to FLASH therefore rests on a parameter chosen for
   stability, and reads as coincidence until a background-independent run says otherwise.

By contrast the **FLASH reference is robust**: radiation on vs off moves the plume front 1.8%,
plume `T_e` 2.5% and `L_n` 2.7%.

### Not comparable, by design
Peak density (FLASH 4141 n_cr and *compressing*; WarpX 5.7 and 1.9 and *decompressing* from
10) and critical-surface position (`ζ_cr` FLASH 4.16, kinetic 9.39, hybrid 31.96) are set by
`n_max` = 795 vs 10 n_cr — **decision D5**, already excluded by TEST_PLAN 12.6. The 3.4×
hybrid/kinetic `ζ_cr` ratio measured on 2026-08-13 reproduces exactly (31.96/9.39 = 3.40).

### Consequences
- **D2b (implementing `conducting`) stays live**, and now has a specific target: reproduce
  FLASH's flat plume `T_e` plateau, not a higher peak.
- **The kinetic leg is now the one to explain** — 30% short and 36% slow against FLASH on
  quantities that survive the rescaling. Leading suspect is the **never-executed D3 gate**
  (collision rates under a reduced mass ratio, TEST_PLAN 12.8 risk 1: PSC applies a special
  correction, WarpX's `BinaryCollision` is not known to).
- **The hybrid's absorption collapse (0.94 → 0.37) is a new, unexplained finding** and is the
  most concrete hybrid defect this comparison produced. Note it contradicts nothing earlier:
  the 2026-08-13 movie showed the density staying overdense, which does not prevent `f_abs`
  falling, since `K ∝ n_e² T_e^(-3/2)` and `T_e` rose.
- A background-independent hybrid run is the prerequisite for any "hybrid matches FLASH"
  claim.

### Tooling bug fixed along the way
`xcode_compare.py` first read the ion drift from `particle_momentum_x`. **In 1D WarpX the
geometry axis is z**; yt exposes the single spatial coordinate as `particle_position_x`, but
momentum keeps its three physical components, so the longitudinal one is `momentum_z`. Using
`_x` reports the transverse thermal spread (0.13 `C_S0`) in place of the outflow (up to 9.9),
and it looked plausible — the plume front moved while the "velocity" read zero, which is what
caught it. Also: target macroparticle weights span **seven decades** (1.7e10 … 1.3e17) because
the exponential initial ramp is loaded at fixed ppc, so every moment here is weight-weighted
and single-particle extrema are meaningless. Cross-checks: binned particle `n_e` reproduces the
field `n_e` to 0.14%, and the ambient floor recovers 9.80e-4 against the configured 1e-3.

### 2026-08-18, later — CORRECTION: the kinetic leg is not slow, and FLASH↔kinetic passes

The entry above says the kinetic leg is "30% short and 36% slow against FLASH" and needs
explaining. **That was a normalisation artifact and is retracted.** `v/C_S0` divides by the
sound speed at 823 eV, but the kinetic run's plume is at 347 eV. Dividing instead by the
sound speed at each code's *measured* `T_e`:

| τ | FLASH `v/(C_S0√(T_e/823))` | kinetic | ratio |
|---|---|---|---|
| 6.7 | 2.820 | 2.911 | 1.032 |
| 13.5 | 2.954 | 3.287 | 1.113 |
| 20.3 | 2.846 | 3.192 | 1.122 |
| 27.0 | **2.954** | **2.961** | **1.002** |

The rarefaction coefficient is the same number in both codes — 0.2% at τ = 27, within 12%
throughout. Renormalising lengths the same way, `L_n/(τ√(T_e/823))` agrees to **5%** (0.786
vs 0.827) and the plume front to **11%**, both converging with τ. So the plume is slow and
short *only because it is cool*, and it is cool because `T_e,SS ∝ μ^(1/3)` and μ is 18.363×
smaller. **The rarefaction physics is identical.**

Combined with absorbed fraction 0.870 vs 0.769 and plume `T_e` at 1.02× / 1.11× of each
code's own Manheimer value, **the FLASH↔kinetic benchmark passes.** That is the Phase-4
deliverable: the ray-traced deposition operator reproduces a real radiation-hydro ablation.

### The differences that remain, ranked
1. **`T_e` SHAPE — the only unexplained one.** FLASH is a flat plateau across the plume
   (diffusive flux-limited conduction); the kinetic rises outward with a hot tenuous tail
   (5.3 keV in the far field). Either genuine non-local kinetic transport — in which case it
   is a *result* — or wrong collision rates under the reduced mass ratio. **Decision D3 is
   the test that distinguishes these, and it has still never been run.**
2. **Mass reservoir, 337×** (D5). Areal electron density 3.86e25 m⁻² (FLASH) vs 1.14e23
   (kinetic). By τ = 27 FLASH has moved **0.275%** of its reservoir into the underdense plume
   and its overdense column has *grown* to 1.005 of initial (shock compression); the kinetic
   has moved **14.9%** and its overdense column has fallen to **0.845**. So FLASH is
   quasi-steady ablation against an effectively infinite reservoir and the kinetic is a
   slowly disassembling foil. It has **not** broken the agreement at τ = 27, but it bounds how
   far the comparison can be extended.
3. Overdense interior and critical-surface position — incomparable, `n_max` 10 vs 795 n_cr.

### On D1 (initialise from the FLASH snapshot)
Worth doing, but **not as a fix — there is no residual discrepancy left for it to fix**, and
it cannot import the one real structural difference (PIC cannot carry 795 n_cr, so capping
the snapshot returns approximately the analytic IC). What it *does* buy is early-time
agreement: the front-position ratio runs 1.69 at τ = 6.7 → 1.11 at τ = 27, and that early
excess is the signature of starting **from rest** when FLASH's 0.1 ns state already carries a
velocity ramp to 980 km/s (5 C_S0 at its tip). It also retires the free parameter
`scale_length_de = 27`. The analytic IC is now *shown* not to have biased the late-time
result, which is worth recording as a positive check on the choice.

Cost is not a constraint on any of this: the kinetic leg is **36 min on one GPU** (552 960
steps at 0.0040 s/step). G1 permits `n_max` up to ~50 n_cr at the present dt (ω_pe·dt = 1.24,
leaving room for 2.6× compression before the 2.0 limit) and raising `n_max` at fixed ppc costs
**no extra macroparticles**.

---

## 2026-08-18 — D3 collision gate: the e–i half PASSES, and the deficit is a cap, not a bug

`studies/collision_gate/` (new): Lezhnin 2025 Appendix B reproduced at **our** production
numerics — uniform periodic laser-off box, Z = 13, `m_i` = 2698 `m_e`, `dz` = 0.5 `d_e`,
`cfl` = 0.35, ppc 2000, `lnΛ` = 6.3 pinned in **both** the deck and the analytic reference.
15 runs: 5 (n, T) points × {collisions off, every step, every 10 = production}, plus one
confirmation run. Figure `studies/collision_gate/media/b1_decay.png`.

### The result
| `n_e/n_cr` | `T_i` | cap-touched % of `f(v)` | `ν_ei·dt_coll` | `c1` | `c10` |
|---|---|---|---|---|---|
| 0.1 | 120 | **1.5 %** | 0.002 | **1.005** | 0.875 |
| 1 | 120 | 4.6 % | 0.015 | 0.890 | 0.637 |
| 0.01 | 12 | 12.9 % | 0.005 | 0.552 | 0.538 |
| 0.1 | 12 | 32.5 % | 0.048 | 0.250 | 0.225 |
| 1 | 12 | 65.2 % | 0.483 | 0.082 | 0.030 |

WarpX reproduces Eq. (B1) to **0.5 %** where its cross-section cap is inactive. The `c1`
ratio is monotonic in the cap-touched fraction and **uncorrelated with `ν_ei·dt_coll`** —
the 0.01 `n_cr` / 12 eV point has `ν·dt_coll` = 0.005 and still reads 0.552. That
decorrelation is the proof of mechanism.

### Mechanism (read out of the WarpX source, not inferred)
`UpdateMomentumPerezElastic.H` applies `sigma_eff = min(pi*b0^2*lnLmd, sigma_max)` with
`sigma_max = 1/(n·r_min)` from `ElasticCollisionPerez.H` — a collision may not have a mean
free path shorter than the interparticle spacing (Perez 2012 §II.C; Angus et al. JCP 531,
113927). A pinned `CoulombLog` **is** honoured (line 181), but the cap applies afterwards
regardless, and since `σ_C ∝ v⁻⁴` it bites on the slow tail even where the thermal-speed
ratio looks safe.

**Where the cap binds, the plasma is strongly coupled and Spitzer at `lnΛ` = 6.3 is not a
physical target.** At `n_cr` / 13.2 eV the self-consistent `lnΛ` is 0.60, and 0.60/6.3 =
0.095 against the measured 0.082 — the paper's own "`lnΛ` < 1 regime" (their Fig. 11a). So
the apparent 12× discrepancy was **my reference being wrong, not the operator**.

Confirmed independently: `lnΛ` pinned at **20** where the cap is inactive gives **0.669**,
against the **0.20** that using WarpX's own `lnΛ` = 4.06 would give.

### Verdict for `P4_lez_kin_bg`
Evaluated cell by cell on the production run's own profiles, density-weighted over the
underdense plume, the cap touches at most **1.71 %** of `f(v)` and `ν_ei·dt_coll` never
exceeds **0.051** — and the ladder measures **1.005** at 1.5 % capped. **The kinetic leg's
collisional transport is sound.** The risk D3 was written to catch (WarpX lacking PSC's
reduced-mass-ratio correction, Ref. 47) is **not present**. Its `t` = 0 cold dense target
is 18 % capped, so only the startup transient is under-collisional.

This closes the last open doubt about the kinetic leg, and so completes the FLASH↔kinetic
benchmark recorded on 2026-08-18 earlier: absorbed fraction 0.870 vs 0.769, plume `T_e` at
1.02× / 1.11× of each code's own μ^(1/3)-corrected Manheimer value, and a rarefaction
coefficient agreeing to 0.2 %.

### One caveat and a cheap fix
`c10/c1` = 0.87 / 0.98 / 0.72 / 0.90 / 0.37 with increasing `ν·dt_coll`. Below ≈0.5 the
scatter matches the effect, so no trend is resolvable: honestly, the production cadence
costs **of order 10–15 %** in the `e–i` rate, rising to 63 % at `ν·dt_coll` = 4.8.
Collisions are **10.4 %** of a production step at `ndt` = 10, so `collisions.intervals: 1`
doubles the run to ~72 min and removes the uncertainty. **Recommended for future Phase-4
kinetic runs.**

Also found before any run: `P4_lez_kin_bg`'s `collisions.pairs` cover only the target
species — the ambient is collisionless and there are no target↔ambient pairs.

### D3 is NOT fully closed
Appendix C (electron thermal conductivity) is not covered; it needs an imposed gradient in
a non-periodic box. **The e–i thermalisation half passes; the conductivity half is
outstanding.**

### Process notes
* Three concurrent GPU runs died with AMReX `Arena out of memory` — it sizes the device
  Arena from free GPU memory (~8.9 GiB), so a second run on the same device has nothing
  left. And a 40-cell box is kernel-launch-latency bound anyway: **0.133 s/step on a 4070
  against 0.011 s/step on 8 OMP threads**, with collisions only 2.8 % of the step. The
  production run's 12.7× GPU advantage does **not** transfer to small boxes; cell count
  decides. `run_variants.sh` now defaults to CPU.
* `analyze.py` had a conditioning bug that produced a confident wrong answer: with
  `t ~ 1e-16` s the design matrix `[t, 1]` has condition number ~1e14, and `lstsq` silently
  zeroed the slope, reporting "no equilibration at all" for a run whose `T_i` had visibly
  moved. Time is now scaled to O(1) before the fit. The tell was the inconsistency between
  the fitted rate and the raw endpoint, not anything in the fit's own diagnostics.

---

## 2026-08-18 — D1 executed: the corona explained the no-background discrepancy, and the residual is unfixable at a reduced mass ratio

`runs/P4/P4_lez_kin_flashic` (new, 774 144 steps, 1 h 27 m, no NaN). No background species,
initial condition fitted to the delivered FLASH run at t = 0.1 ns. See its README for the
full parameter table; this entry records what it settles.

### The question
`P4_lez_kin` (no background) departs from FLASH badly: plume front **2.03×** too far,
outflow **1.37×** too fast, `L_n` **1.82×** too long, and the target disassembles from 10 to
1.74 `n_cr`. How much of that is the initial corona?

### The corona differences, measured against FLASH's 0.1 ns snapshot
| | `P4_lez_kin` | FLASH |
|---|---|---|
| corona form | **Gaussian** | **exponential** |
| `n_cr` surface | 40.6 `d_e` | **2.31 `d_e`** |
| corona `T_e` | 100 eV | **378 eV, isothermal** |
| initial flow | **at rest** | ramp to 4–5 `C_S0` |
| peak `n_e` | 10 `n_cr` | 795 `n_cr` |

The root cause is the **functional form**: fitted over 1e-3…1 `n_cr`, an exponential gives
rms(ln n) = 0.107 against the Gaussian's 0.361 — and a Gaussian cannot be tuned into the
right shape, because its local scale length `L²/(2z)` varies through the corona, so matching
`L_n` at 0.1 `n_cr` forces the critical surface to 24–42 `d_e`. `deck.py` had only ever
written a Gaussian.

### Answer: yes, and the evidence is the energy budget
| | absorbed per TARGET electron | optical depth vs FLASH (τ = 27) |
|---|---|---|
| FLASH | 13.4 eV | 1.00 |
| `P4_lez_kin` | **243 eV — 18× too much** | **5.68×** |
| `P4_lez_kin_flashic` | **9.2 eV — 0.69×** | 0.53× |

The old run over-coupled by 18×: its corona was 3.8× too cold and `K ∝ T^(-3/2)`, so it
absorbed 7.3× too strongly, into a reservoir 11.7× too small. That is the whole explanation
for a plume 2× too far and 1.4× too fast. With the corona fixed the target **survives**
(peak 40 → 37.8, 5.4 % consumed) and the budget lands within 1.5× of FLASH.

### The new leg is self-consistent; the old one was not
`T_e,SS ∝ I_abs^(2/3)`, against each leg's own reduced-mass Manheimer value (312 eV):
FLASH **1.019**, `P4_lez_kin` **1.587**, `P4_lez_kin_flashic` **0.974**. The old leg sat
60 % above what its own absorption could support — volumetric cooking of a foil, not
ablation. The new one sits where its absorption puts it, and is simply under-driven.

### The residual is absorption, and it CANNOT be fixed at a reduced mass ratio
The whole remaining gap is `f_abs` = 0.358 against FLASH's 0.870. Absorption integrates `κ`
over **metres**; hydrodynamics scales with `d_i0`; and `d_i0` is **4.29× smaller** in WarpX.
A corona matched in normalised units is therefore 4.29× shorter in absolute length and
cannot carry FLASH's optical depth, while a corona matched in absolute length would be the
wrong hydrodynamic profile. **At a reduced mass ratio one can match the ablation dynamics or
the absorption, not both.** This is a limitation of the paper's approach, not of this deck,
and is likely why PSC also reduced `c` — which moves `n_cr` and rescales absorption with it.
WarpX has real `c` and cannot follow.

**Consequence for Phase 4:** the FLASH↔kinetic comparison should be read on the quantities
that survive the rescaling (which pass, see the earlier 2026-08-18 entry) and on the
*self-consistency* of each leg against its own absorbed flux — not on absolute agreement in
plume energetics, which is out of reach by construction.

### Tooling
* `deck.py` gains `corona_profile: exponential`, `corona_density_over_ncr`,
  `corona_offset_de`, `theta_e_solid`/`theta_i_solid` (via WarpX's
  `maxwellian_u_std_distribution_type = parser`) and `drift_uz_de` (via
  `maxwellian_u_mean_distribution_type = parser`). All default to the previous behaviour.
* **BUG FIX.** `density_min` was applied identically to both species although the ion
  density function is `(n_e expression)/Z`, so ions were culled a factor **Z = 13** in
  density earlier than electrons — leaving an 18 `d_e` shell at the plume tip with net
  charge **−1.000** of the local density. 7.5e-5 of the total charge, which is why no energy
  budget ever caught it; locally complete. **Every Z ≠ 1 run this project has produced
  carries it.** Found by the smoke test, fixed, regression test added.
* **`Tlocalfrac` is unreliable when the target is much denser than the corona.** It is
  `n_e²`-weighted over all cells, so a 40 `n_cr` slab outweighs the corona ~45 000:1 and the
  number describes the slab, which absorbs nothing. It read 1.2e-7 here while every
  absorbing cell demonstrably used its own temperature (`A × T_e^{1.5}` constant to four
  decimals over 447 cells).
* `strings <binary> | grep -x <key>` — CLAUDE.md's provenance test — **gives false
  negatives**: the compiler merges string literals, so `uz_mean_function(x,y,z)` appears
  only inside `ux_mean_functionuy_mean_functionuz_mean_function`. Use a substring search, or
  better, check WarpX's own `Unused ParmParse` list after a smoke run.

---

## 2026-08-18 (final) — The ablation profiles agree better than the figure says: the raw-eV axes carried most of the "mismatch", and D1's "absorption is unfixable" is too strong

**Environment.** No new WarpX runs. Analysis only, on the existing legs
(`P4_lez_kin_bg`, `P4_lez_kin_flashic`, `P4_lez_hyb_bg3`, FLASH `Ablation_prod_08-17`),
with `/opt/anaconda3/envs/physics/bin/python`. `scripts/xcode_compare.py` gains
`figure_reduced()` → `media/xcode/profiles_reduced.png`; `TEST_PLAN.md` §12.2 and criteria
A2/A3/A4/A6 corrected. 321 tests pass.

### The question
"The ablation profiles are not matching." Asked of `media/xcode/profiles.png`, that is
true as drawn — FLASH's `T_e` sits at ~950 eV and the WarpX legs at ~350, and FLASH's
`v_z/C_S0` runs 1.4× above them. But `profiles.png` plots `T_e` in **raw eV on a shared
axis** and `v` against `C_S0` evaluated at **823 eV for both codes**, and the 2026-08-18
retraction earlier in this file already established that neither is the comparable
quantity. The figure had not been rebuilt to match the retraction.

### How much of the "mismatch" is the axes
Median |relative difference| against FLASH, over the underdense band
`1e-2 ≤ n_e/n_cr ≤ 1`, interpolated onto FLASH's `ζ` grid. RAW is `profiles.png` as it
stood; RED divides `T_e` by each leg's **own** `T_e,SS(µ)` and `v` by the sound speed at
each leg's **own measured** plume `T_e`.

| τ | leg | A2 `T_e` RAW | A2 RED | A4 `v_z` RAW | A4 RED |
|---|---|---|---|---|---|
| 6.7 | kinetic, analytic IC | 59.1 % | **18.6 %** | 56.9 % | 35.3 % |
| 13.5 | kinetic, analytic IC | 61.7 % | **25.8 %** | 39.2 % | **9.8 %** |
| 20.3 | kinetic, analytic IC | 63.4 % | **26.6 %** | 34.7 % | 18.5 % |
| 27.0 | kinetic, analytic IC | 62.9 % | **30.2 %** | 31.8 % | 15.2 % |
| 13.5 | hybrid | 68.8 % | **29.2 %** | 38.6 % | **15.6 %** |
| 20.3 | hybrid | 75.8 % | **39.7 %** | 38.7 % | 16.4 % |
| 27.0 | hybrid | 78.1 % | **42.3 %** | 22.8 % | 18.1 % |

**The normalisation is worth a factor 2–2.5× on both `T_e` and `v_z`**, and A4 reaches
9.8 % — inside its 10 % tolerance — for the kinetic leg at τ = 13.5. Nothing was re-run;
this is the same data on the axes §12.2 should always have specified.

### A1 was being measured with the wrong metric
Point-wise `|Δn_e|/n_e` over the band reads 59–70 % for the kinetic leg at late τ and
looks like a failure. It is not a meaningful number on a profile that falls **four
decades** across the plume: at FLASH's `L_n` = 21.4, a `ζ` shift of 0.5 reads as 60 %.
In log space the same comparison is **0.33 dex (kinetic) and 0.21 dex (hybrid) at
τ = 27** — a factor ~2 in density at fixed `ζ`, equivalently a plume-front shift of 16.3
and 10.3 `ζ` out of ~95. **Quote A1 in dex or as an equivalent `ζ` shift, never as a
point-wise percentage.**

### RETRACTION: "at a reduced mass ratio one can match the ablation dynamics or the absorption, not both"
That claim (2026-08-18, the D1 entry) is **too strong, and the counter-evidence was
already in this file**. Its argument holds `T_e` fixed while shrinking the corona:
`d_i0` is 4.29× smaller, so a normalised-matched corona is 4.29× shorter and was said to
be unable to carry FLASH's optical depth. But `κ_ib` is not invariant under the map —
it *rises* by the compensating factor:

```
κ_ib ∝ n_e² T_e^(−3/2)  at matched n_e/n_cr (λ₀ and n_cr are real in both codes)
T_e,SS ∝ µ^(1/3)   ⇒   κ ∝ µ^(−1/2)
L      ∝ d_i0 ∝ µ^(1/2)
τ_abs  = ∫κ dz ∝ µ^0     ← INVARIANT
```

The similarity transfer is **optical-depth preserving**, and that is why the paper's
approach works at all. Checked against our own numbers: from the measured plume
temperatures (FLASH 839 eV, kinetic 347 eV) the predicted absorbed-fraction ratio is
**0.877**, and the measured `f_abs` ratio for `P4_lez_kin_bg` is **0.769/0.870 = 0.884**.
Agreement to **0.8 %**.

### So `P4_lez_kin_flashic`'s absorption deficit is a deck bug, not a limit
Its IC transferred **three of four quantities in similarity units and one in absolute
units**:

| IC element | transferred as | consistent? |
|---|---|---|
| corona shape, `L_n` = 6.955 `d_e` | FLASH `ζ` × 10 — normalised | yes |
| corona anchor `n_cr`, offset 2.31 `d_e` | `n_e/n_cr` | yes |
| drift `v/C_S0` = 0.548 + 0.05598 `ζ` | normalised to WarpX's `C_S0` | yes |
| **corona `T_e` = 378.3 eV, `T_i` = 115.6 eV** | **absolute eV, straight from FLASH** | **no** |

At the reduced mass ratio the corresponding corona is `378.3 × 18.363^(−1/3)` =
**143.4 eV**. Setting it 2.638× too hot suppresses `κ_ib` by `2.638^1.5` = **4.29×** —
which is the whole of its `f_abs` = 0.358 against the analytic leg's 0.769, and the whole
reason it ends up at 0.54× its own Manheimer value while every other leg sits near 1.0.
The stale §12.2 rule ("temperatures in absolute eV") is what licensed it.

**Concrete fix, one config edit and a 1 h 27 m GPU re-run:**

```yaml
theta_e_init: 2.8061e-4   # 143.4 eV  (was 7.4032e-4 = 378.3 eV)
theta_i_init: 8.5747e-5   #  43.8 eV  (was 2.2622e-4 = 115.6 eV)
```

**Prediction, stated in advance so it can be falsified:** the re-run lands at
`f_abs` ≈ 0.7–0.8 and `T_e`/own-SS ≈ 1, i.e. it reproduces the analytic leg's energetics
*while* keeping the correct exponential corona and critical-surface position — which is
what would let it beat the analytic leg on `ζ_front` and `L_n`. If instead it over-absorbs
to `f_abs` → 1 and stays there, the self-limiting `κ ∝ T^(−3/2)` picture is wrong at this
corona and that is the more interesting result.

### What is left after all of the above — the genuinely open item
**The `T_e` SHAPE, and only that.** In reduced variables at τ = 27 FLASH is a flat
plateau at 1.0–1.15 × its own `T_e,SS` across the whole plume; the kinetic leg sits *on*
that plateau out to ζ ≈ 40 and then **rises** past 2.5; the hybrid is a hump peaking at
1.45 near ζ ≈ 30–50 and falling either side. The magnitudes now agree where the plume
carries mass — it is the outer, tenuous region that differs, which is exactly where a
kinetic tail and a diffusive plateau should part company.

This is unchanged from the earlier entry's ranking, but it is now the *only* item on the
list rather than one of four, and it has a decisive test that has still never been run:
**D3 Appendix C, the electron thermal conductivity gate.** The e–i half passed today; the
conductivity half distinguishes "genuine non-local kinetic transport, and therefore a
result" from "wrong conductivity, and therefore a bug". Until it runs, the `T_e` shape
cannot be quoted as either.

### The one lever that removes the whole class of problem
Every correction in this entry is a power of `µ`. Raising `m_i/m_e` from 2698 toward real
aluminium's 49542 drives `µ^(1/3)` → 1 and makes the reduced and raw axes coincide.
Cost scales as `µ` (steps to a fixed τ): the current kinetic leg is 1 h 27 m on one GPU,
so real mass is ~27 h, and an intermediate `µ` = 10792 (4×) is ~5.8 h. **A two- or
three-point sweep in `µ` is the cleanest possible demonstration of convergence** — if the
reduced-variable residuals shrink as `µ` rises, convergence is shown; if they plateau,
what remains is the kinetic physics and is a result. Nothing else in Phase 4 settles that
question as directly.

### Consequences
- `TEST_PLAN.md` §12.2 rewritten with the correction inline, and **A2/A3 now read
  `T_e/T_e,SS(own µ)`, A4 reads `V_z/C_S(own measured T_e)`, A6 names 312 eV for the
  reduced-mass legs.** The old text is quoted in the correction block rather than deleted.
- `media/xcode/profiles_reduced.png` is the panel the acceptance criteria are read on.
  `profiles.png` is kept — it is the raw-eV view, and it is the one that misleads.
- Ranked, what to do next: (1) the `flashic` corona-temperature re-run, ~1.5 h, settles
  the last energetics discrepancy; (2) D3 Appendix C, settles the `T_e` shape; (3) the
  `µ` sweep, settles convergence as such; (4) re-run `P4_lez_kin_bg` at
  `collisions.intervals: 1` (~72 min) to retire the 10–15 % cadence uncertainty on the
  leg the benchmark is quoted from.

### What I first believed and why it was wrong
That the mismatch needed a new run. It did not — three of the four contributions were in
the analysis, and the fourth (`flashic`'s absorption) is a two-line config edit rather
than the structural limit the D1 entry recorded. **The 2026-08-18 retraction of the
823 eV reference was applied to `xcode_compare.py`'s printed table and to two annotation
lines, but never to the figure's axes or to `TEST_PLAN.md`'s acceptance criteria** — so
the project has been reading its own benchmark against a reference it had already
retired. When a retraction lands, grep for every place the retracted number is used.

---

## 2026-08-18 (final, later) — `P4_lez_kin_flashic_ct`: the corona correction works on temperature and scale length, only partly on absorption — and the ion mass ratio changed with it

**Environment.** `build_cuda1d/bin/warpx.1d` (binary dated 2026-08-13 12:21, unchanged
since the parent ran, so provenance is identical), one RTX 4070 (**GPU 1**), `--gpu 1 -L`,
149 184 steps in **15 min** at 0.0061 s/step. `--verify` OK. 328 tests pass.

### What was run, and the honest caveat about it
`runs/P4/P4_lez_kin_flashic_ct` tests the previous entry's claim that
`P4_lez_kin_flashic`'s `f_abs` = 0.358 was a **mixed-unit initial condition** — corona
temperature imported from FLASH in absolute eV while every other IC element was
transferred in similarity units.

**It is not a single-variable test, and must not be quoted as one.** Two things changed:

| | parent | this run |
|---|---|---|
| corona `T_e` / `T_i` | 378.3 / 115.6 eV (absolute, from FLASH) | **47.81 / 14.61 eV** (µ-consistent) |
| `mass_ratio` (m_Al/mₑ) | 2698 | **100** |

The mass ratio changed on the user's instruction. The paper (§II.B) says *"we use a mass
ratio of `m_p/m_e` = 100"* — the **proton**, which for aluminium gives 26.98 × 100 = 2698,
and that is what every earlier Phase-4 leg ran. But the paper reaches its reduction with a
**reduced speed of light** (`m_e c²` = 60 keV against 511), which WarpX cannot follow with
real `c` and real `mₑ`. Running the ion itself at 100 mₑ is this project's choice. µ vs
real aluminium is therefore **495.4**, and this leg's own `T_e,SS` is **104 eV**.

### Result at τ = 27, the like-for-like window against FLASH

| | parent (2698, hot corona) | **this run (100, µ-consistent)** | FLASH |
|---|---|---|---|
| `f_abs` (time-integrated to τ = 27) | 0.358 | **0.551** | 0.870 |
| plume `T_e` | 168.1 eV | **≈123 eV** | 839.0 eV |
| `T_e` / **own** `T_e,SS` | **0.539** | **1.18** | 1.019 |
| `L_n` | 8.77 (0.41× FLASH) | **≈24 (1.13× FLASH)** | 21.4 |
| `ζ_front` | 46.8 (0.50×) | **47 (0.50×)** | 94.6 |
| peak `n_e` | 37.8, falling from 40 | **46.3, RISING from 40** | 4141 |

**The prediction is partly confirmed and the falsification criterion is not met.** The
README predicted `f_abs` → 0.7–0.8 and `T_e`/own-SS → ≈1, and said the claim would be
falsified by `f_abs` staying near 0.36. It did not stay: it moved to 0.551.

- **`T_e` self-consistency is fixed.** 0.539 → **1.18** of its own Manheimer value. This
  was the parent's most conspicuous defect — the only Phase-4 leg not sitting near 1.0 —
  and it is gone.
- **The density scale length is fixed.** 0.41× → **1.13×** of FLASH. The parent's corona
  was right in *shape* but wrong in *temperature*, and `L_n` is what that costs.
- **The target now compresses rather than ablates away**: peak `n_e` rises 40 → 46.3,
  where the parent fell 40 → 37.8 and `P4_lez_kin` collapsed 10 → 1.74. That is the
  qualitative behaviour FLASH shows (its overdense column *grows*).
- **Absorption is only 63 % recovered.** 0.551 against FLASH's 0.870, where 0.7–0.8 was
  predicted. `T_e,SS ∝ I_abs^(2/3)` puts the absorption-supported temperature at 76 eV
  against the measured ≈123, so this leg now sits **1.6× above what its own absorbed flux
  supports** — the opposite sign of the parent's problem, and unexplained.
- **The plume front is unchanged at 0.50× FLASH.** Neither correction touched it.

### A late-time feature worth recording
Because of the `max_step` error below, the run continued to τ = 140. Over that extension
`f_abs` **recovers**: 0.350 at τ = 27 → **0.781** at τ = 140, while peak `n_e` stays near
45–50 and `T_e` climbs to 182 eV (1.76× own SS). So the absorption deficit at τ = 27 is a
*transient*, not a floor. Nothing in Phase 4 has looked at this window before.

### MY ERROR: `max_step` was set by mixing the two `d_i0` conventions
I sized the run for τ = 27 using the **ion** inertial length for WarpX (10 `d_e` at
`m_i` = 100) while the FLASH τ it was matched to uses the **proton** one. Under the
consistent proton convention (`d_i0` = `d_e`√(m_i/A_Al·mₑ) = 1.925 `d_e`) the τ unit is
0.0751 ps, so 10.53 ps is **τ = 140**, not 27, and τ = 27 falls at step 28 695. This is
exactly the trap `TEST_PLAN.md` §12.2 documents, committed by the person who had just
finished writing about it. The run is not wasted — τ = 27 is inside it and is what the
table above reports — but a run sized this way at 2698 would have cost 5.2× more wall
clock than intended rather than 5.2× less.

### Tooling
* **`xcode_compare.warpx_scales(mass_ratio)`** — `d_i0`, `C_S0`, τ and `T_e,SS` are no
  longer module constants. `load_leg` reads `reference.mass_ratio` from each run's own
  config, so a leg at `m_i` = 100 is normalised on its own scales; previously the
  hardcoded `TAU_W` labelled this completed τ = 140 run as τ = 5.2. Regression: at 2698 it
  reproduces the old `DI0_W`/`TAU_W` to 3e-5 (the config rounds 26.9815 × 100 to 2698).
  **`d_i0` is the PROTON skin depth**, the paper's convention and the one every recorded
  number uses — defining it from the ion instead would restate all of RESULTS.md by 5.19×.
* **`deck.py` gains `numerics.arena_init_size_mb`.** AMReX pre-allocates **3/4 of the
  card's TOTAL memory** in one `cudaMalloc` — 8904 MiB of an RTX 4070's 11873 — **not 3/4
  of free memory** as the earlier entry today recorded. So on a shared GPU it aborts at
  init whenever another user holds enough of the card, regardless of how small the run is.
  It killed the first launch (8509 MiB free, 8904 requested) while another user held
  3.2 GB. This deck's real footprint is a few hundred MB; capped at 2 GiB.
* **`config.py`'s geometry diagram hardcoded "Gaussian"** for the coronal ramp, so it has
  mislabelled every exponential-corona run since `corona_profile` was added — including the
  parent's README, whose deck is exponential. It now reads `corona_profile`.

### Not done, deliberately
The **G3 laser-off control was not run** (user's decision). The asymmetry that makes this
defensible: grid heating warms the corona and `κ_ib ∝ T^(−3/2)`, so it can only push
`f_abs` **down** — a high `f_abs` is self-validating, and only a low one is ambiguous.
`f_abs` = 0.551 is mid-range, so **the control is still the right next step if the 63 %
recovery is to be quoted**, and `dz/λ_D` = **327** here against the parent's 116 makes
that more pressing, not less. Partly offset by 5.2× fewer steps at τ = 27.

### Open
1. Why does this leg sit **1.6× above** its own absorbed-flux expectation?
2. Is the **0.50× plume front** a real deficit or another normalisation artifact? It is
   the one quantity untouched by two successive IC corrections.
3. **The comparison figures have not been rebuilt** with this leg — the other three legs
   are at `m_i` = 2698 and this one is at 100, so `TEST_PLAN.md` §12.6 acceptance across
   all four is not meaningful until it is decided whether the older legs are re-run at 100.

---

## 2026-08-18 (final, later still) — D-1 and D-2: the far-field shelf is NOT an ambipolar precursor, and non-isothermality explains most of the shape

`studies/plume_structure/` (new): `d1_trough.py`, `d2_shape.py`. Analysis only, no runs.

### D-1 — the trough/shelf is quasineutral everywhere. The precursor hypothesis is FALSIFIED
The proposal was that the density minimum beyond the plume front, with material again
beyond it, might be a **hot-electron-driven fast ion precursor** — real kinetic physics a
3T fluid cannot produce, and therefore a *result* rather than a defect. The discriminator
is not density (both stories give the same `n_e`) but **macroparticle count** and whether
the charge separation is **coherent**. A real ambipolar front is charge-separated at its
leading edge with one sign over many bins; noise flips sign bin to bin.

At τ = 27, over ζ = 40–110, resolved bins only:

| leg | macroparticles/bin at ζ = 40…100 | `n_e/(Z n_i)` | % of bins electron-rich |
|---|---|---|---|
| `kin_bg` | 574–1719 (**fully resolved**) | **1.006 ± 0.069** | **50 %** |
| `flashic` | 24–152 (marginal) | **1.001 ± 0.091** | **49 %** |
| `flashic_ct` | resolved to ζ = 50, then **exactly 0 beyond ζ = 70** | 1.037 ± 0.140 | 43 % |

**Quasineutral to 0.1 %, with the sign of the departure a coin flip.** There is no coherent
charge separation in any leg, so there is no ambipolar precursor. Two consequences:

* **`kin_bg`'s shelf is its own ambient background.** It sits at 1e-3 `n_cr`, which is the
  configured `ambient.density_over_ncr`, and it is fully resolved. Not a plume feature at
  all — and a reminder that bg3-vs-bg4 moved the plume front 1.8×.
* **`flashic`'s trough is a REAL, quasineutral density minimum** — marginally resolved, but
  a genuine two-population structure rather than noise or kinetics. The likeliest reading
  is that its fitted initial corona was launched as a **distinct shell** ahead of the
  newly-ablated plume and never merged with it, i.e. **an unrelaxed initial condition**.
  `flashic_ct`, whose corona expands 5.2× faster in absolute terms, has no shelf at all by
  τ = 27 — consistent with the shell having already run off the end.
* **`flashic_ct` has a hard cutoff, not a tail.** Zero macroparticles beyond ζ = 70 against
  FLASH's smooth exponential still at 7.5e-3 `n_cr` at ζ = 100. That is the finite-slab
  free-expansion signature (plateau then cliff), not the semi-infinite rarefaction.

### D-2 — non-isothermality explains 50–82 % of the profile shape, for the legs where it can be measured
The isothermal rarefaction `n = n_cr exp(−z/C_S t)` has `d ln n/dζ = −1/(τ·C_S/C_S0)`,
**constant in z only if `T_e` is**. `R` below is the fraction of the profile-shape variance
removed by dividing the measured slope by the prediction formed from each leg's own local
`T_e(z)`.

| leg | raw slope std | corrected | **R** |
|---|---|---|---|
| FLASH | 0.330 | 0.460 | **−1.15** |
| `flashic` | 11.70 | 3.68 | **0.82** |
| `flashic_ct` | 1.05 | 0.744 | **0.50** |
| `kin_bg` | 0.681 | 1.321 | −2.42 (**metric invalid, see below**) |

* **For the two no-background legs, knowing `T_e(z)` removes 50–82 % of the structure.**
  So non-isothermality is most of the shape difference, as proposed — but not all of it.
* **FLASH's `R` is negative, and that is meaningful rather than broken here**: its density
  profile is *more* exponential than its own residual `T_e` variation would predict, which
  is what an imposed diffusive conduction operator does — it flattens `T_e` and the
  leftover variation is small and uncorrelated with the density slope.
* **`kin_bg`'s `R` is not usable**, and the reason is itself the finding: its `T_e`
  **maximum is in the tenuous far field** (the hot tail), so the "restrict to beyond the
  `T_e` plateau onset" cut leaves only a 10-ζ window at τ = 27. A leg whose temperature
  peaks outside its own plume has no isothermal region to fit.

### MY ERROR, corrected mid-diagnostic
The first version of `d2_shape.py` fitted the whole underdense band and reported **R < 0
for FLASH itself** — "knowing `T_e` makes FLASH less exponential", which is a broken metric,
not a result. Cause: the band includes the ablation front, where `T_e` ramps from ~0 over a
few `d_i0` and `1/√T_e` diverges. The fit is now restricted to beyond the `T_e` plateau
onset (first ζ at which `T_e` exceeds half its in-band maximum). Recorded because the
broken version's numbers were *plausible* — every leg came out negative together, which
reads as a physics result rather than a bug.

### The reservoir: `TargetInjector` is available and is the right tool
`warpx-cda/Source/Particles/TargetInjector/` — a density-relaxation injector ported from
PSC's `InjectFoil`. Each application it deposits the measured density of a species group
and, inside a user-given box, replenishes the deficit toward a target `n_t` on a relaxation
time `τ_inj`, **co-injecting a neutralizing species in exact charge balance**. That is
precisely the semi-infinite reservoir the comparison is missing: it pins the slab at `n_t`
and replaces what ablates away, converting a disassembling foil into a solid.

* **It is already in `build_cuda1d/bin/warpx.1d`** (substring check on `target_injector`,
  `ppc_reference`, `neutralizing_species` — all present), so **no rebuild is needed**.
* **It is NOT plumbed through `make_inputs.py`.** `config.yaml` cannot express it today,
  and CLAUDE.md forbids hand-editing a deck. This is a generator gap, and closing it is the
  prerequisite for the reservoir test.
* Keys: `target_injector.{species, intervals, lo, hi, density, reference_density,
  ppc_reference, tau, random_positions, neutralizing_species}` plus per-species
  `{fraction, u_std}`.

### Where this leaves the discrepancy
Three distinct causes are now separated, and only one of them is the closure:

1. **Finite reservoir** — `flashic_ct` cuts off hard where FLASH continues. Addressable
   with `TargetInjector`, and that is the next run.
2. **Unrelaxed initial condition** — `flashic`'s trough is its own corona as a detached
   shell. Addressable by relaxing the IC before the laser fires, or by the injector.
3. **No electron conduction** — the residual 18–50 % of shape variance, plus the far-field
   `T_e` maximum in `kin_bg`. This is D2b/D3-Appendix-C and is the one that needs the
   `conducting` closure or a heat-flux measurement.

---

## 2026-08-18 (final, last) — The semi-infinite reservoir is NOT the cause: `TargetInjector` plumbed, run, and the hypothesis falsified

`runs/P4/P4_lez_kin_flashic_res` (new, 149 184 steps, **14 min** on one RTX 4070, no NaN,
`--verify` OK). `src/laserprod/{deck,config}.py` gain an `injector:` block;
`tests/test_injector_schema.py` (10 checks). 345 tests pass.

### The tooling gap, closed
WarpX's `TargetInjector` — a density-relaxation injector ported from PSC's `InjectFoil` —
was **already compiled into `build_cuda1d`** but **not expressible in `config.yaml`**, so
the reservoir test could not be run without hand-editing a deck. `make_inputs.py` now emits
`target_injector.*`, and `config.validate` refuses, at config time rather than after the
queue hands over the GPU: unknown species names, a box outside the domain, an inverted box,
non-positive `tau`/`ppc`, and **pinning above the target's own density** — the operator
replenishes a *deficit*, so a higher value is a particle **source** and breaks G6 rather
than crashing.

Two details that would have failed silently:
* injected ions carry **`u_std = sqrt(th_tis/mass_ratio)`** like every other ion block.
  Omitting the division injects ions hot by √2698 = **52×** and heats the reservoir the
  injector exists to hold cold.
* injected particles carry the **SOLID** temperatures (`th_ts`), not the corona's — they
  stand for undisturbed material behind the ablation front.

### The run: a genuine single-variable test
The deck differs from `P4_lez_kin_flashic_ct` **in the injector block and nothing else**
(verified by diff) — which the parent, changing two things at once, was not. The box pins
the **rear half** of the slab (−200 → −100 `d_e`) at its own 40 `n_cr`, stopping 100 `d_e`
short of the laser-facing face so the ablation front stays free.

### FALSIFIED — and the injector demonstrably worked, so it is a real null

| | `_ct` (foil) | `_res` (pinned) |
|---|---|---|
| total electron weight end/start | 1.000 | **1.146** (+29 310 macroparticles) |
| weight inside the pinned box | 6.12e23 | **8.10e23 (+32 %)** |
| plume front `ζ` at τ = 27 | 43.7 | **43.7 (unchanged)** — FLASH 94.6 |
| `n_e/n_cr` at ζ = 70 | 0.0 | 4.7e-8 — FLASH **3.3e-2** |
| `L_n` | 23.3 | **17.9**, i.e. AWAY from FLASH's 21.4 |
| plume `T_e` | 124.2 eV | 130.1 eV |
| `f_abs` | 0.603 | 0.637 |
| shape raw slope std | 1.050 | **0.933** — FLASH **0.330** |

**Feeding the target does not lengthen the plume.** The added mass stays in the slab (peak
`n_e` 46.3 → 47.0 — it was already *compressing*, not running out). The plateau-and-cliff
survives intact. The profile shape improves **11 %** against a **3.2×** gap.

### The number that made the null predictable, and was there all along
`_ct`'s total electron weight ratio over the whole run is **exactly 1.000** — **no weight
ever left the domain.** The "PIC loses 5–15 % of its reservoir" figure describes material
moving from slab to plume, *not* mass being lost, so there was never a global deficit for a
reservoir to fill. A local deficit did exist inside the box (hence +32 %), and filling it
changed nothing downstream. **I should have checked the weight budget before building the
feature** — it cost ~1 h of plumbing to learn something one diagnostic would have said.
The plumbing is not wasted (it is the tool D5 always needed), but the ordering was wrong.

### Where the discrepancy now stands — one cause left standing
Of the three separated on 2026-08-18:

1. ~~**Finite reservoir**~~ — **ELIMINATED** by this run, at 14 GPU-minutes.
2. **Unrelaxed initial condition** — still live for `flashic` (its corona as a detached
   shell), but `flashic_ct`/`_res` show the cliff *without* a shell, so it is not the whole
   story either.
3. **No electron heat conduction** — **now the leading cause by elimination.** FLASH's
   smooth exponential is a statement that its plume is isothermal, enforced by
   flux-limited Spitzer-Härm; WarpX has no conduction operator, its `T_e` is not flat, and
   `kin_bg`'s `T_e` *maximum* sits in the tenuous far field. `D2b` (the hybrid `conducting`
   closure) and `D3` Appendix C (the heat-flux gate) are the two tests that address it, and
   **neither has ever been run**.

Cost note: `f_abs` is now 0.637 against FLASH's 0.870 and plume `T_e` is 1.25× its own
Manheimer value, so this leg is over-performing its absorbed flux by a wider margin than
before — unchanged in kind from the parent, and still unexplained.

---

## 2026-08-18 (final, last but one) — Fig. 2 replicated: the corona is LOAD-BEARING, FLASH's conduction is sound, and the two codes are in different transport regimes

`scripts/fig2_ic.py` (new), `studies/plume_structure/d12_transport.py` (new). Analysis
only. `runs/P4/P4_lez_kin_bg5` launched (see below).

### Fig. 2 — the paper's own acceptance test for an initial condition
The paper initialises PIC from the FLASH 0.1 ns snapshot and shows four panels: `n_e`,
`T_e`, flow speed, and **laser power absorption**, claiming "identical laser power
absorption profiles". **Panel (d) is the test that matters**: the corona is not required to
match FLASH pointwise, it is required to *absorb the same way*.

Replicated at t = 0.1 ns, each leg on its own `d_i0`:

| leg | `m_i/m_e` | ζ(critical surface) | max `T_e` | **peak `P_abs` at ζ** |
|---|---|---|---|---|
| **FLASH** | — | **0.27** | 379.4 eV | **0.27** |
| `flashic` (exponential corona, 378.3 eV) | 2698 | **0.23** | 419.5 eV | **0.28** |
| `kin_bg` (Gaussian corona, 100 eV) | 2698 | 4.08 | 107.2 eV | **4.13** |
| `flashic_ct` | 100 | 1.17 | 53.0 eV | 1.95 |

### The corona is NOT a smoothing approximation — it decides where the laser lands
This answers the question directly. Moving from the fitted exponential corona to the
analytic Gaussian moves the **peak deposition from ζ = 0.28 to ζ = 4.13**, a factor **15 in
position**, and the critical surface from 0.23 to 4.08. It is consistent with what
`CLAUDE.md` already records — `L_n/w_t` 0.19 → 0.75 took the optical depth to the turning
point from 0.14 to 5.60 and `f_abs(0)` from 0.248 to **1.000**. The corona sets the
absorption *regime*, not the amount. **No late-time comparison is meaningful until the IC
passes panel (d).**

And `flashic`'s IC **passes it**: deposition peak 0.28 vs 0.27, critical surface 0.23 vs
0.27, the 378.3 eV plateau against FLASH's 379, and a velocity ramp that overlies FLASH's
to ζ ≈ 7. **So the earlier characterisation of that IC as a "mixed-unit transfer" that was
2.638× too hot is too strong**: judged by the paper's own criterion the absolute-eV corona
is *correct*, because it is a handoff of FLASH's state, not a prediction of the reduced-mass
steady state the run will later relax toward. Those are different criteria and this file
previously conflated them.

### MY BUG: `flashic_ct` and `flashic_res` carry a corona 5.19× too extended
When `mass_ratio` went 2698 → 100 I rescaled the temperatures, the drift and `max_step`,
but **not the corona geometry**. `scale_length_de` = 6.955 and `corona_offset_de` = 2.3144
were derived in FLASH ζ and converted assuming `d_i0` = 10 `d_e`; at `m_i/m_e` = 100 the
proton skin depth is 1.925 `d_e`, so in normalised units that corona is **5.19× too wide**
and should have been 1.339 and 0.4456 `d_e`. It is why `flashic_ct`'s critical surface sits
at ζ = 1.17 against FLASH's 0.27. The reservoir A/B is unaffected — both legs carried the
same corona, so it remains a valid A/B — but **neither `_ct` nor `_res` was ever a good
match to FLASH's IC**, and their absolute agreement numbers should not be quoted.

### (1) FLASH's flux limiter is NOT the explanation — hypothesis not supported
I proposed that FLASH's flat plateau might be an artifact of its flux limiter, which would
have made part of the discrepancy FLASH's error. **The delivered checkpoints say
otherwise.** Restricted to the compared plume (1e-2 ≤ `n_e/n_cr` ≤ 1):

* **median `fllm` = 0.969**, i.e. the limiter removes ~3 % of the classical flux
* 93 % of cells are limited at all, but only **6 % are cut by more than half**

My first look reported 46 % of cells cut by more than half — that was the **whole domain**,
dominated by the cold chamber and the dense target interior, neither of which is compared.
**In the plume, FLASH is running essentially classical Spitzer-Härm.** The plateau is
physics, not a fudge factor.

### (2) The two codes are in DIFFERENT transport regimes — and FLASH is the valid one
`Kn = λ_ei/L_T`, density-weighted over the same band. Spitzer-Härm requires `Kn` ≲ 0.06:

| leg | median `Kn` | % of cells `Kn` > 0.06 |
|---|---|---|
| **FLASH** | **0.018 – 0.024** | 20 – 25 % |
| `kin_bg` (2698) | **0.13 – 0.16** | 65 – 78 % |
| `flashic` (2698) | 0.19 – 4.0 | 71 – 91 % |
| `flashic_ct` (100) | 0.04 – 0.25 | 25 – 91 % |

**FLASH sits just inside its own model's validity; the PIC legs sit well outside it.** So
the codes *should* disagree on `T_e` shape — a plateau is what a local diffusive closure
produces and a kinetic code has no obligation to reproduce it.

**Two caveats, both load-bearing.** (a) The PIC `T_e` is a binned particle moment, so a
pointwise `dT_e/dz` is dominated by shot noise; unsmoothed, `flashic` reports `Kn` = 19,
which is a noise floor rather than a plasma statement. The table above smooths `T_e` over 9
cells before differentiating — FLASH, a fluid solution, is left unsmoothed, which is the
like-for-like choice. (b) **`Kn` is computed from the very `T_e` profile whose shape is the
thing being explained**, so it partly restates the symptom. The non-circular content is
FLASH's own number: 0.02, i.e. FLASH passes its own validity test, so the gap is ours to
explain rather than FLASH's.

### `P4_lez_kin_bg5` launched — the clean 2698 leg
`P4_lez_kin_flashic`'s IC (which passes Fig. 2) with a background of **1e-5 `n_cr`**, the
paper's stated PIC floor, instead of `kin_bg`'s 1e-3 — which is **33 940×** the 1e-10 g/cm³
chamber it stands for, and which moved the plume front **1.8×** between bg3 and bg4. The
paradox it tests: **the leg with the correct IC (`flashic`, `f_abs` 0.358) agrees worse than
the leg with the wrong one (`kin_bg`, 0.769)**, which suggests the dense background is doing
the work as a tamper. ~1 h 30 m.

**Cost note recorded before it bites again:** the complete 10-pair collision set (adding
ambient self- and target↔ambient collisions) ran at **0.058 s/step against 0.0068 — 8.5×,
ETA 12 h 28 m** — because every pair touching an ambient species walks all 5376 cells while
the target occupies ~1000. Cut back to the target-only 3 pairs, matching both parents, so
the run differs from `flashic` in exactly one thing. The background is therefore
collisionless, as in every earlier leg — deliberate, and noted rather than silent.

---

## 2026-08-18 (final, actually last) — Read back against the paper's own setup: **ppc is 200× too low**, and four other departures

No new runs. `P4_lez_kin_bg5` was **killed at 30 %**: the paper states outright *"We do not
introduce any chamber gas … since we are unable to fully capture the physics at such low
densities"*, so testing a thinner background was testing the wrong axis. Superseded by the
table below.

### Every PSC parameter the paper states, against our decks

| parameter | **PAPER (PSC)** | `P4_lez_kin` | `kin_bg` | `flashic` |
|---|---|---|---|---|
| box length | 1000 `d_e` = 100 `d_i0` | 2500 | 2500 | 2688 |
| cells | 5000 | 5000 | 5000 | 5376 |
| **cells per `d_e`** | **5** (`dz` = 0.2) | **2** (0.5) | 2 | 2 |
| **`N_ppc` at `n_cr`** | **100 000** | **500** | 500 | 500 |
| **density floor** | **1e-5 `n_cr`** | **2e-3** | 2e-3 | 2e-3 |
| chamber gas | **NONE**, explicitly | none | **1e-3 `n_cr`** | none |
| `n_max` | 10 `n_cr` | 10 ✓ | 10 ✓ | 40 |
| target thickness | 4.5 `d_i0` | 4.5 ✓ | 4.5 ✓ | 20.0 |
| boundaries | **reflecting** | refl / **open** | refl / **open** | refl / **open** |
| e–i / i–i rate correction | **YES** (Ref. 47) | **NO** | NO | NO |
| Coulomb log | single global | ✓ | ✓ | ✓ |

### 1. `N_ppc` = 500 against the paper's 100 000 — a factor 200, and the new leading suspect
The paper is explicit about what that number buys: *"This particle number allows us to
resolve densities greater than 1e-5 `n_cr`."* The PIC density floor is `n_cr/N_ppc`, so
**ours is 2e-3 `n_cr` where theirs is 1e-5** — we cannot represent the tenuous plume at all,
and FLASH's exponential runs well below our floor.

Worse, it attacks the one quantity still in dispute. **The `T_e` "hot tail rising outward"
may substantially BE ppc noise**: a per-cell temperature at 500 ppc in a rarefied plume is a
small-sample estimate whose upper tail is heavily biased, and this file has already been
bitten by it twice — `CLAUDE.md` records that `T^(-3/2)` convexity biases absorption high at
low ppc, and today's `D-2` Knudsen analysis returned `Kn` = 19 for `flashic` until the
temperature was smoothed, which is a noise floor rather than a plasma statement. **A `T_e`
shape argued from 500 ppc is not yet a physics result.**

### 2. Resolution: 2 cells per `d_e` against the paper's 5
Also the cheapest route to the worst gate we have: `dz/λ_D` = 116–327 would improve by 2.5×
on the same change.

### 3. The `hi` boundary is `open`; the paper uses **reflecting**
Hot electrons leave our box and in PSC they do not. That truncates the ambipolar potential
which drives the expansion, and the plume front running **0.71×** short is exactly the
symptom it would produce. The paper's 100 `d_i0` box is only just longer than the plume it
contains (~95 `d_i0` at τ = 27), so the reflecting condition is load-bearing, not incidental.

### 4. Our box is 2.5× longer at the same cell count
Which is *why* we are 2.5× coarser. Matching the paper's box would buy the resolution back
for free.

### 5. The collision-rate correction we do not have — and the paper's own warning
*"Caution should be used when modeling collisions in PIC systems with reduced speed of light
and mass ratio parameters, since they will modify the relative role of e–e, e–i, and i–i
collisions **if treated uniformly**. A special approach to match e–i and i–i collisional
rates is implemented in PSC."* WarpX treats them uniformly. `D3` measured WarpX's e–i rate
against Spitzer and passed, but **that is not the same as having the correction** — the
correction is about the *relative* rates, which no single-pair test can see. TEST_PLAN
§12.8 risk 1 remains open, and `D3` Appendix C is still unrun.

### What the paper's own convergence study says we do NOT need
`n_max` was scanned over {2, 5, 10, 20} `n_cr`: *"The underdense plasma density evolves
similarly in all cases. However, electron temperature matches only when `n_max` ≳ 5 `n_cr`."*
So 10 is sufficient and `flashic`'s 40 buys nothing — consistent with the reservoir
falsification earlier today, and a second independent reason to go back to the thin
paper-faithful target.

### Consequence
The paper-faithful deck has never actually been run. `P4_lez_kin` matches it on `n_max`,
thickness and chamber gas but misses on ppc (200×), resolution (2.5×), box length (2.5×)
and the `hi` boundary. **Before any more physics is inferred from the `T_e` shape, a ppc
ladder is required** — it is the one departure large enough to manufacture the disputed
feature on its own.

---

## 2026-08-18 (final, truly last) — RETRACTION of "ppc is 200× too low", and the ppc ladder finally runs

`studies/ppc_ladder/` (new), `numerics.density_min_frac` plumbed,
`tests/test_density_min_frac.py`. 354 tests pass.

### RETRACTION: the ppc comparison in the previous entry is wrong
That entry called `N_ppc` = 500 vs the paper's 100 000 a "factor 200" and made it the
leading suspect for the `T_e` tail. **That is only true at `n_cr`.** The paper loads
*"10^5 **equally weighted** particles per cell per species at critical density"* — uniform
weight, so its particle count scales with the local density:

| `n/n_cr` | 10 | 1 | 0.1 | 1e-2 | **1e-3** | 1e-4 | 1e-5 |
|---|---|---|---|---|---|---|---|
| PSC ppc | 1e6 | 1e5 | 1e4 | 1e3 | **100** | 10 | 1 |
| ours (fixed 500) | 500 | 500 | 500 | 500 | **500** | 500 | 500 |

**PSC has more particles than us only above ~5e-3 `n_cr`. Below that we have more — and
that is exactly where the disputed hot tail lives.** So the correct loading scheme
*weakens* the "the tail is ppc noise" hypothesis rather than strengthening it. Where PSC is
genuinely better is the target and near-critical region (2000× at 10 `n_cr`), i.e. where the
laser deposits — which bears on absorption and the ablation front, not the plume tail.

Matching their ppc number is also not possible: uniform weight at `N_ppc(n_cr)` = 1e5 needs
**3.4e8 macroparticles per species** (~70 GB) for this target.

### The departures were already known and deliberate — I should have read the config first
`P4_lez_kin`'s `config.yaml` already documents nearly every item in the previous entry's
table, and **records the measurement that settles two of them**:

> *"The paper's 1000 `d_e` box does NOT hold this run: MEASURED 2026-08-13, the front
> reaches 949.8 of 950 `d_e` at 24.6 ps — 45 % through — and is pinned there for the
> remaining 30 ps … after, `T_e` climbs to 2.9× SS because the confined plasma cannot
> expand."*

So the 2500 `d_e` box and the **open** `hi` boundary are *deliberate, measured* departures,
not oversights: the paper's box confines our plume and drives `T_e` to 2.9× its steady
state. My "the boundary should be reflecting" item is answered — it was tried. The ppc note
in the same file already says *"the paper's ppc is quoted AT `n_cr` with equal weights, so
its ppc scales with density; ours does not … compare resolved dynamic range, not the
number"* — the exact point of this retraction, recorded weeks ago and not read.

**What survives from the previous entry:** the resolution (2 vs 5 cells per `d_e`), the
resolved dynamic range, and the absent e–i/i–i relative-rate correction.

### What is actually comparable: resolved dynamic range, and it is now a config primary
The floor is set by `density_min`, **not** by ppc, and it was hardcoded at `1e-4·n_t` — four
decades against the paper's six (10 `n_cr` down to the 1e-5 `n_cr` at which one uniformly
weighted macroparticle per cell remains). `numerics.density_min_frac` now exposes it, and
every ladder rung sets 1e-6 to span the same six decades.

### The ladder (decision D6, declared in `P4_lez_kin` and never run)
`studies/ppc_ladder/`: `P4_lez_kin` unchanged except ppc ∈ {500, 2000, 10000} and
`density_min_frac` = 1e-6. **The question is narrow and falsifiable: does the outward `T_e`
rise weaken with more particles?** If it does, it was sampling noise. If it survives 20×,
it is kinetic transport and D2b / D3-Appendix-C are the follow-ups. Rungs 500 and 2000 are
running (19 min and 53 min); 10000 follows on the first free card.

### Two process notes, both caught by the harness rather than by me
* **A formatting change is a deck change.** Plumbing `density_min_frac` made the default
  render as `0.0001*nt` where it had always been `1.e-4*nt` — the same number, and **36
  tests failed**, because they compare rendered decks against committed ones. Numerically
  identical is not good enough when `--verify` diffs text. Fixed with a `_pow10` formatter
  that reproduces the historical literal; the default is byte-identical again.
* **The Arena collision, exactly as recorded, because I launched two rungs on one card.**
  The second aborted at init. Now that `numerics.arena_init_size_mb` exists the generator
  sets 4096 MiB on every rung, so rungs can share a device instead of the first one taking
  3/4 of it.

---

## 2026-08-18 (last, ppc ladder rung 1) — **the `T_e` outward rise was the DENSITY FLOOR, not ppc and not kinetics**

`studies/ppc_ladder/analyze.py` (new). `L_ppc500` complete (552 960 steps, **20 min**, no
NaN); `L_ppc2000` at 20 %, `L_ppc10000` launched (ETA ~4 h).

### The metric
`RISE` = density-weighted `<T_e>` over the outer half of the underdense band ÷ the inner
half, split by position. FLASH's isothermal plateau gives ~1; a hot tail gives > 1; if the
tail is sampling noise it falls toward 1 as ppc rises.

### Result — and it is not the ppc axis that moves it

| leg | τ = 6.7 | 13.5 | 20.3 | **27.0** | `<T_e>` at 27 | vs own SS |
|---|---|---|---|---|---|---|
| **FLASH** | 1.023 | 1.077 | 1.125 | **1.148** | 839.0 eV | **1.02** |
| `P4_lez_kin` — **4 decades**, 500 ppc | 1.042 | 1.242 | 1.305 | **1.504** | 473.2 eV | **1.52** |
| `L_ppc500` — **6 decades**, 500 ppc | 0.945 | 1.015 | 1.144 | **1.133** | 361.6 eV | **1.16** |
| `L_ppc2000` — 6 decades, 2000 ppc | 0.944 | — | — | — | — | — |

**Widening the resolved dynamic range from four decades to six — `density_min_frac`
1e-4 → 1e-6, the ONLY difference between the first two rows, verified by config diff —
takes the outward rise from 1.504 to 1.133, against FLASH's own 1.148.** The shape
discrepancy that has been the last open item all day essentially closes on that one change.

It moves the magnitude too: plume `<T_e>` against each leg's own Manheimer value goes
**1.52× → 1.16×**, where FLASH sits at 1.02×.

**And ppc is not the lever.** At τ = 6.7 the 500 and 2000 rungs give `RISE` = 0.945 and
0.944 — quadrupling the particle count moves it by 0.1 %. That is exactly what the
retraction earlier today predicted: our fixed-ppc loading already gives us *more* particles
than PSC has below 5e-3 `n_cr`, so ppc was never the binding constraint in the plume. The
binding constraint was that **we were culling the plume at 1e-3 `n_cr` where the paper
resolves to 1e-5**, and the cells nearest that cull were the ones reporting a hot tail.

### Why this was invisible for so long
`density_min` was **hardcoded** at `1e-4·n_t` in `deck.py` — it was not a config primary, so
it never appeared in a run's parameter table, never varied in a sweep, and could not be seen
in a config diff between legs. Every Phase-4 leg carried the same four decades and therefore
the same artifact, which made it look like a property of WarpX rather than of our deck.

### Status of the three candidate causes
1. ~~Finite reservoir~~ — eliminated by the injector run.
2. ~~Unrelaxed initial condition~~ — `flashic`'s trough, real but not the shape driver.
3. **No electron heat conduction** — **demoted.** Most of what was attributed to a missing
   `∇·q_e` was a density floor. Whether a residual 1.133 vs 1.148 needs any closure argument
   at all is now the question, and it is a much smaller one.

### Not yet closed
* `L_ppc2000` and `L_ppc10000` must reach τ = 27 before "ppc does not matter" is more than a
  τ = 6.7 statement.
* `<T_e>` = 362 eV is still 1.16× its own steady state against FLASH's 1.02×, and `f_abs`
  has not been re-measured on the six-decade decks.
* The lower floor loads more tenuous plasma, so the density-weighted mean is taken over a
  different population; part of the 473 → 362 eV move is that reweighting rather than a
  physical cooling. The `RISE` ratio is constructed to be insensitive to it, but the
  absolute `<T_e>` comparison is not.

### Process note
`analyze.py`'s first version reported **identical numbers at τ = 13.5, 20.3 and 27.0** for
the 20 %-complete rung — one dump wearing three labels, because `xcode_compare.pick()`
returns the nearest entry unconditionally. A coverage guard now drops a requested τ rather
than relabelling a dump. It is the same trap `talk_xcode.py` already carries `TAU_TOL` for,
and it produced numbers that looked entirely plausible.

---

## 2026-08-18 (last, addendum) — **the comparison was misaligned in time by 2.696 τ**, and correcting it makes agreement worse

`scripts/xcode_compare.py` gains `--tau-offset`, defaulting to **2.696 (aligned)**.

### The error
Every Phase-4 WarpX leg's `t` = 0 **is FLASH's `t` = 0.1 ns**, i.e. FLASH's τ = 2.696 — the
fitted ICs by construction, and the analytic one because its scale length was *derived* as
`C_S t` at 0.1 ns (`P4_lez_kin`'s config: *"0.1 ns = 2.69 ion response times, so
`C_S t` = 2.69 `d_i0` = 27 `d_e`"*). `xcode_compare.py` nevertheless sampled both codes at
**equal τ**, so it compared states **2.7 τ apart — 10 % of the run** — and gave the WarpX
legs 1.1 ns of elapsed process against FLASH's 1.0.

`talk_xcode.py` has carried a `--tau-offset` flag for this since it was written, defaulting
to 0 *"to keep the convention the RESULTS.md numbers were measured on"*. The main comparison
script had no such flag, so the misalignment was never applied there and never visible.

### Correcting it moves the WarpX legs AWAY from FLASH
τ is now FLASH's clock; a leg is sampled at τ − 2.696.

| at FLASH τ = 27 | unaligned | **aligned** | FLASH |
|---|---|---|---|
| `ζ_front`, 6 decades | 68.66 (0.73×) | **60.22 (0.64×)** | 94.57 |
| `L_n`, 6 decades | 14.47 (0.68×) | **12.78 (0.60×)** | 21.42 |
| `ζ_front`, hybrid | 92.37 (0.98×) | **81.95 (0.87×)** | 94.57 |
| `L_n`, hybrid | 17.76 (0.83×) | **15.29 (0.71×)** | 21.42 |

The direction is right and unflattering: the unaligned comparison was giving every WarpX leg
an extra 2.7 τ of expansion, and the hybrid's much-quoted **0.98× plume front is 0.87× once
the handoff is aligned**.

### Scope of the correction
**Every plume-front, `L_n` and profile number in this file recorded before today was
measured unaligned**, including the "FLASH↔kinetic benchmark passes" entry and the
hybrid's front/velocity agreement. Those are not retracted — the runs and the measurements
stand — but they are systematically 2.7 τ generous, and any of them re-quoted should be
re-measured with the default. `--tau-offset 0` reproduces the old convention exactly.

Not affected: absorbed fractions (integrated over the whole run), `T_e` against each leg's
own Manheimer value (a plateau, so 2.7 τ moves it little — 361.6 → 350.8 eV), and every
Fig.-2 initial-condition number (τ = 0 on both clocks by construction).

### Figures
`media/xcode/` rebuilt with three curves — FLASH, `kinetic, 6 decades` (`L_ppc500`) and
`hybrid` — on the aligned clock. The dropped legs stay one `--leg` away.

---

## 2026-08-18 (last, correction) — the six-decade result was measured on the WRONG corona; `P4_lez_kin_ic6` fixes it

`L_ppc2000` (40 %) and `L_ppc10000` (0.2 %) **killed**. Two reasons, both sound: ppc is not
the lever (500 vs 2000 gave `RISE` 0.945 vs 0.944 at τ = 6.7, a 0.1 % move), and **every
ladder rung inherited `P4_lez_kin`'s analytic Gaussian corona** — the initial condition that
*fails* the paper's own Fig.-2 acceptance test.

### The mistake
`L_ppc500` produced the largest single step toward FLASH all campaign — `T_e` rise
1.504 → 1.133 against FLASH's 1.148, from widening the resolved density range alone. But it
was generated from `P4_lez_kin`, whose corona is the analytic Gaussian: **peak laser
deposition at ζ = 4.13 against FLASH's 0.27, critical surface 4.08 against 0.27**. The
density-floor A/B remains valid (both sides carried the same corona) but the leg is not a
FLASH match, and it should not have gone into the comparison figure as one.

### `P4_lez_kin_ic6` — six decades AND the FLASH-fitted corona
`L_ppc500`'s geometry and dynamic range, with `P4_lez_kin_flashic`'s exponential corona,
temperatures and initial drift, on the **paper-faithful target** (10 `n_cr`, 4.5 `d_i0`)
rather than `flashic`'s reservoir-motivated 40 and 20 — the reservoir having been falsified
earlier today, and the paper's own `n_max` scan finding `T_e` matches for `n_max` ≳ 5 `n_cr`.

**It passes the Fig.-2 acceptance test, measured from its step-0 deposition dump:**

| leg | ζ(critical surface) | max `T_e` | **peak `P_abs` at ζ** |
|---|---|---|---|
| **FLASH** | 0.27 | 379.4 eV | **0.27** |
| **`P4_lez_kin_ic6`** | **0.23** | 408.2 eV | **0.28** ✓ |
| `P4_lez_kin_flashic` | 0.23 | 419.5 eV | 0.28 ✓ |
| `L_ppc500` (Gaussian) | 4.08 | 108.3 eV | **4.13** ✗ |

**And all four pre-run gates pass for the first time in this phase** (`ω_pe·dt` = 0.783,
`dz/λ_D` = **58.1** against 116 on the 100 eV corona — the hotter FLASH corona doubles the
Debye resolution). Every earlier Phase-4 deck carried two warnings.

### What is still true from the ladder
* **The density floor is the dominant lever on the `T_e` shape** — `P4_lez_kin` vs
  `L_ppc500`, single-variable, 1.504 → 1.133. That A/B is clean.
* **ppc is not** — 0.1 % across 4×, at τ = 6.7.
* Both were measured on the Gaussian corona, so whether the floor result *transfers* to the
  correct IC is exactly what `P4_lez_kin_ic6` now tests.

---

## 2026-08-18 (final) — `P4_lez_kin_ic6`: the shape result **transfers** to the correct IC, and the run turns out not to have reached steady state

`runs/P4/P4_lez_kin_ic6` complete — 552 960 steps, **21 min** on one RTX 4070, no NaN,
`--verify` OK. Figures rebuilt on the aligned clock with this leg in place of `L_ppc500`.

### It passes the acceptance test the Gaussian-corona legs failed
From its own step-0 deposition dump: **peak `P_abs` at ζ = 0.28 against FLASH's 0.27**,
critical surface 0.23 against 0.27, corona 408 eV against 379. `L_ppc500` sits at 4.13 and
4.08. And **all four pre-run gates pass**, the first Phase-4 deck to do so
(`ω_pe·dt` = 0.783, `dz/λ_D` = 58.1 against 116 — the hot FLASH corona doubles the Debye
resolution).

### The `T_e` shape result survives the corona change — this was the open question
`RISE` (outer/inner `<T_e>` over the underdense band; FLASH's plateau ≈ 1):

| leg | τ = 6.7 | 13.5 | 20.3 | **27.0** |
|---|---|---|---|---|
| **FLASH** | 1.023 | 1.077 | 1.125 | **1.148** |
| `P4_lez_kin` — 4 dec, Gaussian | 1.042 | 1.242 | 1.305 | **1.504** |
| `L_ppc500` — 6 dec, Gaussian | 0.945 | 1.015 | 1.144 | **1.133** |
| **`P4_lez_kin_ic6` — 6 dec, FLASH IC** | 1.354 | 1.899 | 1.640 | **1.161** |

**1.161 against FLASH's 1.148.** So the density-floor result was not an accident of the
Gaussian corona: two different initial conditions, both at six decades, land within 2 % of
FLASH's own outward rise, while the four-decade version sits 31 % above it. **The `T_e`
shape discrepancy — the last open item of the campaign — is a resolved-dynamic-range
artifact, not missing electron conduction.**

The velocity profile is the other clear win: on the aligned clock `v_z/C_S` overlies FLASH's
from τ = 13.5 to 27.

### But the run has NOT reached steady state, and that is new
`<T_e>` in the plume climbs **129.8 → 183.8 → 224.6 → 271.2 eV** across the four times, with
no sign of flattening (increments 54, 41, 47), where FLASH is visibly plateauing
(599 → 733 → 794 → 839, increments 134, 61, 45). At the end `f_abs` is still **0.992** —
the target remains optically thick and the laser is still being fully absorbed, so energy is
still going in.

That inverts the earlier legs, whose absorption decayed as the target went underdense. With
the compact FLASH corona and a properly resolved plume the target holds (peak `n_e` 10.18,
essentially its initial 10) and keeps absorbing. **Comparing at τ = 27 therefore compares a
converged FLASH against an unconverged WarpX**, which is the most likely reason the
remaining metrics look short:

| at FLASH τ = 27, aligned | `ic6` | FLASH |
|---|---|---|
| `f_abs` (whole-run mean) | 0.478 | 0.870 |
| plume `<T_e>` / own SS | **0.795** (still rising) | 1.019 |
| `ζ_front` | 47.9 (0.51×) | 94.6 |
| `L_n` | 9.73 (0.45×) | 21.4 |
| `ζ_cr` | 1.51 (0.36×) | 4.16 |
| peak `n_e` | 10.18 (initial 10) | 4141 |

### The obvious next run
**Extend `ic6` until `T_e` plateaus** — it is 21 minutes, so 3–4× the duration is under two
hours. Until it does, `f_abs`, `ζ_front` and `L_n` are being read off a transient and none of
them is a fair test. The shape result stands regardless, because `RISE` is a ratio within a
single profile rather than a comparison of two clocks.

---

## 2026-08-18 (final, deposition) — **why the kinetic plume is slower: the absorption is 2.4× too concentrated**

`scripts/deposition_compare.py` (new), `media/P4/P4_lez_kin_ic6/deposition_compare.png`.
`flash_series` now also returns `dens`.

### The measurement
ζ by which 50 % and 90 % of the absorbed power has been deposited, counting inward from the
laser side. Clocks aligned (a WarpX leg's `t` = 0 is FLASH's τ = 2.696):

| FLASH τ | kinetic τ | `ζ`(50 %) FLASH | kinetic | `ζ`(90 %) FLASH | kinetic |
|---|---|---|---|---|---|
| **2.7** | 0.0 | **0.38** | **0.43** | **1.02** | **0.93** |
| 9.4 | 6.7 | 2.42 | 1.43 | 7.11 | 4.08 |
| 16.2 | 13.5 | 5.71 | 1.93 | 15.72 | 7.18 |
| **22.9** | 20.2 | **9.26** | **3.78** | **25.41** | **11.83** |

**At the handoff the two deposition profiles are the same** — 0.38 vs 0.43 and 1.02 vs 0.93,
which is Fig. 2 passing, now confirmed on the volumetric profile rather than only at its
peak. **They then diverge monotonically.** By τ = 22.9 FLASH is laying 90 % of its power
down over 25.4 `d_i0` while the kinetic does it over 11.8 — and the half-power depth is
**2.45× shallower** (3.78 against 9.26).

### The mechanism, and it is not under-absorption
`f_abs` at the end of the kinetic run is **0.992** against FLASH's 0.870 — the kinetic leg
absorbs *more* of the beam, not less. It simply puts that energy into a much thinner layer
just outside the critical surface, where FLASH spreads it through an extended corona.

That is the answer to "why is the kinetic slower": **the same joules heat a smaller mass of
expandable plasma.** The ablative mass flux is set by the temperature reached in plasma that
can actually fly away, and a compact deposition layer heats a compact plume, which keeps the
absorption compact — a feedback FLASH escapes and the kinetic leg does not, within 27 τ.

It also explains the non-convergence recorded in the previous entry: the run is still
absorbing at essentially 100 % at `t_end`, so it is nowhere near the quasi-steady ablation
FLASH has settled into.

### Caveat on FLASH's absolute units, recorded rather than papered over
`depo` does not close the energy budget in either obvious interpretation: `∫depo dz` is
9.2e-10 of the absorbed intensity and `∫depo·dens·0.1 dz` is 1.2e-13, and the residual is
~1e13 ≈ 1/dt. So `depo` is almost certainly specific energy **per timestep** [erg/g] rather
than a rate. That factor is one number per dump and cancels in both panels here — the
profile is peak-normalised and the depth panel is a cumulative *fraction* — but **the
density weighting does NOT cancel and is applied**, since `depo` and `depo·dens` have
different shapes and skipping it moves `ζ`(50 %)/`ζ`(90 %) rather than merely rescaling them
(uncorrected, the FLASH depths read 0.59/1.78 → 17.87/46.94 instead of 0.38/1.02 → 9.26/25.41).
**Absolute W/m³ for FLASH is not established by this script and must not be read off it.**

### Next
The compact-deposition finding and the non-convergence are the same story told twice, so the
extended `ic6` run tests both at once: if the plume eventually expands, the deposition region
should broaden toward FLASH's and `f_abs` should fall off 0.99.

---

## 2026-08-19 — **G3 PASSES decisively: there is no grid heating.** `ic6`'s rising `T_e` is real absorption

`runs/P4/P4_lez_kin_ic6_off` complete — 552 960 steps, **17 min**, no NaN, `--verify` OK.
Deck differs from the physics run in **exactly one line** (`laser_deposition.intensity`),
verified by diff.

### The subtraction
Electron kinetic energy from the `EP` reduced diagnostic, over the whole run:

| | start | end | **gain** |
|---|---|---|---|
| driven (`ic6`) | 5.0771e5 J | 1.8424e6 J | **+1.3347e6 J** |
| **control (laser off)** | 5.0771e5 J | 3.2835e5 J | **−1.7936e5 J** |

**The control's electrons COOL by 35 %.** Grid heating does not merely fail to dominate —
it is **absent**: the laser-off run has no net numerical heat source at all, and the laser
has to work against a real cooling term rather than being flattered by a spurious one.

The energy that leaves the electrons goes where it should: ions **gain 1.9436e5 J** against
the electrons' 1.7936e5 J loss, so the transfer closes to **8 %** with no creation. That is
the ambipolar rarefaction doing exactly what it should in a laser-off expansion.

### What this settles
1. **`ic6`'s still-climbing `T_e` (129.8 → 271.2 eV) is laser absorption, not numerics.**
   The non-convergence recorded yesterday is physical: the run has not yet reached
   quasi-steady ablation, and the right response is to run it longer.
2. **Implicit PIC is not needed.** `theta_implicit_em` buys grid-heating immunity at ~1.9×
   per step; there is no grid heating here to be immune to.
3. **`dz/λ_D` = 253 in the cold solid is confirmed harmless for this measurement** — which
   is what the plume value of **1.8** predicted. The badly-resolved region is a mass
   reservoir, not the region any benchmark quantity is measured in. The 15-day resolved-λ_D
   run would have bought nothing.
4. The earlier decision to defer this control was, in the event, correct — but it is now
   **measured rather than argued**, and the argument that justified deferring it (grid
   heating suppresses absorption, so a high `f_abs` is self-validating) had genuinely
   stopped applying once `f_abs` reached 0.992 with `T_e` still rising.

### Also fixed
`ic6` had inherited `controls.laser_off: P4_lez_kin_off` down the config chain — the control
for a *different* deck (Gaussian corona, 100 eV, four decades). A G3 subtraction is only
meaningful against a run differing in the laser alone, so it now names its own control.

### Consequence
The extended `ic6` run is the clear next step and needs no numerical caveat: run it until
`T_e` plateaus, then read `f_abs`, `ζ_front` and `L_n` off a converged state instead of a
transient. The deposition finding (absorption 2.45× too concentrated) is unaffected either
way — it is measured at times FLASH covers.

---

## 2026-08-19 (extended) — `P4_lez_kin_ic6_long`: **still no plateau at 4× duration**, and the target burns through before one is reachable

`runs/P4/P4_lez_kin_ic6_long` complete — 2 211 840 steps, **1 h 01 m**, `reached max_step`,
`--verify` OK, no stray `.old.` plotfiles. Deck differs from the parent in duration and
diagnostic cadence only. τ_own 0 → **107.83** (218.64 ps).

The run was launched to settle one question: does the kinetic leg reach quasi-steady
ablation, and at what temperature? The README pre-registered three outcomes. The answer is
**outcome 3 (no plateau)** — but not for the reason outcome 3 was written to catch, and the
run's two secondary expectations were both **backwards**.

### `T_e` is still rising at τ 108, significantly

Density-weighted moments, `xcode_compare` definitions, over τ 70–108:

| | slope | significance | verdict |
|---|---|---|---|
| `Te_at_cr` (at the critical surface) | **+1.751 ± 0.436 eV/τ** | 4.0 σ | still rising |
| `Te_mean_plume` (band mean, 1e-2…1 `n_cr`) | **+2.092 ± 0.225 eV/τ** | 9.3 σ | still rising |

Eyeballing the last four dumps suggests a plateau (501 → 522 → 524 → 522 eV); the
regression does not. **The apparent flattening is scatter, not convergence** — recorded here
because the eyeball read was made first and was wrong.

### But it *is* converging — slowly, to a value close to Manheimer

Fitting the physically right model, `T(τ) = T_∞ − A exp(−τ/τ_relax)`:

| | `T_∞` | `τ_relax` | `T_∞`/`T_e,SS` (312 eV) | reached by τ 108 |
|---|---|---|---|---|
| `Te_at_cr` | **381.5 ± 21.5 eV** | 44.3 | **1.22** | 93.8 % |
| `Te_mean_plume` | 620.0 ± 11.5 eV | 60.2 | 1.99 | 84.2 % |

**`Te_at_cr` is the Manheimer comparator, not the band mean.** `T_e,SS` is the temperature
of the absorption region; the band mean is pulled up by the hot, tenuous far plume
(`Te_max_plume` exceeds 1000 eV). Read correctly, the kinetic leg extrapolates to **1.22 ×**
its own reduced-mass steady state — the physics is right and the approach is simply slow.
Read incorrectly it is 1.99 ×, which is how the earlier "disagreement" arose.

### The configuration can never reach that asymptote

Peak density decays as **`n_peak` = 18.66 exp(−τ/38.7)** over τ 35–108 (10.0 → 1.14 `n_cr`),
crossing **1 `n_cr` at τ ≈ 113** — five τ after this run ends, and far short of the ~3 `τ_relax`
≈ 130 needed. **The 45 `d_e` / 10 `n_cr` target is consumed on the same timescale as the
temperature relaxes.** Once `n_peak` < 1 there is no critical surface and `Te_at_cr` ceases
to exist as a diagnostic.

This is a **design finding, not a physics failure**: quasi-steady ablation is unreachable in
this configuration at any duration. Getting there needs a thicker or denser target (a mass
reservoir), not a longer run.

### Both secondary expectations were backwards

1. **`f_abs` rose; it did not fall.** The README expected absorption to fall away from 0.992
   as the target went underdense. Time-mean `f_abs` by window: **0.282** (τ<10) → 0.614 →
   0.859 → 0.954 → **0.975** (τ 78–108); whole-run mean **0.823**. The absorbing column is
   the **inner corona**, which lengthens as the target ablates: the deposition median moves
   4.3 → 38.8 → 114.3 → **236.8 `d_e`** (τ 0/27/54/81), always sitting near critical
   (`n_e` = 0.76 → 0.43 `n_cr`), and the 90 % quantile reaches only 590 `d_e`.
   **The far plume absorbs nothing** — 0.0 % of `P_abs` lands beyond 1500 `d_e` at every
   dump, and 84.8 % is still inside 500 `d_e` at τ 81. `Vskip` → 0 by τ ≈ 30 means only that
   no cell is *empty*, not that the far plume is optically active. Consequence for design:
   **box size does not set `f_abs`**, so the domain need only contain the absorbing corona
   (plus margin), not the whole plume.
2. **The domain risk half-materialised.** The `1e-2 n_cr` front hit the 2450 `d_e` wall at
   **τ 78.2**; the bulk `0.1 n_cr` contour only reached **1302 `d_e`**, comfortably inside,
   vindicating the README's extrapolation for the bulk but not for the tenuous precursor.

### Why the late data survive the boundary anyway

Outflow at the open boundary is **supersonic at all times — Mach 2.3 to 4.8** (local
`C_S` from the local `T_e`). The wall is therefore causally disconnected from the ablation
region and cannot feed back on it, so **local quantities near the critical surface are sound
to τ 108**. What is *not* sound is anything integrated over the band: edge `n_e` climbs
through the `1e-2` band floor at **τ 93**, so `ζ_front`, `L_n` and `Te_mean_plume` are
truncation-contaminated from **τ ≈ 102** and `ζ_front` pins at the wall (244.7 `d_i0`).

### Gates

| Gate | Value | Verdict |
|---|---|---|
| G1 `ω_pe dt` | 0.783 at 2× compression | PASS |
| G2 `dz/λ_D` | 58 cold target | INFO (G3 makes it meaningful) |
| G3 grid heating | inherited from `ic6_off` — measured **negative** | PASS |
| G4 `ray_cfl` | 0.25 | PASS |
| G5 ppc | 500 | PASS |
| G6 energy closure | **(ΔKE+ΔFE)/E_abs = 0.876** | see below |
| G7 `dz` | 0.5 `d_e`, unchanged | INFO |

**G6, with the loss fraction quoted beside it as the gate requires:** 53.5 % of *macro*particles
left the domain but only **0.89 %** of the *weight* — the escaping population is the
low-weight, high-energy tail of the exponential corona. The 12.4 % deficit is energy carried
out by those particles; its **sign is a loss**, which is the opposite of the grid-heating
signature and consistent with G3's negative result.

### No shock

Ion phase space is a clean self-similar rarefaction fan, `u_z` rising linearly to 5–8
`C_S(target)` at the wall, with **no reflected population**. As expected for pure ablation —
recorded because the project gates the word "shock" on this diagnostic.

### Tooling note

`laser_report.py` prints `f_abs peak` and `f_abs final` as **instantaneous** samples. Here
both read `1.0000` while the run-mean was `0.823` and the instantaneous value oscillates
between 0.75 and 1.00 late (0.08–1.00 early). The parent's quoted "`f_abs` still 0.992" is
the same kind of sample. **Quote a time-mean over a stated window instead.**

### Media
`media/P4/P4_lez_kin_ic6_long/{movie_fields,movie_phase}.mp4`, `laser_history.png`,
`laser_profile.png`, `checks.png`, `gates.png`.

---

## 2026-08-19 (convergence) — **the τ = 27 FLASH agreement is a coincidence of the transient**, and the real disagreement is 1.6–2.0×

Prompted by `P4_lez_kin_ic6_long`. Both codes' `T_e` histories were fitted to the same
model, `T(τ) = T_∞ − A exp(−τ/τ_relax)`, with the same `xcode_compare` scalars, and each
normalised by **its own** `T_e,SS` (FLASH 823 eV at real mass; WarpX 312 eV at μ = 2698 —
the μ^(1/3) transfer).

| `Te_at_cr` | `τ_relax` | at τ 27 | converged `T_∞` | /own `T_e,SS` at τ27 | /own at ∞ |
|---|---|---|---|---|---|
| FLASH | **3.99** | 646.1 eV | 631.5 ± 5.5 eV | 0.785 | 0.767 |
| WarpX `ic6_long` | **44.33** | 214.3 eV | 381.5 ± 21.5 eV | 0.687 | 1.223 |
| **WarpX/FLASH** | | | | **0.875** | **1.594** |

| `Te_mean_plume` | `τ_relax` | at τ 27 | converged `T_∞` | /own at τ27 | /own at ∞ |
|---|---|---|---|---|---|
| FLASH | **5.54** | 839.0 eV | 817.5 ± 6.2 eV | 1.019 | 0.993 |
| WarpX `ic6_long` | **60.22** | 272.8 eV | 620.0 ± 11.5 eV | 0.874 | 1.988 |
| **WarpX/FLASH** | | | | **0.858** | **2.001** |

### The finding

**At τ = 27 the two codes agree to 12–14 % in similarity units — inside the paper's 20 %
tolerance — and that agreement is worthless as validation.** FLASH is **99.9 %** converged at
τ 27; WarpX is **36–46 %**. WarpX is crossing FLASH's converged value *on its way up*. Run
either code a little longer and the agreement evaporates: extrapolated to convergence the
same comparison reads **1.59×** and **2.00×**.

This inverts the natural reading of the extended run. The slow WarpX approach does **not**
excuse the τ = 27 disagreement — at τ = 27 there barely *is* one. What the extended run
reveals is a disagreement that the τ = 27 snapshot **hid**.

### Why WarpX relaxes 11× slower, and what that is worth

Observed ratio of `τ_relax` (`Te_at_cr`): **44.33/3.99 = 11.1**. Two contributions:

1. **The reduced mass ratio, a factor 4.285.** `v_th,e`/`C_S` = √(μ/Z), so on the ion clock
   τ = `d_i0`/`C_S0` electron transport is √(49542/2698) = **4.285×** slower at μ = 2698 than
   at real mass. A conduction-limited relaxation is stretched by exactly that.
   **This predicts FLASH's `τ_relax` = 44.3/4.285 = 10.3, and FLASH measures 3.99** — so the
   mass ratio is real but accounts for only part of it. Prediction not confirmed; recorded as
   made.
2. **The missing mass reservoir, the residual factor 2.6.** FLASH ablates a thin front off a
   deep solid — its `n_peak` *rises* 795 → **4141 `n_cr`** over the run. `ic6_long` had no
   reservoir at all: `n_peak` fell 10 → 1.14 and the whole slab decompressed. Decision D5
   already held that the overdense interiors are different objects; this shows the difference
   **sets the relaxation time**, not merely the profile.

### The consequence, and the caveat that matters most

**`ic6_long`'s fitted `T_∞` is probably not an ablation steady state at all.** It is the
asymptote of a decompressing slab, fitted over a run in which the target was being consumed
throughout. Quoting "WarpX converges to 2× its own Manheimer steady state" as a physics
result would be over-reading it — Manheimer describes steady ablation, which this run never
performed.

That is what `P4_lez_kin_thick` (set up 2026-08-19, 200 `d_e`, ~2.5 h) is for, and it now
carries a **falsifiable pre-registered prediction**: with a real reservoir, `τ_relax` should
fall from 44.3 toward **3.99 × 4.285 ≈ 17**, and the converged `T_e` should come **down**
toward 1.0 × its own `T_e,SS`. **If it does not — if WarpX still converges to ~2× with a deep
reservoir intact — the disagreement is real physics rather than target design**, and the
prime suspect becomes collisions under a reduced mass ratio (TEST_PLAN 12.8 risk 1).

### Method note
FLASH's `Te_at_cr` (631.5 eV) and its band mean (817.5 eV) differ by 1.29×, and only the band
mean is close to its Manheimer 823. So **the choice of comparator changes the answer** and
must be stated: the tables above compare each statistic to itself across codes, which is the
only defensible form.

---

## 2026-08-19 (Fig. 3) — the paper's Fig. 3 recreated with a WarpX leg, and it agrees far better than raw eV suggested

`scripts/paper_fig3.py` (new) recreates Lezhnin et al. 2025 Fig. 3 — the five-panel
FLASH-vs-PIC profile comparison, (a) `n_e`, (b) `T_e`, (c) `T_i`, (d) `v_z`, (e) laser
deposition — with **`P4_lez_kin_ic6`** standing in for the paper's PSC run, at the paper's own
times **0.2/0.4/0.6/0.8 ns** in red/blue/green/magenta, FLASH solid and WarpX dashed.
Output: `media/P4/P4_lez_kin_ic6/paper_fig3.png` (similarity units) and `paper_fig3_eV.png`
(the paper's absolute axis).

### Three things the figure required getting right

1. **Use `ic6`, not `ic6_long`.** `ic6` dumps particles every **1.348 τ**, and the paper's
   four times land on that grid to **0.002 τ**. `ic6_long` dumps every 5.391 τ, and the 2.696
   clock offset is almost exactly *half* of that — so the paper's grid lands mid-interval and
   `pick` takes the earlier dump every time, biasing **every** WarpX curve **2.695 τ early**.
   The script now anchors on the WarpX dump and pulls FLASH to the same aligned time
   (`--snap`, default on), so a colour pair is genuinely simultaneous.
2. **`T` must be normalised by each code's OWN `T_e,SS`.** Every other axis already is
   (`ζ`/`d_i0`, `v`/`C_S0`, `n_e`/`n_cr`). In raw eV, FLASH's 800 eV against WarpX's 300 eV
   reads as catastrophic disagreement; against 823 and 312 eV respectively it is **0.97 vs
   0.96**. `--tnorm tss` is the default for exactly this reason; `--tnorm none` reproduces the
   paper's absolute axis.
3. **Mask the moments where there is no plasma.** FLASH's delivered `T_i` carries a known
   vacuum artifact reaching **~1.4e5 eV** (`P4_lez_flash/DELIVERY.md`), which autoscaled panel
   (c) into uselessness; a WarpX per-bin moment in the far wing is a handful of
   macroparticles. `--nfloor` (default 1e-3 `n_cr`) blanks both.

### What it shows

- **(b) `T_e` agrees well in the inner plume** — both codes sit at 0.85–1.0 `T_e,SS` out to
  ζ ≈ 15. Beyond that WarpX **rises above 1** while FLASH stays isothermal. That is the
  paper's own reported PSC-vs-FLASH distinction ("the PSC electron temperature profile is
  doubly peaked… one peak near the critical surface and another at the edge of the expanding
  plasma… this contrasts with the isothermal plasma expansion observed in FLASH"), and the
  WarpX leg **reproduces PSC's behaviour, not FLASH's**.
- **(a)** near-corona densities agree; the WarpX plume falls off faster at every time.
- **(c)** WarpX's `T_i` runs hotter than FLASH's, increasingly so late and far out.
- **(d)** `v_z` agrees at 0.2 ns and WarpX is progressively slower after.
- **(e)** on a LOG axis (`--depo-scale`, default) the two profiles track each other closely from the near-critical peak at ζ ≈ 1–3 out to ζ ≈ 10–15, then WarpX falls off **faster** than FLASH — the same steeper plume that panel (a) shows, and consistent with the earlier finding that the kinetic absorption is too concentrated. On a linear axis this panel is all spike and no comparison.

### Also
Added `Ti` to `xcode_compare.warpx_particles` (additive; 391 tests pass, `talk_xcode` still
imports). Panel (e) is only populated because `ic6`'s deposition dumps happen to fall at
τ_own 0/6.7/13.5/20.2 — that cadence is the `profile_intervals`-not-a-multiple-of-
`laser.intervals` bug, which asked for 20 dumps and wrote 4. Fixed in `P4_lez_kin_thick`.

---

## 2026-08-19 (deposition) — deposition split by time: **WarpX's critical surface sits at half FLASH's ζ**, and that is why its absorption is concentrated

`scripts/paper_fig3e.py` (new) plots Fig. 3(e) alone, one stacked panel per time, shared log
axis. Output `media/P4/P4_lez_kin_ic6/paper_fig3e_bytime.png`.

**Times anchor on the WarpX deposition dumps**, not the paper's grid — the deposition profile
is written on `profile_intervals`, which is far coarser than the plotfile cadence, so
anchoring on 0.2/0.4/0.6/0.8 ns leaves panels with no WarpX curve at all. FLASH is pulled to
the same aligned time, giving three simultaneous panels.

| `t_FLASH` | `τ_F`/`τ_W` | `ζ_cr` FLASH | `ζ_cr` WarpX | median `ζ` FLASH | median `ζ` WarpX | ratio | 90 % `ζ` F/W |
|---|---|---|---|---|---|---|---|
| 0.35 ns | 9.4 / 6.7 | 1.33 | **0.78** | 1.89 | 1.40 | 1.35 | 4.87 / 4.05 |
| 0.60 ns | 16.2 / 13.5 | 2.61 | **1.27** | 3.47 | 1.90 | 1.82 | 10.24 / 7.14 |
| 0.85 ns | 22.9 / 20.2 | 3.56 | **1.71** | 5.94 | 3.73 | 1.59 | 17.81 / 11.80 |

### What the split panels show that the combined one could not

1. **Both codes put the deposition peak just outside their own critical surface** — the
   operator is doing the right thing; the peak is not misplaced relative to the physics.
2. **WarpX's critical surface is at roughly HALF FLASH's `ζ` at every time** (0.78/1.33,
   1.27/2.61, 1.71/3.56 — a ratio of 0.59, 0.49, 0.48). The WarpX critical surface simply has
   not moved out as far.
3. **That, and not a defect in the deposition kernel, is what "the absorption is too
   concentrated" means.** The median deposition `ζ` differs by only 1.35–1.82×, and the 90 %
   width by 1.2–1.5× — much less than the concentration ratio quoted earlier from a different
   measure. The deposition column is anchored on the critical surface, so a critical surface
   at half the distance drags the whole profile inward with it.
4. Beyond ζ ≈ 10 FLASH's profile decays much more slowly, matching its shallower density
   profile in Fig. 3(a). WarpX's far tail is macroparticle noise, not structure.

This reframes the deposition discrepancy as a **consequence of the density profile**, i.e. of
where the critical surface sits, rather than an independent problem with the laser operator.

---

## 2026-08-19 (thick) — **the reservoir made it WORSE**: prediction falsified, and the cause is a suppressed ablation rate

`runs/P4/P4_lez_kin_thick` (2h51m) and `P4_lez_kin_thick_off` (2h19m) complete, both
`reached max_step`, `--verify` OK on both, no `.old.` plotfiles. Cost estimate before launch
was 2.0–2.8 h; measured 2h51m, at the top of the range.

### The pre-registered predictions

| # | prediction | outcome |
|---|---|---|
| 3 | `n_peak` stays above 1 `n_cr` | **PASS**, emphatically — see below |
| 1 | `τ_relax` falls from 44.3 toward ~17 | **FALSIFIED** — it *rose* to 108–249 |
| 2 | converged `T_e` falls toward 1.0 × `T_e,SS` | **FALSIFIED** — it *rose* to 2.52 × |

| | `τ_relax` | `T_∞` | /own `T_e,SS` |
|---|---|---|---|
| FLASH | 3.99 | 631.5 eV | 0.767 |
| `ic6_long` (45 `d_e`, no reservoir) | 44.33 | 381.5 eV | 1.223 |
| **`thick` (200 `d_e` reservoir)** | **249 ± 123** (`Te_at_cr`), 108 ± 7 (band) | **787 ± 231 eV** | **2.52** |

`T_e` is still rising at τ 100–180 at 6.8 σ (`Te_at_cr`) and 30 σ (band mean). **Giving the
target a real mass reservoir did not help the leg converge — it made it hotter and slower.**

### It is not a boundary artifact

The obvious suspect is the drive becoming a boundary quantity, and it is excluded. The
deposition median stays pinned at the critical surface for the whole run (`n_e` = 0.42–0.68
`n_cr` at the median, moving 4.3 → 279 `d_e`), and only **0.02 %** of `P_abs` lands beyond
3800 `d_e` of the 4000 `d_e` face. The domain sizing did its job. (`ζ_front` reads NaN after
τ ≈ 135 only because edge `n_e` rises through the band floor, making the band-based
diagnostic undefined — a diagnostic artifact, not a physics one.)

### The mechanism: the ablation rate FELL, and the target COMPRESSED

Measured from the field dumps (`dz` = 0.5 `d_e`, the reliable resolution — the 400-bin
particle diagnostic smears a thin dense target and under-reports its peak):

| | ablation rate of the above-critical reservoir |
|---|---|
| `ic6_long` (45 `d_e`) | 3.00–3.25 `n_cr·d_e` per τ |
| **`thick` (200 `d_e`)** | **2.22 average, decelerating 2.93 (τ 20–90) → 1.82 (τ 90–180)** |

And the target **compresses under the ablation pressure**: peak `n_e` goes 10.0 → **15.04**
`n_cr` at τ 108 before relaxing to 9.35. Only 418 of 2003 `n_cr·d_e` are consumed in 180 τ,
so the reservoir is **79 % intact** — prediction 3 passes with room to spare.

**That is the explanation.** More mass did not buy more ablation; it bought a *denser,
harder-to-ablate* target. The ablation rate is set by how fast heat reaches the ablation
front, so compressing the target lengthens and steepens the conduction path, the mass flux
falls, less enthalpy is carried away, and the absorbed power goes into heating the corona
that is already there. `T_e` overshoots Manheimer and keeps climbing.

### What this implicates

**Electron thermal conduction under the reduced mass ratio.** On the ion clock, electron
transport is √(μ_real/μ_sim) = **4.285×** slower at μ = 2698 than at real mass — so a
conduction-limited ablation rate is suppressed by that factor, exactly the direction needed.
This is the paper's **Appendix C** (conductivity), which the D3 collision gate explicitly
never covered (RESULTS 2026-08-18). It is now the leading candidate for the whole Phase-4
temperature discrepancy, and it is *not* a laser-operator problem.

### Gates

- **G3 PASSES decisively.** Control electrons **cool** by 1.6995e5 J against the driven run's
  gain of +1.7387e7 J: ratio **−0.0098**. No grid heating, at 1.667× the steps and 1.68× the
  cells of `ic6`, which is what the control was run to bound.
- **G6 closure 0.9305** (against `ic6_long`'s 0.876), with **0.36 %** weight loss (0.89 %) —
  quoted together as the gate requires. The bigger box retains more, which is *why* the
  closure improved.
- Ion energy share settles at **0.37** of the total from τ ≈ 50 and stays flat.

### One thing that did improve, and it matters

At τ = 27, the thick leg's absorbed fraction is **0.872 against FLASH's 0.870** — essentially
exact, where `ic6` managed 0.478. Its plume `T_e` is then **0.822 ×** what its own absorbed
flux supports, i.e. the leg is *under-converged at τ 27* rather than mis-driven. So the
absorption physics is right; the transport is what is not.

### Media
`media/P4/P4_lez_kin_thick/{movie_fields,movie_phase}.mp4`; `media/xcode/{profiles,profiles_reduced,history}.png`
regenerated with the thick leg. `paper_fig3` is NOT generated for this run: its 8.99 τ dump
spacing is too coarse for the paper's 0–19 τ window (two of the four times snap to one dump).
`P4_lez_kin_ic6` remains the paper-comparison leg.

---

## 2026-08-19 (PSC preliminary) — the WarpX discrepancy is **electron–ion over-equilibration**, not the laser, not the IC

`~/psc-raytrace/run_ourflash` at 11 % (through FLASH `t` = 0.20 ns). PSC runs the **same
reduced mass ratio** as the WarpX legs (`m_p/m_e` = 100 ⇒ `m_Al/m_e` = 2698) and the **same
IB kernel**, so it isolates what is WarpX-specific. Preliminary, but the three comparisons
below are already decisive.

### 1. The laser deposition modules are the same function

Operator-level cross-validation was completed 2026-08-03: PSC's `get_lnlambda` vs our `nrl`
agree to **0.000e+00** over 1681 points, the IB coefficient to **6.7e-16**, and compiled
WarpX C++ vs PSC to **8e-9**. What differs is how it is *applied*:

| | WarpX `ic6` | PSC |
|---|---|---|
| Coulomb log | **constant 6.3** | **per-cell, ≈5.10** measured at the critical surface |
| application cadence | every **10** steps | every **1** step |
| turning point | marched at `ray_cfl` = 0.25 | analytic closed form (and it needed the NaN guard, this session) |
| collisions | every 10 steps | every 10 steps — **matched** |

lnΛ 6.3 vs 5.1 makes WarpX's coefficient **1.23×** larger per unit path. Yet measured `f_abs`
is similar (WarpX 0.478 at τ 27; PSC 0.47–0.56) and **both sit near half of FLASH's 0.870**.
So the absorbed fraction is a shared PIC-vs-FLASH gap, not a PSC-vs-WarpX one.
*Caveat*: PSC's `f_abs` diagnostic is documented valid only for **sub-critical** profiles, and
this target is overdense — so PSC's absorbed fraction is not yet quotable.

### 2. The initial conditions are equivalent — this is ruled out

Measured at the handoff (FLASH `t` = 0.1 ns), each code as it actually starts:

| | `ζ_cr` | `ζ_front` | `L_n` | `T_e` plume |
|---|---|---|---|---|
| FLASH (truth) | 0.273 | 3.430 | 0.716 | 378.3 eV |
| PSC (interpolated FLASH) | 1.016× | 1.307× | 1.107× | 0.981× |
| WarpX `ic6` (4-parameter analytic fit) | 1.123× | 1.011× | 0.971× | 1.002× |

On the underdense ramp *where the laser is absorbed* the profiles agree to a few percent
(at ζ = 2: FLASH 0.0926, PSC 0.0894, WarpX 0.0892 `n_cr`). **The analytic fit is as good a
starting point as the interpolated profile.**

### 3. Where it actually diverges: temperature, not hydrodynamics

All three codes at the **same absolute time**:

| t | code | `ζ_front` | `L_n` | `T_e` plume |
|---|---|---|---|---|
| 0.15 ns | FLASH | 5.91 | 1.35 | **472 eV** |
| | PSC | 1.28× | 1.21× | **0.96×** |
| | WarpX | 1.09× | 1.15× | **0.32×** |
| 0.20 ns | FLASH | 10.85 | 2.40 | **559 eV** |
| | PSC | 0.98× | 1.05× | **0.92×** |
| | WarpX | 0.88× | 0.99× | **0.22×** |

**WarpX's density structure tracks FLASH as well as PSC's does. Only its temperature is
wrong.**

### The mechanism: WarpX equilibrates `T_e` and `T_i` within one ion response time

The `T_i` moment was validated against the config's own IC (measured 116.3 eV vs
`theta_i_init` = 115.6 eV; `T_e` 377.2 vs 378.3).

| τ_own | `T_e` | `T_i` | `T_i/T_e` |
|---|---|---|---|
| 0.00 | 377.2 | 116.3 | **0.308** — matches FLASH's 0.293 |
| 1.35 | 131.8 | 160.2 | **1.216** |
| 2.70 | 119.3 | 143.0 | 1.198 |
| 5.39 | 123.4 | 144.7 | 1.172 |

FLASH holds `T_i/T_e` = 0.29–0.33 for its whole run. **WarpX destroys the `T_e ≫ T_i` state —
the paper's headline result — inside one τ.** Total electron energy is *not* lost (it grows
3.6× by τ 27), so this is an **energy-partition** failure, not an absorption failure: the
absorbed energy is thermalised into the ions instead of staying in the electrons.

That also explains why the hydrodynamics survives: equilibration redistributes energy between
species without immediately changing the total pressure driving the expansion, so `ζ_front`
and `L_n` stay close to FLASH while `T_e` collapses.

### Two hypotheses tested and DISCARDED

- **Diagnostic binning.** `warpx_particles` bins 400 cells over 2500 `d_e` (6.25 `d_e`/bin)
  against a corona scale length of 6.955 `d_e`. Refining to 12500 bins (0.20 `d_e`, matching
  PSC's grid) moved `T_e` at τ 2.7 from 121.5 → **110.4 eV** — *down*, not up. The 4× deficit
  is physical, not an artifact.
- **The reduced mass ratio.** PSC runs the identical ratio and does *not* show the collapse.
  This **undercuts the conduction hypothesis** from the thick-target entry above, which
  attributed the WarpX overshoot to 4.285×-slower electron transport on the ion clock. Same
  ratio, different answer ⇒ the ratio is not sufficient.

### Where this points
WarpX's Coulomb collision operator (`type: coulomb`, Perez et al. 2012 with the `σ_max` cap,
`intervals: 10`, global lnΛ = 6.3). Note PSC rescales its collision frequency explicitly for
the reduced parameters (`nudt0 *= ReducedSoL² (511000/temp_phys)²`); WarpX has no equivalent
rescaling. **The D3 gate passed e–i thermalisation against Lezhnin Eq. (B1) — which is itself
an equilibration formula — so "matches B1" and "over-equilibrates relative to PSC/FLASH" can
both be true, and that tension is now the thing to resolve.**

### Not yet quotable
PSC's `T_i` normalisation (my read gives 7200–8000 eV, ~16× `T_e`, certainly a missing mass
factor in my reader). PSC's `f_abs` at an overdense target. Both need fixing before the
finished run is analysed.

---

## 2026-08-19 (collision cadence) — supercycling is NOT the cause; the operator's RATE is

`runs/P4/P4_lez_kin_ic6_coll1` — `P4_lez_kin_ic6` with `collisions.intervals` 10 → 1 and
**nothing else changed** (`laser.intervals` stays 10; deck diff is `max_step` and the three
`ndt_supercycle` lines only). 110592 steps, 14 min, `--verify` OK. `P4_lez_kin_ic6` is the
matched control and its dumps already land on the comparison times.

| τ_own | `T_e` ndt=10 → ndt=1 | `T_i/T_e` ndt=10 → ndt=1 | FLASH `T_e` | PSC `T_e` |
|---|---|---|---|---|
| 0.00 | 377.2 → 377.2 | 0.308 → 0.308 | 378.3 | 371.3 |
| 1.35 | 131.8 → **126.7** | 1.216 → **1.069** | 472.4 | 454.7 |
| 2.70 | 119.3 → **106.5** | 1.198 → **1.089** | 559.3 | 516.0 |
| 5.39 | 123.4 → **121.2** | 1.172 → **1.173** | 646.3 | 562.9 |

**Falsified.** Collisions every step give a small, transient improvement in `T_i/T_e` that has
**completely vanished by τ 5.39**, and `T_e` ends *lower*, not higher — the correct direction
for more equilibration but nowhere near enough. WarpX still runs at **0.19 × FLASH** where PSC
runs at 0.87.

**What this clears and what it leaves.** The cadence is no longer a suspect: the
over-equilibration is set by the collision operator's *rate*, not its application frequency.
Remaining differences between the two codes' collision setups (RESULTS same date, above):

1. **WarpX has no reduced-parameter correction of any kind**, where PSC applies two explicit
   ones — an overall `(511/60)²` = 72.5× for its reduced speed of light, and
   `√(1836.15/ReducedMassRatio)` = **4.285×** on ion–ion for the reduced mass ratio.
2. **Different regimes**: PSC's own counters put **78 %** of its collisions in the large-angle
   branch here, while WarpX's Perez `σ_max` cap engages on ~1.7 % of the production plume.
3. **Species treatment**: WarpX runs three separately-configured pairwise operators; PSC pairs
   all particles in a cell without separating by species.
4. lnΛ runs the *wrong way* to explain anything — PSC's collision value ≈8.28 exceeds WarpX's
   6.3 by 31 %, so PSC should equilibrate faster, and does not.

The Perez `σ_max` cap (D3's "1.5 capped point") is now the leading suspect, followed by the
absence of a mass-ratio correction.

**Cost**: 0.0076 s/step vs the control's 0.0023 — **3.3×** for `intervals: 1`, well above the
~1.15× that D3's "10–15 % at `ndt` = 10" would suggest.

---

## 2026-08-19 (root cause) — it is **absorption**, not collisions: `Tlocalfrac` ≈ 0 and WarpX absorbs 3–6× too little

`runs/P4/P4_lez_kin_ic6_nocoll` — `ic6` with `collisions.enabled: false`, deck differing from
`ic6_coll1` by **exactly the removed collision block**. 3 min, `--verify` OK, zero
`pairwisecoulomb` entries in `warpx_used_inputs`.

### The σ_max cap, cleared without a rebuild

Two independent arguments: (i) `sigma_eff = min(π b0² lnΛ, σ_max)` can only **reduce** `s12`,
so removing the cap makes equilibration *faster* — the wrong direction; (ii) on **e–i**, the
channel governing `T_e`↔`T_i`, `(π b0² lnΛ)/σ_max` = **0.055 / 0.255 / 1.18** at
n = 0.01 / 0.1 / 1 `n_cr` (120 eV) — essentially inactive across the plume band. It *is*
strongly active on **i–i** (3–680), but i–i moves no energy between species.

### Collisions off: three-quarters of the gap survives

| τ_own | ndt=10 | ndt=1 | **OFF** | FLASH | PSC |
|---|---|---|---|---|---|
| 2.70 `T_e` | 119.3 | 106.5 | **176.7** | 559.3 | 516.0 |
| 2.70 `T_i/T_e` | 1.198 | 1.089 | **0.468** | 0.325 | — |
| 5.39 `T_e` | 123.4 | 121.2 | **162.5** | 646.3 | 562.9 |

Collisions drive the `T_i/T_e` inversion, but `T_e` recovers only 0.19× → **0.25×** FLASH.

### The root cause: `f_abs`

| τ_own | WarpX `ic6` | PSC | FLASH |
|---|---|---|---|
| 0.50 | **0.153** | 0.47 | 0.870 |
| 2.70 | **0.218** | 0.56 | 0.870 |
| 5.39 | **0.322** | ~0.5 | 0.870 |

**WarpX absorbs 3× less than PSC and 4–6× less than FLASH** on the same IC with a kernel
cross-validated to 8e-9. Its electrons therefore cool (377 → 177 eV even with collisions off)
where FLASH's heat (378 → 559 eV) — expansion beats the drive.

**Leading candidate: `Tlocalfrac` ≈ 0.0000 for the entire run.** `temperature_mode: local`
never delivers a measured per-cell `T_e`, so the IB coefficient uses the **fallback**
`electron_temperature` = 378.3 eV rather than the ~120 eV plume. `K ∝ T^(-3/2)` makes that a
**5.6×** under-estimate — the size of the deficit. Gate G5 says "Watch `Tlocalfrac`"; it was
not watched. Note the sign is the *opposite* of G5's stated worry (it warns per-cell noise
biases absorption HIGH; here the fallback biases it LOW).

**Confirmation still needed**: `temperature_mode: constant` at ~130 eV should raise `f_abs`
~5×; and/or raise ppc until `Tlocalfrac` is O(1).

### RETRACTED
**The collision hypothesis.** RESULTS 2026-08-19 (PSC preliminary) said "the WarpX discrepancy
is electron–ion over-equilibration". **Demoted**: real and collision-driven, but only ~25 % of
the `T_e` gap. Cadence and `σ_max` are cleared; absorption is the primary cause.

---

## 2026-08-19 (floor) — the temperature floor confirmed: `f_abs` doubles, but only ~⅓ of the `T_e` gap closes

Two single-variable runs against the `P4_lez_kin_ic6` control, on identical dump times.

**Source finding first.** `LaserDeposition.cpp:703` sets `m_theta_floor = m_theta_e` — the
floor **defaults to `electron_temperature`** — and the gate at :1017 accepts a measured
per-cell temperature **only if `kT > kT_floor`**. With `electron_temperature` = `th_t` =
378.3 eV and a ~120 eV plume, the measurement is never accepted: `Tlocalfrac` = 0 and `K` is
evaluated at 378.3 eV everywhere.

| τ_own | control `f_abs`/`Tloc` | **A: floor 20 eV** | **B: ppc 2000** |
|---|---|---|---|
| 0.50 | 0.142 / 0.000 | **0.308 / 0.233** | 0.126 / **0.000** |
| 2.70 | 0.217 / 0.000 | **0.545 / 0.394** | 0.187 / **0.000** |
| 5.39 | 0.319 / 0.000 | **0.634 / 0.667** | 0.268 / **0.000** |

- **A confirms the diagnosis.** `Tlocalfrac` activates at step 0 (0.001 → 0.43); `f_abs`
  doubles into PSC's 0.47–0.56 band; `E_abs` to τ 5.39 rises **2.2×** (2.38e5 → 5.26e5 J).
- **B is the null that makes A interpretable.** At **4× the particles** `Tlocalfrac` is still
  **0.000** and `f_abs` is unchanged. The blocker is the floor, not statistics
  (`min_macroparticles_per_cell` defaults to 4, trivially met at 500 ppc).

### But it does not close the gap

| τ_own | `T_e`/FLASH: control | nocoll | **floor 20 eV** | ppc 2000 | PSC |
|---|---|---|---|---|---|
| 2.70 | 0.213 | 0.316 | **0.330** | 0.238 | 0.923 |
| 5.39 | 0.191 | 0.251 | **0.308** | 0.223 | 0.871 |

Doubling the absorbed energy buys ~+55 % of `T_e`, from 0.19–0.21× to **0.31–0.33×** FLASH.
WarpX remains **~3× below** FLASH and PSC. Removing collisions entirely buys a similar +50 %.
Neither effect, nor plausibly both together, accounts for a 4–5× deficit.

### Standing conclusion
Two **real, confirmed defects** are now on the record — a temperature floor that halves the
absorbed energy, and a collisional `T_i/T_e` inversion absent from FLASH and PSC — and
**together they explain roughly half the discrepancy**. The remainder is still open. Note
`Vskip` = 0.9466 at t = 0 (the ray march skips 95 % of the domain as empty) is the next thing
I would look at, since it bounds where absorption can occur at all.

### Recommendation for production decks
Set `laser.temperature_floor_theta` explicitly and well below the expected plume temperature.
Leaving it to default to `electron_temperature` silently pins the IB coefficient to the
initial temperature for the whole run. Gate G5's "watch `Tlocalfrac`" should become a hard
check: `Tlocalfrac` ≈ 0 in `local` mode means the mode is not doing anything.

---

## 2026-08-20 — PSC-equivalent heating: **the deposition operator is exonerated**

`runs/P4/P4_lez_kin_ic6_pscheat`. Three config knobs, **no code change**, chosen to remove
every difference between WarpX's and PSC's laser heating:

| knob | control | this run | PSC |
|---|---|---|---|
| `temperature_floor_theta` | default = `electron_temperature` = **378.3 eV** | **1 eV** | none |
| `min_macroparticles_per_cell` | default **4** | **1** | `NNe /= 0` |
| `coulomb_log_mode` | constant **6.3** | **`nrl`** (per cell) | per cell |

(The floor is 1 eV rather than 0 because the operator asserts > 0; at 1 eV it never binds on
a ≥100 eV plume. `nrl` is the documented "what would PSC have done here" mode — it reproduces
PSC's `get_lnlambda` to 0.000e+00 over 1681 points.)

| τ_own | | control | floor only | **PSC-equiv** | PSC | FLASH |
|---|---|---|---|---|---|---|
| 2.70 | `f_abs` | 0.217 | 0.545 | **0.423** | 0.47–0.56 | 0.870 |
| 5.39 | `f_abs` | 0.319 | 0.634 | **0.461** | 0.47–0.56 | 0.870 |
| — | `Tlocalfrac` | 0.000 | 0.23–0.67 | **1.000** | — | — |
| 2.70 | `T_e`/FLASH | 0.213 | 0.330 | **0.290** | 0.923 | 1.000 |

**`Tlocalfrac` reaches 1.000 and `f_abs` reaches PSC's band — and `T_e` does not move.**

### The finding
**At the same absorbed fraction, WarpX produces ~3× less plume electron temperature than
PSC.** Absorption is no longer the discriminator. Combined with the earlier eliminations —
collision cadence (refuted), Perez `σ_max` cap (inactive on e–i and wrong-signed), collisions
entirely off (only ~25 % of the gap), temperature floor (real, ~⅓ of the gap) — **the laser
deposition operator is cleared**. The residual is downstream of absorption.

### Where to look next
The one measured asymmetry consistent with "absorption matches, temperature does not" is
**where** the energy lands: WarpX's median deposition ζ is **1.35–1.82× smaller** than FLASH's
(RESULTS 2026-08-19, deposition), i.e. into **denser** plasma. The same joules spread over more
mass give a smaller temperature rise. That is the next thing to measure directly.

### Caveat
`lnLmean` reads **1.01** in this run — the NRL expression floors at 1 in most cells — where
PSC's laser module gave **≈5.10** at the critical surface. Domain-mean vs point value are not
directly comparable, but the coefficient match is **not** established. The conclusion does not
depend on it: it rests on `f_abs` being matched while `T_e` is not.

---

## 2026-08-20 (deposition) — **where the energy lands is NOT the discriminator**; the partition is

Direct measurement, `P4_lez_kin_ic6_pscheat` re-run with `profile_intervals` = 22120 (divisible
by `laser.intervals` = 10, so the dumps actually fire — the same LCM trap as `ic6_long`).
5 deposition profiles, τ_own 0 → 4.31. Physics unchanged; `--verify` OK.

### The hypothesis, and its refutation

RESULTS 2026-08-19 (deposition) found WarpX's median deposition ζ **1.35–1.82× smaller** than
FLASH's, and I proposed the energy was landing in **denser** plasma — same joules over more
mass, so a smaller temperature rise. **Measured, that is wrong.**

| τ_own | `⟨n_e⟩_dep` WarpX | `⟨n_e⟩_dep` FLASH | median ζ ratio |
|---|---|---|---|
| 0.00 | 0.707 | 0.707 | 1.13 |
| 1.08 | 0.634 | 0.547 | 1.52 |
| 2.16 | 0.738 | 0.644 | 2.01 |
| 3.24 | **0.485** | 0.654 | 1.38 |
| 4.31 | **0.488** | 0.666 | 1.26 |

Both codes deposit at `n_e` ≈ **0.5–0.7 `n_cr`** — at the critical surface, as they should —
and **late in the run WarpX deposits into *less* dense plasma than FLASH**, the opposite of
the hypothesis. The profiles overlay across four decades
(`media/P4/P4_lez_kin_ic6_pscheat/paper_fig3e_bytime.png`) and the median-ζ ratio *converges*
1.52 → 1.26 once the heating is PSC-equivalent. The earlier 1.35–1.82× was measured on the
un-fixed `ic6`, where the temperature floor was distorting the coefficient.

### What the energy actually does

The laser deposits into **electrons only** (`laser_deposition.species = targ_electrons`), so
every joule in the ion column arrived there from the electrons. At τ_own 5.39:

| run | `E_abs` | `ΔE_e` | `ΔE_i` | electron share |
|---|---|---|---|---|
| control | 2.380e5 | **−1.443e4** | +1.941e5 | **−0.08** |
| **no collisions** | 1.563e5 | +2.402e4 | +1.261e5 | **0.16** |
| floor 20 eV | 5.257e5 | +1.620e5 | +2.711e5 | 0.37 |
| PSC-equiv | 4.367e5 | +8.657e4 | +2.429e5 | 0.26 |

**Ions take 74 % of the absorbed energy — and 84 % with collisions switched entirely off.**
So the electron→ion transfer is **not collisional**: it is the ambipolar field doing work on
the ions, i.e. the absorbed energy is promptly converted into plume *directed* motion instead
of staying as electron heat. In the production control the electrons **net lose** energy.

### The plume band, for scale
At τ_own 5.39 the 1e-2…1 `n_cr` band holds `N` = 3.18e21 electrons/m² in WarpX against
**2.38e22 in FLASH** (7.5× fewer), each at **188 eV against 653 eV** (3.5× cooler). FLASH's
band *count* grows 6.4× over the window as its target ablates into it; WarpX's grows 2.8×.

### Standing eliminations
Initial conditions (equivalent), laser kernel (cross-validated 8e-9), collision cadence
(refuted), Perez `σ_max` cap (inactive on e–i, wrong-signed), collisions entirely (~25 % of the
gap), temperature floor (real, ~⅓ of the gap), full PSC-equivalent heating (`f_abs` matched,
`T_e` unmoved), and now **deposition location**. What remains is the **energy partition**:
WarpX converts absorbed energy into ion motion where FLASH holds `T_i/T_e` = 0.33 and PSC
keeps `T_e` at 0.92× FLASH on the *same* absorbed fraction.

### The gap in the evidence
PSC's energy partition is **not** measured — my PSC `T_i` normalisation is still wrong (it
reads ~16× `T_e`, a missing mass factor). Fixing it is now the single most valuable next step,
because PSC absorbing what WarpX absorbs while staying hot is the whole remaining puzzle.

---

## 2026-08-20 (partition) — **PSC keeps ⅔ of the energy in electrons; WarpX gives ¾ to ions**

The missing measurement is in. I did **not** fix the PSC `T_i` normalisation — I found a better
route: PSC's moment dump already carries `KEe` and `KEi`, the per-species kinetic energy
densities, so the partition is read directly and no temperature convention is needed.

### Why the `T_i` route was abandoned (recorded, since I chased it first)
Calibrating the read-back against the IC files I supplied: `T_e` returns at **0.983×** the
input (the electron formula is right) and `n_e`/`n_i` = **13.000** exactly (so `NNi` is the
true ion density) — but `T_i` returns at **45×**. Per cell that factor is not constant at all:
it spans **1.02 → 906**, spread p75/p25 = 8.6, and correlates with local density at
**−0.84**. So `Sxxi+Syyi+Szzi` is an **uncentered** second moment — it contains the bulk flow,
not just the thermal spread — and PSC loads ions at `NNpart`/Z per cell, i.e. **77 per cell at
`n_cr` and <1 per cell at 1e-2 `n_cr`**, so the outer plume is badly sampled. There is no
single factor to divide out, which is why the earlier "7200 eV" was meaningless.

### The partition, from PSC's own `KEe`/`KEi`

| `t_FLASH` | PSC electron share of the **gain** |
|---|---|
| 0.109 ns | 0.682 |
| 0.145 ns | 0.693 |
| 0.200 ns | 0.677 |
| 0.264 ns | 0.653 |

Steady at **0.65–0.69**. Against WarpX at τ_own 5.39:

| code / configuration | electron share of the energy gain |
|---|---|
| **PSC** | **0.65–0.69** |
| WarpX, PSC-equivalent heating | **0.26** |
| WarpX, production control | **−0.08** (electrons net LOSE) |
| WarpX, collisions OFF | **0.16** |

**The partition is inverted.** PSC retains about two-thirds of the absorbed energy in the
electrons; WarpX delivers about three-quarters of it to the ions. That is the whole remaining
discrepancy, and it explains why PSC reaches `T_e` = 0.92× FLASH while absorbing no more than
WarpX does.

### What it is not
Not collisional — WarpX gives ions **84 %** with collisions switched entirely off, *more* than
with them on. The transfer is the **ambipolar field doing work on the ions**, i.e. absorbed
energy going into plume directed motion rather than electron heat. Not the deposition location
either: both codes deposit at `n_e` ≈ 0.5–0.7 `n_cr` (2026-08-20, deposition).

### Where that leaves the investigation
Eliminated: initial conditions, laser kernel, collision cadence, `σ_max` cap, collisions
entirely, temperature floor, PSC-equivalent heating, deposition location. **Surviving
candidate: the electron→ion energy transfer through the self-consistent field.** The one
first-order setup difference not yet tested is the **reduced speed of light** — PSC runs
`m_e c²` = 60 keV, WarpX the full 511 keV — which changes the electron thermal speed relative
to `c` and hence the sheath/ambipolar dynamics. WarpX cannot reduce `c`, so testing this needs
either a PSC run at `m_e c²` = 511 keV or an analytic estimate of the ambipolar partition's
dependence on it.

---

## 2026-08-20 (hybrid) — the hybrid does **not** have the floor bug, and it partitions energy like PSC. The defect is specific to WarpX's **kinetic electrons**

Checked `P4_lez_hyb_bg3` against every defect found in the kinetic legs.

### 1. Temperature floor — NOT present
`Tlocalfrac` = **0.994–1.000** for the whole run, against 0.000 in the kinetic legs. Two
reasons: `temperature_mode = hybrid_fluid` takes `T_e` from the Ohm's-law field, which is
defined in every cell without particle statistics; and its floor is `electron_temperature` =
1.957e-4 = **100 eV**, below its ~400 eV plume, so it never binds. The kinetic legs inherited
a 378.3 eV floor against a ~120 eV plume.

### 2. Absorbed fraction — same deficit
`f_abs` 0.169 (τ 2.7) → 0.450 (τ 27), against FLASH's 0.870. So even with a **correctly
functioning local temperature**, a WarpX-family run absorbs about half of FLASH — the same
level as the floor-fixed kinetic runs (0.42–0.46) and PSC (0.47–0.56). This cleanly separates
the two defects: the floor bug is *not* what makes WarpX absorb less than FLASH.

### 3. Energy partition — the hybrid behaves like PSC

**Correction to RESULTS 2026-08-20 (partition):** that entry compared WarpX at τ_own 5.39
against PSC over τ_own 0.4–4.3 — **mismatched times**, which understated the gap. Time-matched,
electron share of the energy gain:

| τ_own | kin control | kin PSC-equiv | kin no-coll | **hybrid** | PSC |
|---|---|---|---|---|---|
| 0.50 | **−3.49** | −1.55 | −0.23 | **0.979** | 0.65–0.69 |
| 1.35 | **−2.23** | −0.74 | −0.28 | **0.923** | " |
| 2.70 | **−0.99** | −0.10 | −0.13 | **0.857** | " |
| 4.04 | −0.37 | 0.15 | −0.01 | **0.780** | " |
| 5.39 | −0.08 | 0.31 | 0.16 | **0.701** | " |

A negative share means the electrons **lose energy in absolute terms** while the ions gain —
at τ 0.5 the control's electrons shed 78 % of what its ions take up, *while the laser is
heating them*.

**The hybrid, with fluid electrons, tracks PSC. The kinetic legs, with PIC electrons, do the
opposite.** Same laser operator, same target, same mass ratio, same collision settings.

### What this points at, and a reinterpretation
The defect is specific to **WarpX's kinetic electrons draining energy into ions**. Note this
was already visible and was read the other way: RESULTS 2026-08-19 (G3) recorded that
`P4_lez_kin_ic6_off` — **laser off** — has its electrons **cool by 35 %**, with the loss
appearing in the ions (−1.7936e5 J against +1.9436e5 J, closing to 8 %). That was logged as
evidence of *no grid heating*, which it is. But in the light of PSC and the hybrid it is also
evidence of an **electron energy sink that operates with no laser at all**, and the ambipolar
drain outrunning the laser resupply is exactly what the numbers above show.

With PSC-equivalent heating the resupply is matched to PSC (`f_abs` 0.42–0.46 vs 0.47–0.56)
and the electrons *still* lose, so it is the **drain**, not the supply.

### Consequence for the running test
This makes the 511 keV PSC run (`run_ourflash_511keV`, launched 2026-08-20) more pointed, not
less: PSC and WarpX differ in the electron push mainly through the **reduced speed of light**
(60 keV vs 511 keV), and that run measures whether PSC's partition survives at full `c`.

---

## 2026-08-20 (511 keV) — the reduced speed of light is NOT the cause. **The defect is WarpX's kinetic electron treatment**

`runs` → `~/psc-raytrace/run_ourflash_511keV`. PSC rebuilt with `ReducedSoL` = 3000/511000, i.e.
`m_e c²` = **511 keV, full `c`**, against the paper's 60 keV. 64 000 steps, t_FLASH 0.1 → 0.1996 ns,
**1 h 45 m**, zero NaN. Verified at runtime: `K_temperature` = 511000.000, `K_time` = 1.0381e-14 s,
`dt` = 1.557 fs — all matching prediction. ICs regenerated into `ic_ourflash_511keV/` because
`K_temperature` *is* `m_e c²`; reusing the 60 keV files would have loaded the plasma 8.5× too hot.

### Result

| t_FLASH | PSC 60 keV | **PSC 511 keV** |
|---|---|---|
| 0.110 | 0.682 | **0.656** |
| 0.130 | 0.686 | **0.671** |
| 0.150 | 0.692 | **0.616** |
| 0.170 | 0.688 | **0.616** |
| 0.190 | 0.681 | **0.660** |

**PSC keeps ~⅔ of the absorbed energy in its electrons at full `c` just as at 60 keV.** The
change is ~5 %, against the factor needed to explain WarpX. And because PSC ties collision
strength to `ReducedSoL`, this run also weakened collisions by **72.5×** — so the partition is
insensitive to the speed of light *and* to collisionality, two variables at once.

### The investigation, closed to one candidate

Electron share of the energy gain, time-matched (τ_own 0.5 → 5.4):

| code | electron share |
|---|---|
| PSC, 60 keV | 0.68 → 0.68 |
| PSC, 511 keV | 0.66 → 0.62 |
| **WarpX hybrid (fluid electrons)** | **0.98 → 0.70** |
| **WarpX kinetic (PIC electrons)** | **−3.49 → −0.08** |

Everything else has been eliminated by measurement: initial conditions (equivalent on the
absorbing ramp), the laser kernel (cross-validated 8e-9), collision cadence (refuted), the
Perez `σ_max` cap (inactive on e–i and wrong-signed), collisions entirely (only ~25 % of the
gap), the temperature floor (real, ~⅓ of the gap, now fixed), PSC-equivalent heating (`f_abs`
matched, `T_e` unmoved), deposition location (same density, 0.5–0.7 `n_cr` in both), and now
the reduced speed of light.

**What survives: WarpX's kinetic electrons drain energy into the ions in a way PSC's kinetic
electrons and WarpX's own fluid electrons do not.** The same operator, target, mass ratio and
collision settings produce opposite partitions depending only on whether WarpX's electrons are
particles or a fluid. That localises the defect to the **electron push / field solve**, not to
any of the physics modules.

### The clearest single piece of evidence
`P4_lez_kin_ic6_off` — **laser off** — loses 35 % of its electron energy to the ions
(−1.7936e5 J against +1.9436e5 J). There is no laser, no absorption and no temperature floor
in play; the drain runs on its own. That run is the cheapest reproducer for anyone taking this
upstream.

---

## 2026-08-20 (Debye) — PRELIMINARY: resolution is **cleared**. The electron drain is converged in `dz`

`runs/P4/P4_lez_kin_off_dz125` at 81 % (τ_own 4.54 of 5.39). Laser OFF, so no absorption, no
temperature floor, no collisional heating — the cleanest reproducer of the drain. Deck differs
from `P4_lez_kin_ic6_off` in `dz_over_de` (0.5 → 0.125), the step count for the same physical
time, and a domain truncation that removes only empty cells (the laser-off plume reaches
158 `d_e` by τ 5.4 and the corona has no particles beyond ~82 `d_e` at t = 0).

| τ_own | control `dz`=0.5 | **`dz`=0.125** | ratio | `E_i/E_i0` ctrl / fine |
|---|---|---|---|---|
| 0.50 | 0.887 | 0.864 | 0.974 | 1.466 / 1.555 |
| 1.35 | 0.795 | 0.801 | 1.009 | 1.725 / 1.862 |
| 2.70 | 0.739 | 0.757 | 1.025 | 1.843 / 2.083 |
| 4.04 | 0.722 | 0.731 | 1.013 | 1.925 / 2.218 |

**A 4× refinement — `dz/λ_D` from 29.2 to 7.3, i.e. from 3.6× over gate G2's budget to inside
it — moves the electron energy loss by 1–2.5 %.** The drain is ~27 % at both. The ions gain
*more* at the finer resolution, the opposite of a numerical artifact being cured.

**Outcome 2, as pre-registered.** Debye under-resolution is not the cause. This was the
prediction recorded in the run's README before launching, on the strength of the 511 keV PSC
run (2.92× resolution change, 5 % partition change).

### What this leaves
The electron→ion transfer in WarpX's kinetic electrons is **converged in spatial resolution**.
Combined with everything already eliminated, that points at either (a) genuinely correct
ambipolar physics that PSC and the WarpX hybrid both suppress, or (b) something in the electron
push / current deposition that does not improve with `dz`.

### The missing control, and it is cheap
**PSC has never been run with the laser off.** A free expansion converting electron thermal
energy into ion directed energy is real physics; the question is whether PSC's free expansion
does it at the same rate. That is the like-for-like test and it costs PSC nothing extra (no ray
march). Until it exists, "WarpX drains and PSC does not" rests on runs where PSC also had a
laser resupplying its electrons.

### Operational note
The first launch of this run **died on GPU out-of-memory** — another user took 9.5 GB on each
card in the ~1 minute between my pre-flight check (both GPUs free) and the launch. Checking
`nvidia-smi` is necessary but not sufficient on a shared box; `scripts/queue_run.sh` exists to
wait for capacity and should be used.
