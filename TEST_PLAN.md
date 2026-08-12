# TEST_PLAN.md — Testing the WarpX ray-tracing laser-deposition module as a shock driver

**Project.** `LaserProdShock` — a systematic test campaign for the WarpX
`LaserDeposition` operator (`warpx-cda/Source/Particles/LaserDeposition/`) used as a
**shock driver**: an actual ray-traced laser ablating a target, replacing the prescribed
`ParticleHeater` + `TargetInjector` piston surrogate that `KinShock2020` used to replicate
Schaeffer et al. 2020.

**Status.** The 2D operator bug of §2.7 is **FIXED upstream** (2026-07-29, `warpx-cda` c817b63)
and verified on the shipped CI decks — see §2.8. **Phase 1's 2D path is unblocked, but its two 2D
runs remain invalid**: `P1_vac_2d` / `P1_vac_2d_off` were produced by the buggy operator and must
be re-run before any 2D claim. Phase 1 in **1D** is complete and its findings (§2.4–2.6) already overturn H2 and H3's
thickness clause. **Phase 0 is complete** (2026-07-28): tooling built, all five boundary runs
done, and the boundary decision recorded (`open` on the propagation axis + periodic
transverse; B₀ uniform to 1.000000 under pec).
**2026-07-29, `P1_vac_2d_spot` (§7.2.1): the operator is validated in 2D and H5 is still
untested.** Step 0 is exact on a *spatial* measure (per-column ratio 1.00010, total within
2.2×10⁻⁵ of `I₀w₀√π`) and c817b63 holds on all 10 dumps — but the run **loses transverse
isolation after 1.99 ps**, because its box was sized from `c_s` where `v_th,e` = 10 `c_s` governs.
A valid H5 spot run needs a **4.9× wider** transverse box, which makes Phase 1.5 a prerequisite
rather than an optimisation. The **box-sizing rule** in §7.2.1 applies to Phase 2 and 3B too, and
`scripts/spot_isolation.py` now checks it.

**Phase 1.5 (§7.5) is on the plan, and is now blocking**: the ray march is **65.6 %** of a driven 2D run by
WarpX's own profiler, so before Phase 2's 2D runs and Phase 3B's ~30-point `beam_waist` sweep pay
that cost ~30 more times, three changes are scoped — cache a redundant `sample()`, OMP over rays,
and skip the provably-no-op march through vacuum (measured at 47 % of the path at `t` = 0, but
decaying to 36 % by 8 ps and to 1 % on a 27 ps run — see §7.5.2). It
is a **code** phase: no deck changes, no new physics runs, and its acceptance suite re-validates
the existing P1 corpus **spatially** (per-column profiles), because §2.8 established that a
conserved total is not a working operator.
The config schema (§3), the deck renderer, gates G1–G7, the laser diagnostics and the
cross-run comparison all work in 1D and 2D from one code path; 173 tests pass. The three
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
   absorbs strongly and weakens as its corona heats and rarefies. `Z_eff·lnΛ` is a very
   strong knob (25 → 91 gave **16×** the coupled energy).
   ⚠️ **The inherited form of this hazard — "shuts off within ~0.05 gyroperiods, coupled
   energy set by heat capacity and nearly independent of intensity" — was FALSIFIED by
   `P1_vac_1d` and `P1_vac_1d_long`; see §2.4 and §2.5.** Absorption falls onto a *plateau*
   (`f_abs` ≈ 0.24), and the plateau ends only when the rarefaction takes the peak density
   below `n_cr` (28.8 ps), so `E_abs = ∫f_abs(t)·I₀ dt` and is **not** intensity-independent.
   The rest of the hazard (that the drive is self-limiting at all, and that `Z_eff·lnΛ` is
   dangerous) stands.
5. **Phase space is the only arbiter of a shock claim.** The B and density streaks of the
   `run_laser_shock` pulse looked shock-like on their own. What disproved the shock was the
   phase space: 0.00 % ion reflection, upstream/downstream `f(u_z)` differing only by a
   drift and a mild broadening, and a piston (~1 v_A) *slower than the compression it had
   launched* (2.63 v_A). **No run in this project may be called a shock without a
   phase-space diagnostic.**

### 1.3 Explicitly out of scope

- Re-validating the ray tracer against analytic IB / WKB (done upstream; §1.1).
- Cross-validation against PSC — **done upstream at the operator level** as of 2026-08-03
  (`LASER_DEPOSITION_PLAN.md`; blocked on module access only from 2026-07-27 to then). The
  PSC ray-trace module is now in hand and builds; `laser_deposition/psc_reference/` links
  its compiled routines and calls them, and the two modules agree to round-off: lnΛ to
  **0.000e+00** over 1681 points, the coefficient to **6.7e-16**, with the whole residual
  being two constants PSC rounds (+0.4701 % and +0.0131 %). Out of scope *here* because it
  is settled upstream, not because it is blocked. Test C (the coupled expanding-plasma
  case) still awaits a matched PSC PIC run.
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

### 2.4 RESOLVED 2026-07-28 — **H2 is falsified, and the tension above is explained**

`P1_vac_1d` (10.018 ps, vacuum, `L_n/w_t` = 0.75) settles it, and the guess in the paragraph
above was right: **coupling is drive-limited, not capacity-limited.**

| measurement | value |
|---|---|
| `f_abs` | 1.000 → **plateau ≈ 0.23**, *not* → 0 |
| late/early `dE/dt` | **0.41** — not 0, so `E_abs` never rolls over |
| 90 % / 99 % of `E_abs` delivered by | 8.86 / 9.90 ps of a 10.02 ps run |
| `E_abs` | 2.4626×10⁶ J/m² = **11.5×** the `L_n` = 15 run's |

So `E_abs ≈ f_abs·I₀·t_drive` with `f_abs` quasi-steady, hence **`E_abs ∝ I₀`** — the direct
negation of H2 ("coupled energy is intensity-independent, `t_s ∝ 1/I₀`"). Absorption does not
switch off; it **floors**. A half-peak "shutoff time" is still reportable (0.2505 ps here) but
is *not* a shutoff — it is the fall onto the plateau, and quoting it as `t_s` is misleading.

**H1 is not directly tested by this**: it predicts `T_e,shutoff`, and there is no shutoff to
evaluate it at. Restate H1 in terms of what sets the **plateau level** instead of a cutoff.

**H4 loses its stated mechanism and must be re-derived.** H4 assumed H2 — that raising `I₀`
shortens the drive rather than strengthening it. With `E_abs ∝ I₀` and a floor that never
closes, raising `I₀` raises the coupled energy *and* keeps the drive running. An optimum `I₀`
may still exist, because the geometric constraint is untouched and real: a too-fast piston
crosses the box in a fraction of a gyroperiod (the upstream `3e19` run hit exactly that). But
it is a **geometry-and-timing optimum, not the capacity-ceiling optimum §2.3 describes.**
Phase 3A must therefore measure `E_abs(I₀)` and `v_p(I₀)` directly rather than test the H2
form, and its named deliverable becomes **the plateau law** — what sets `f_abs,plateau` —
rather than the `Z_eff·lnΛ` discrepancy, which the plateau picture already explains
qualitatively (`E_abs ∝ f_abs·t`, so a longer near-unity phase multiplies both factors).

**H3 is untested, not confirmed or falsified.** See `runs/P1/P1_vac_1d/README.md`: a
weight-weighted bulk gives α ≈ 0.46, but ~30 % of the slab is still cold at 10 ps and is being
averaged in, so that is a **lower bound**. A fair test must restrict to the ablated population
— which is what `plot_ablation.py` is for. **That is the next Phase-1 item.**

### 2.5 REFINED 2026-07-29 by `P1_vac_1d_long` (100 ps) — the drive DOES decay, and H3 holds

The 10 ps run could not see the end of the drive. The 100 ps run can, and it changes the
conclusion in one important way while leaving H2 falsified.

**There IS a drive-decay timescale: ~40 ps, and it is HYDRODYNAMIC.** `f_abs` holds its ≈ 0.24
plateau to ~30 ps, then decays to 0.042 by 100 ps. The cause is unambiguous:

| | t [ps] |
|---|---|
| peak `n_e` falls below `n_cr` (the turning point disappears) | **28.8** |
| smoothed `f_abs` below 0.90 / 0.75 / 0.50 / 0.25 × plateau | 20 / 34 / **41.6** / 68.9 |

So the drive ends because **the rarefaction thins the target below critical and the beam punches
through** — not because a shutoff temperature is reached (H1's mechanism), and not never (the
10 ps reading in isolation). `E_abs` = 1.349×10⁷ J/m², i.e. **57 %** of what a persistent 0.234
plateau would have delivered; late/early `dE/dt` = 0.23.

**H2 stays falsified**: `E_abs` is neither intensity-independent nor capacity-limited. The
correct form is `E_abs = ∫f_abs(t)·I₀ dt` with `f_abs` set by the target's **hydrodynamic
state**. This gives Phase 3A a concrete mechanism to test: `I₀` should set how *fast* the target
rarefies (higher `I₀` → hotter → faster `c_s` → earlier `n_cr` crossing → shorter drive), so a
**drive-duration law `t_drive(I₀)`** replaces H2's `t_s ∝ 1/I₀`. **H4's optimum may therefore
survive after all, by a different route** than §2.3's capacity argument — this is now the
sharpest thing Phase 3A can measure.

**H1 should be restated.** There is no shutoff temperature to predict. The analogous quantity is
what sets the **plateau level** (≈ 0.24 here) and the **`n_cr`-crossing time**.

**H3 is CONFIRMED: α = 1.5–2.4, inside the predicted 1–3.** The bulk saturates
(0.73 → 0.81 → 0.84 `c_s` over 50–100 ps), so it is a measurement, not a bound. Two cautions
that the 10 ps run's α ≈ 0.46 shows are easy to get wrong:

- **Use the measured electron energy for `c_s`, not `laser_report`'s implied `T_e,ab`.** By
  100 ps **66 %** of the coupled energy is in *ions*, so an implied `T_e,ab` that assumes all of
  it is electron thermal (2.775 keV) overestimates `c_s` by 2.3× and understates α to 0.84. From
  `<KE_e>` = 822 eV ⇒ `T_e` = 548 eV ⇒ `c_s` = 0.00327 c ⇒ **α = 1.90** (1.52 control-subtracted,
  2.36 by rms).
- **Never use a percentile front.** It is contaminated by undriven expansion (the laser-off
  control's own front reaches 0.0178 c) and, at late times, *truncated* by the boundary — the
  driven front reads 0.0536 c at 30 ps but 0.0245 c at 100 ps because the fast ions have left.

**Drive efficiency for Phase 2: 62 % of `E_abs` ends up in ion energy** (ion share of particle
KE rises 29.7 % → 65.8 % between 10 and 100 ps). That, and `t_drive` ≈ 40 ps against the
`5 ω_ci0⁻¹` = 38 ps that formation needs, are the two numbers Phase 2 inherits — and they say
the margin is **thin**.

### 2.6 REFINED 2026-07-29 by `P1_vac_1d_thick` (400 d_e) — **H3's thickness clause is falsified, and the thin margin is fixable**

A 5×-thicker target at otherwise identical parameters (30 ps, 36 ppc, rear-truncated) changes
three things, and two of them were predicted wrong beforehand.

**1. Thickness buys drive DURATION.** Peak `n_e` never falls below `n_cr` — it *rises* to
**1.92 `n_cr`** under ablation-pressure compression — where the 80 d_e target crossed at 28.8 ps
and lost its plateau. **So §2.5's "thin margin" against the 38 ps formation requirement is a
thickness problem, and thickness fixes it.**

**2. Coupled energy is NOT thickness-independent.** `E_abs` at 29.9 ps is **+46 %**
(1.109×10⁷ vs 7.574×10⁶ J/m²) and the plateau **+23 %** (0.2597 vs 0.2117), because `K ∝ n_e²
T_e^{−3/2}` and 5× the mass for the same drive keeps the target **colder**, which absorbs
*better*. Drive-limited means no capacity ceiling — it does **not** mean the plateau level is a
constant. (ppc confound ≤ 3.5 % against a 23 % shift.)

**3. H3's thickness clause is FALSIFIED.** H3 argued `v_p` is thickness-independent because
"thickness raises `E_abs` and the mass in step, so `v = √(2E/m)` is unchanged". **That assumed
`E_abs ∝ w_t`, which §2.4 disproved.** `E_abs` rose 46 % for 5× the mass, so

```
v_p(400 d_e)/v_p(80 d_e) = sqrt(1.46/5) = 0.54   predicted
                         = 0.63                  measured (0.00223 c vs 0.00353 c)
```

**α = `v_p`/`c_s` ≈ 1 survives** (0.92 here, 1.13 there) — that is the part of H3 that holds.
Restate H3 as: *α ≈ 1–2 universally, but `v_p` itself falls as ≈ √(`E_abs`(w_t)/w_t).*

**Consequence — a new sweep axis for Phase 3.** Thickness buys drive duration but costs piston
speed as √(E/m), and formation needs **both** a supercritical `v_p` and ≳ 1 `ω_ci0⁻¹` of drive.
**There is therefore an optimum target thickness**, and it is as consequential as the optimum
`I₀` that H4 is about. §9.2's geometry sweep must scan `w_t`, not only spot size.

**Methodological correction.** A truncated run's rear boundary sits on a **free surface**, which
*must* rarefy — checking that boundary density is "unchanged" is an ill-posed test of the
truncation. The correct criterion is **core decoupling**: the width of slab still at its initial
density between the two disturbance fronts. Here 269 of 400 d_e (67 %) stayed undisturbed while
the rear-boundary density fell 37 %, and the truncation was sound. Truncation also costs the
energy budget: **6.13 % weight loss at 30 ps** against 1.14 % at 100 ps untruncated, so
**G6 cannot be closed tightly on a truncated run** — strict closure claims must come from
untruncated runs.

### 2.7 BLOCKER 2026-07-29 — **the 2D planar validation FAILS on an operator BUG: rays clamped at the transverse boundary**

`P1_vac_2d` (uniform beam, periodic transverse, therefore *exactly planar*) against its matched
1D baseline `P1_vac_1d_thick`. §7.2 makes this the gate on every 2D physics claim, and it does
not pass.

**Not a plumbing bug.** At t = 0 the two agree on total absorbed power per unit area to
**2×10⁻⁵** (1.0000×10¹⁸ vs 9.9998×10¹⁷ W/m²), and boundary weight loss matches to **0.2 %**
(6.133 % vs 6.146 %). Ray launch, power apportionment over 64 rays, deposition mapping and the
boundaries are all correct.

**What fails.** Column-integrated `P_abs` across the 64 transverse columns, which must be uniform
to shot noise for a planar configuration:

| t [ps] | 0 | 2.99 | 8.97 | 20.92 | 26.90 |
|---|---|---|---|---|---|
| `P_abs` column rms/mean | **0.021** | 4.02 | 4.17 | 5.09 | **5.53** |

At 8.97 ps the columns span **0.10× to 25.2× the mean — a factor of 250** — and it **grows**
while the density noise does not.

**The cause is a located BUG, not physics.** The non-uniformity is confined to the **two edge
columns** — 23.2× and 25.2× the mean at 8.97 ps, with all 62 interior columns at 0.10–0.51× — and
their share of all absorption goes **3.2 % (t = 0, exactly 2/64) → 73.0 % (3 ps) → 98.8 %
(26.9 ps)**. `theta_e` and `n_e` in those columns respond accordingly, so the energy really lands
there. In `warpx-cda/Source/Particles/LaserDeposition/LaserDeposition.cpp`:

```cpp
// deposit(), ~line 739 -- clamps the cell index in EVERY dimension:
idx[d] = amrex::min(amrex::max(ii, lo3[d]), hi3[d]);
// the ray march exit test, line 893 -- checks ONLY the propagation axis:
if (c[m_axis] < plo[m_axis] || c[m_axis] > phi[m_axis]) { break; }
```

A ray that acquires transverse deflection and passes `xlo`/`xhi` is therefore **neither wrapped
periodically nor terminated**: it marches on outside the domain and every further deposit is
**clamped into the edge column**, where it unloads its remaining power.

**What supplies the deflection is benign.** The G3 control develops the same ~5 % transverse
density ripple with **no beam** (corona rms/mean 0.040 → 0.044 vs 0.056 → 0.063 driven), so it is
ordinary PIC shot noise; the start is quiet (`NUniformPerCell`, 0.06 % initial variation). At
t = 0 rays are exactly normal-incidence and the profile is uniform, which is why the artifact
switches on only once structure exists — and grows as more rays drift out.

**Therefore it will NOT converge away.** `rays_per_cell`, ppc and field smoothing are all
irrelevant to a deterministic index clamp. **The fix is upstream**: wrap the index for periodic
dimensions via `geom.periodicity()` instead of clamping, and terminate on non-periodic transverse
faces.

**Consequence.** 2D couples **+12.4 %** more energy than matched 1D (`E_abs/(P_inc·t_end)`
0.4169 vs 0.3710).

**Measurement caution.** The *median* `f_abs` over 5–25 ps differs by 48 % (0.385 vs 0.260), which
badly overstates it: 2D sums 64 rays so its distribution is smooth and median ≈ mean, while 1D's
single ray is spiky and median ≪ mean. **Compare energy-integrated `E_abs` or the mean across
dimensionalities, never the median.**

**Required before any 2D physics claim (this supersedes §7.2's ordering):**
1. **Fix the transverse boundary handling upstream** — a code change, not a convergence study.
2. **Re-run `P1_vac_2d` / `P1_vac_1d_thick` as a regression test.** The pass criterion is sharp:
   the 2 edge columns must carry ~3.1 % of the absorption (2/64), not 98.8 %, and `E_abs` must
   match the 1D baseline rather than exceed it by 12 %.
3. Only then the finite-spot run (H5) — a real transverse intensity profile cannot be separated
   from an edge pile-up of this size.

**The 1D results are unaffected**: 1D has no transverse dimension for rays to refract into, which
is precisely why this comparison isolates the effect. Also recorded: at 36 ppc the G3 control's
excursion is **−3.09 %** of the driven gain against **−0.066 %** at 400 ppc — 47× larger, the
honest price of 2D-affordable ppc, and the same poor statistics that seed the artifact.

### 2.8 RESOLVED 2026-07-29 — the §2.7 bug is fixed upstream and verified

`warpx-cda` **c817b63**, `Source/Particles/LaserDeposition/LaserDeposition.cpp`. Both the
interpolation/deposition index mapping and the ray-march exit test are now keyed off **one**
`wrap[]` flag, so a face can never be periodic for interpolation and open for termination at once:

| face | index mapping | ray march |
|---|---|---|
| periodic **transverse** | wrap (modulo) | keeps going |
| non-periodic transverse | clamp (one step only) | terminates |
| propagation **axis**, either end | clamp | terminates **always** |

The axis terminates even when nominally periodic — a beam leaving the front or back of the target
is gone. That choice is what keeps the 1D tests, which *are* periodic along z, bit-for-bit
unchanged; wrapping there would have silently changed 1D physics while fixing 2D.

**Verified on the shipped CI decks** (`Examples/Tests/laser_deposition/`), A/B against a binary
built from the pre-fix commit, at the CI configuration (2 MPI ranks). The 2D **oblique** deck is
the decisive case and is sharper than `P1_vac_2d`: 30° tilt across a 0.2 mm periodic transverse
box, so rays drift **2.9 domain widths**, while the density is uniform in x — hence the correct
answer is *exactly* uniform deposition, known analytically rather than to shot noise.

| | before | after |
|---|---|---|
| share of absorption in 1 of 8 columns | **99.53 %** | 12.50 % (= 1/8, exact) |
| per-column max/min | 9.1×10⁵ | **1.000** |
| step-0 total `P_abs` | 6.945009×10¹⁹ | **6.945009×10¹⁹** (unchanged, 7 digits) |
| `analysis_oblique.py` vs closed form | 1.29 % | **0.48 %** error |

The unchanged total is the point: the bug **moved** energy without creating or destroying it —
exactly the "misplaces energy in space while conserving the total" class `ACCURACY.md` warned all
five CI tests would miss, because every one of them reduces the operator to a total. All five pass
both before and after. 1D decks are **bit-identical** (profiles and `EP.txt`).

**CI benchmarks need resetting** — `Regression/Checksum/benchmarks_json/` for
`test_2d_laser_deposition_{oblique,gaussian,focus}`. Legitimate to reset here because the pre-fix
binary reproduces every committed benchmark to ≤4×10⁻¹⁶ (machine precision) at 2 ranks, i.e. this
build *is* the CI reference. Magnitudes: oblique +164 %, focus +4.7 %, gaussian +2.2×10⁻⁵; 1D
unchanged. `particle_momentum_*` and `j*` rise because the same absorbed energy now spreads over
8× more electrons and |u| ∝ √E is **concave** (predicted √8 = 2.83×, measured 2.46×). Gaussian and
focus move at all only because near-critical reflection off a noisy `grad n_ref` gives rays a small
transverse kick; their step-0 column distributions are byte-identical.

**Still required before any 2D physics claim:**
1. **Re-run `P1_vac_2d` and `P1_vac_2d_off`.** Their 5h07m / 1h57m of output is invalid — produced
   by the buggy operator. `build_cuda/bin/warpx.2d` has been rebuilt with the fix and is ready.
   Pass criterion unchanged from §2.7: the 2 edge columns must carry ~3.1 % of absorption (2/64),
   not 98.8 %, and `E_abs` must match `P1_vac_1d_thick` rather than exceed it by 12 %.
2. Then the finite-spot run (H5).

Note the §2.7 artifact only switched on **after** structure developed (3.2 % at t = 0 → 98.8 % at
26.9 ps), so a short slice of `P1_vac_2d` cannot serve as the regression test — which is why the
oblique CI deck, wrong from its first application, was used instead.

---

### 2.9 STARTED 2026-08-06 — **H1: the mechanism is right, the threshold is wrong by ~an order of magnitude**

H1 is the last of H1–H5 still open. H2 is falsified (§2.4), H3 confirmed (§2.5–2.6), H5 is
now *testable* thanks to `P1_vac_2d_spot_abl`'s open transverse faces, and H4 waits on Phase 3A.

**H1 as written.** Absorption shuts off when the optical depth through the absorbing layer
falls to ~1, so `T_e,shutoff ∝ (Z_eff lnΛ n_e² L)^{2/3}`.

**First leg cost nothing.** The per-cell profile dump carries `n_e`, `theta_e` *and the IB
coefficient `A`*, so τ is integrable directly off runs already on disk — the mechanism can be
tested before any new run. With `K = (A/n_cr) n_e²/√(1 − n_e/n_m)` integrated from the
injection face down to the turning point (`$CLAUDE_JOB_DIR/tmp/h1_tau.py`; fold into
`laserprod.metrics` when that exists):

| run | `I₀` | τ at `t` = 0 | τ later | `1 − e^{−2τ}` | measured `f_abs` |
|---|---|---|---|---|---|
| `P1_vac_1d` | 1e18 | 6.69 | 0.198 (5 ps) | 0.327 | ≈ 0.24 plateau |
| `P1_vac_1d_long` | 1e18 | 6.64 | 0.119 (10 ps) | 0.212 | ≈ 0.24 plateau |
| `P1_vac_1d_thick` | 1e18 | 4.85 | 0.112 (15 ps) | 0.200 | — |
| `P1_vac_2d_spot_long` | 1e18 | 6.49 | 0.485 (15 ps) | 0.621 | 0.68 final |
| `P1_vac_2d_spot_abl` | 1e19 | 6.38 | **0.131** (13.4 ps) | **0.2305** | **0.2264** |

**Three findings, and they split H1 down the middle.**

1. **The optical-depth picture of the plateau is RIGHT.** `1 − e^{−2τ}` — a ray that turns and
   comes back out — reproduces the measured plateau to **1.8 %** on `P1_vac_2d_spot_abl`
   (0.2305 vs 0.2264) and to within ±40 % across the 1D corpus. So `f_abs` really is set by the
   corona's instantaneous optical depth, which is H1's underlying claim.
2. **The corona DOES thermostat.** τ collapses from ~5–7 at `t` = 0 to ~0.1–0.2 within 1–3 ps
   and then holds roughly flat for the rest of the run while `T_e` keeps climbing. That
   self-regulation is exactly the behaviour H1 describes.
3. **But it thermostats at τ ≈ 0.1–0.2, not τ ~ 1** — an order of magnitude below H1's
   criterion. At τ = 1 the absorbed fraction would still be `1 − e^{−2}` = **0.86**, i.e. nearly
   full absorption, nothing like a shutoff. **So H1's numerical threshold is wrong, and the
   constant in `T_e,shutoff` with it.** The `(Z_eff lnΛ n_e² L)^{2/3}` *form* may still hold —
   it follows from `τ = const` and `K ∝ Z lnΛ n_e² T_e^{−3/2}` for any constant, not just 1.

   And the thermostat point is **not universal**: τ ranges 0.13 → 0.93 across the corpus, with
   the 2D spot at 1e18 sitting ~4× above the 1D runs. So "fixed τ" is geometry-dependent, and a
   single-number `T_e,shutoff` cannot be right across dimensionality.

**Consequence for the wording of H1.** `T_e,shutoff` is not a shutoff temperature — nothing
shuts off, and §2.5 already retired the half-peak `t_s` for the same reason. The quantity that
exists is the **plateau coronal temperature** `T_e,plat`, the temperature at which the corona
holds τ ≈ 0.1–0.2. H1 should be re-read as a prediction about *that*:

    H1' :  T_e,plat  proportional to  (Z_eff lnLambda n_e^2 L)^(2/3)     [exponent UNTESTED]

**What is still needed, and it does need runs.** The exponent. The one knob with a standing
quantitative tension is `Z_eff·lnΛ`: H1–H2 predict `E_abs ∝ (Z_eff lnΛ)^{2/3}`, a factor 2.4 for
the upstream 25 → 91 change, where **16×** was measured (§2.3). Nothing in *this* project has
varied `Z_eff·lnΛ` yet, so that tension is still inherited rather than reproduced. The cheapest
decisive test is a **1D vacuum ladder** — `P1_vac_1d` runs in ~8 min on one GPU:

- **Leg B (`Z_eff·lnΛ`, 3 new runs)** at `I₀` = 1e18: 5×7 = 35, 13×5 = 65, 13×7 = 91, with
  `P1_vac_1d` (25) as the anchor. H1' predicts `T_e,plat ∝ (Z lnΛ)^{2/3}`, i.e. ×2.36 over
  25 → 91. **Change it in small steps** — 25 → 91 coupled 16× more energy upstream and produced
  a 0.06 c piston, so the ladder is deliberately ordered and each step checked before the next.
- **Leg A (`I₀`, 2–3 new runs)** at `Z_eff·lnΛ` = 25: 1e17, 1e19, 1e20. H1'/H2 predict
  `T_e,plat` independent of `I₀`; the only measurement so far is `T_e ∝ I^0.18` between two 2D
  runs at different times and BCs, which is indicative at best. **This leg is what settles
  whether "nearly independent" means independent.**
- Legs C (`n_e`) and D (`L`) afterwards, and note D is confounded: `L_n` moves the absorption
  *regime* (optically thin ↔ thick, §2.5 and RESULTS 2026-07-30), not just the amount.

Report `T_e,plat` **absorption-weighted, and say so** — it runs 2–3× above the density-weighted
value, and quoting the wrong one is a factor √3 in every sound speed built on it.

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
| **1.5** | Can the ray march stop being 65 % of every driven 2D run? (a CODE phase — §7.5) | 0 new; re-validates P1 | ~1 day |
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

#### 7.2.1 RESULT 2026-07-29 — `P1_vac_2d_spot` ran; **H5 is untested, and the reason is a box-sizing rule**

The finite-spot run completed (144 000 steps, 9.961 ps, 5 h 38 m) with its control. The operator
came out **exact at `t` = 0 on a spatial measure** — per-column mean ratio to `I₀exp(−(x/w₀)²)` =
1.00010, residual lag-1 autocorrelation −0.521, total absorbed within **2.2×10⁻⁵** of `I₀w₀√π` —
and c817b63's `wall/interior` ratio stayed ≤ 1.16 on all 10 dumps against the clamp's 20–25.

**But the run stops being a finite spot after ~2 ps.** `scripts/spot_isolation.py` measures the
transverse profile of the *net* absorbed energy (driven minus the control's drain): `dark/lit` goes
**0.135 at 1 ps → 0.946 at 10 ps**, i.e. the deposited energy ends flat to 7 % across a box the
beam illuminates at **1.1×10⁻⁷ of peak**. Periodic transverse faces make the run an infinite array
of spots at 8 `w₀` pitch, and once heat crosses half the pitch the array merges.

**Cause: the box was sized with `c_s`.** The prediction was 14 ps to the wall; electrons carry the
energy and `v_th,e` = 37.7 `d_e`/ps against `c_s` = 4.0 at the measured 227 eV corona, giving
**2.1 ps** — measured 1.99 ps. Optimistic by 7× from the wrong speed alone.

> **BOX-SIZING RULE, and it applies to Phase 2 and Phase 3B as much as here:**
> `L/2 ≳ v_th,e(T_e,corona)·t_end + (initial extent)`, for **every** dimension.
> This is the third time this campaign has been caught by `v_th,e` — the Phase-0 open-boundary
> blocker, O2's vacuum estimate (§7.5.2) and now this. Ask it of every dimension before launching.

**What a valid H5 spot run costs.** `L_t/2 ≳ 396 `d_e`` for a 10 ps run — **4.9× wider**, 1 584
transverse columns against 320 — and the ray march scales *linearly* with columns. So a valid H5
run is ~5× this one on the dominant term, which is precisely what §7.5 exists to buy. The cheap
alternative is to keep the box and stop at **`t` ≲ 1.6 ps**, which no longer covers a crossing
time and so cannot test H5 either.

**H5 is untested, not falsified.** `f_ax/f_abs(1D)` is 1.09 at `t` = 0, then 0.80–1.01 through 7 ps
**with no trend**, then 0.62 and 0.56 at 8 and 9 ps — inside the invalid window. Note also that the
periodic images push the answer *toward* planar (ratio → 1), so they do not explain a fall to 0.56:
the late drop is **unexplained rather than attributed** and must not be read either way.

**Two things to carry forward.** (1) `w_eff` is the second moment of the ABSORBED POWER and the
shot-noise leak inflates it (2.39 `w₀` at a 16 % leak) — it is not the heated radius. (2) On-axis
`T_e` ends at **243 eV absorption-weighted** against **81 eV density-weighted**; state which, since
`c_s` differs by √3 and every derived timescale with it.

**`rays_per_cell` convergence is settled and needs no ladder here**: `ac1` stayed negative on all
10 dumps (−0.51 → −0.24), so the scatter is neighbour exchange from random ray wander, not the
coherent refractive channelling that would demand sub-cell sampling (`studies/rays_per_cell`).

### 7.3 Pass criteria

1D and 2D-planar agree on axis; the energy budget closes (G6); the deposition profile sits
where WKB predicts; `f_abs(t)`, `t_s`, `T_e,shutoff` and `v_p` are measured with the
laser-off control subtracted; H1 and H3 are either confirmed with fitted coefficients or
falsified with a stated replacement.

---

## 7.5 Phase 1.5 — making the ray tracer affordable (a CODE phase, not a physics phase)

**Numbered 7.5 deliberately**, so every `§7.2`/`§8.1` reference in `CLAUDE.md`, the run READMEs
and `RESULTS.md` keeps its meaning. This phase changes **no physics and no deck**; it changes what
Phases 2 and 3 cost, and it is the first phase whose deliverable is an upstream commit to
`warpx-cda` rather than a run.

### 7.5.0 Why now, and the measurement that justifies it

The eikonal ray march is the dominant cost of every driven 2D run, measured three independent
ways:

| measurement | value | source |
|---|---|---|
| `LaserDeposition::applyDeposition` share of total wall time | **65.61 %** | WarpX TinyProfiler, `P1_vac_2d` (43 200 calls, 1.208×10⁴ s of 1.842×10⁴ s) |
| next largest phase (`GatherAndPush`) | 11.39 % | same table |
| cost per application, 320-ray spot deck | **771 ms** | per-step wall times, `P1_vac_2d_spot`: 64.6 ms without an application, 836.1 ms with one |
| driven vs laser-off step, same grid | 0.140 vs **0.0702** s/step | `P1_vac_2d_spot` vs `P1_vac_2d_spot_off` |
| serial RK4 steps per application | **1.47×10⁶** | 320 rays × ~4 600 steps (`path/(ray_cfl·dz)`) |
| per RK4 step | **0.52 µs** ≈ 1 570 cycles at 3 GHz | derived from the two rows above |

The last number is the tell: one RK4 step is ~120 flops, so this is running at ~1 % of scalar
peak. It is **serial host code** — the march is a plain `for` loop, not inside a `ParallelFor`,
and `LaserDeposition.cpp` contains no `#pragma omp` at all — so on a box with 32 cores and 5 888
CUDA cores this phase uses exactly one scalar core. `nvidia-smi` shows the driven run oscillating
**0 % → 61 % → 0 %** while the laser-off control holds a steady 82–90 %.

**Why it pays now rather than after Phase 2.** Everything downstream is 2D and driven: `P2_mag_2d`
quasi-1D and then finite-spot (§8.3), and Phase 3B's geometry sweep, which scans `beam_waist` over
~30 points (§9.2). All of them pay this cost, and the march scales **linearly with transverse
columns** — which is precisely what makes an H5-scale spot (`w₀` ≈ 0.8 `ρ_i0` = 214 `d_e,cr`,
~3 400 columns) unaffordable today. A ~15× on this phase converts to ~1.9× on every driven 2D run
and moves H5's real spot size from impossible to expensive.

**Time box.** If the acceptance suite in §7.5.4 is not passing within a day of work, the phase is
abandoned and Phase 2 proceeds at the current cost. A performance phase that eats the physics
budget has failed even if the code is faster.

### 7.5.1 O1 — OMP-parallelise over rays

**Legality.** Rays are independent by construction: `n_host` is gathered once per application
(`ParallelCopy` to a single full-domain box, then `dtoh_memcpy`) and is **not written** during the
march, and `trace_ray` has no ray-to-ray coupling. The frozen field is what makes this safe.

**The race surface is THREE pieces of state, not two.** The source audit of 2026-07-29 corrected
this section: two are in `deposit()`, and the third is easy to miss and much more dangerous.

```cpp
H_arr(idx[0], idx[1], idx[2]) += absorbed / (n_e * V_cell) * inv_me;   // deposit(), line ~780
absorbed_power_total += absorbed;                                      // deposit(), line ~782
amrex::Real A_loc = m_K_coeff;                                         // line ~716  <-- THIS
```

`A_loc` is the interpolated inverse-bremsstrahlung coefficient at the most recent `sample()`
position. It is declared in the enclosing scope and captured by reference precisely *because*
`sample` is called from the RK4 stages that do not need it — it is a side channel, documented as
"read it immediately after the `sample` whose position you mean". Under `#pragma omp parallel for`
over rays, every thread writes it on every one of the five samples per step, and each then reads
whatever another thread last wrote. **That does not perturb rounding — it corrupts the absorption
coefficient**, so the run would produce plausible, smooth, entirely wrong physics with no crash and
no conservation violation. It is exactly the failure mode §2.8 was written about.

The fix is to stop it being shared at all rather than to guard it: make it an out-parameter of
`sample()`, so callers that need it own a local and callers that do not pass scratch. That also
removes the "read it immediately after" ordering contract, which is a latent hazard even in serial
code. **O1 must not be attempted as a bare `parallel for`.**

Everything else in the enclosing scope is safe to share, and the compiler enforces the important
part: `n_arr` and `A_arr` are `const_array(mfi)`, and the geometry (`plo`, `dxi`, `lo3`, `hi3`,
`wrap`, `h`, `max_steps`, …) is `const`. All of `trace_ray`'s march state (`c`, `T`, `P`, `n_ref`,
`g`, `r_prev`, `ne_prev`, and O3's `s_valid`) is local to the invocation, so it is per-ray already —
one reason O3 was written with its state inside `trace_ray` rather than beside `rk4`.

The `MFIter` at line ~683 walks the **gathered full-domain box**, so there is exactly one iteration
and the ray loop is the unambiguous parallel region — no question of nesting the parallelism at the
box level.

`absorbed_power_total` is a `reduction(+:)`. `H_arr` is the design decision:

- **Atomics** (`#pragma omp atomic`) — two lines, low contention (nearest-cell deposition keeps a
  normally-incident ray in its own column), but the summation order into a cell becomes run-to-run
  variable. That is a real cost *here*: the pre-fix binary reproduced every committed
  `laser_deposition` checksum to **≤4×10⁻¹⁶** (§2.8), and this campaign has just had to reset
  those benchmarks once.
- **Per-accumulator buffers, reduced in fixed order** — deterministic, and the memory is trivial in
  2D. Budget it as `N_ACC × n_cells × 8 B`: the spot run's 320×2200 box is 5.6 MB per buffer, so
  **45 MB at `N_ACC` = 8** and 90 MB at 16. Worth checking before an H5-scale spot, where 3424
  columns give 60 MB per buffer — **482 MB at 8, 963 MB at 16** — so `N_ACC` should be a runtime
  parameter, not a compile-time constant, and it must be logged with the run.

**Take the buffers, and decouple the accumulator count from the thread count.** Use a fixed
`N_ACC` (16) buffers with ray `i` → buffer `i % N_ACC`, reduced in buffer order. Then the result is
**bit-identical for any `OMP_NUM_THREADS`**, which is a far stronger and more testable property
than "reproducible at fixed thread count", and it is what §7.5.4's thread-invariance test checks.
Schedule `static, 1` so that adjacent rays — which have similar cost — land on different threads:
load balance matters because `trace_ray` exits early on `P > P_min` (`P_min = 10⁻⁸ P0`), so a core
ray extinguished before its turning point costs a fraction of a wing ray that transits the domain.

**Two machine-specific blockers, both to be fixed in this phase:**

- `scripts/launch.sh --gpu` **forces `OMP_NUM_THREADS=1`**, on the then-correct reasoning that with
  the CUDA backend the push is on the device and host threads only contend. Once the march is
  threaded that inverts for *driven* runs: add a flag, and record the benchmark.
- This box collapses above ~12 threads (14.5 / 41.5 / 58.5 / **64.9** steps/s at 1/4/8/12, then
  **3.1** at 16) because it is shared and the OpenMP spin-wait barriers burn the timeslice. The
  realistic factor is **6–8×**, not 32×. Do not quote a scaling curve measured on a loaded box.

**3D caveat, stated now so it is not discovered later.** At 10⁸ cells a per-accumulator FAB is
800 MB, so 3D needs tiled accumulators or atomics. 3D is out of scope (§1.3) but the operator is
not, and the header should say which regime the buffers assume.

### 7.5.2 O2 — skip the march through vacuum

**This is not an approximation, it is a no-op removal.** Where `n_e` = 0, `sample()` returns
`n_ref` = 1 and `g` = 0, so the RK4 integration of `dc/ds = T/n_ref`, `dT/ds = ∇n_ref` reduces
**exactly** to a straight line (all four stages return the same derivative), and `ne_m` = 0 skips
the `deposit()` branch entirely. The code spends 24 interpolations per step rediscovering that
light travels straight through nothing.

**CORRECTED 2026-07-29 — the payoff is ~2×, not ~9×, and it decays during the run.** The
estimate above was geometric: the fraction of the *domain* in front of the target. Measured from
the `n_e` in the dumps (`studies/ray_march_perf/vacuum_fraction.py`, figure
`media/ray_march_perf/o2_vacuum_fraction.png`), `f_vac` is a **function of time** and much smaller:

| run | `f_vac` at `t` = 0 | march speedup | `f_vac` at `t_end` | march speedup |
|---|---|---|---|---|
| `P1_vac_1d_thick` | 0.636 | 2.75× | 0.011 (26.9 ps) | **1.01×** |
| `P1_vac_2d` | 0.636 | 2.75× | 0.010 (26.9 ps) | **1.01×** |
| `P1_vac_2d_spot` | 0.471 | 1.89× | 0.360 (8.0 ps) | **1.56×** |

**Why it decays: the fast-electron halo, not the hydrodynamic plume.** At the measured coronal
`T_e` ≈ 300 eV, `v_th,e` = 7.3×10⁶ m/s = **43 `d_e`/ps**, which is **10× `c_s`** (4.3 `d_e`/ps). The
`10⁻⁴ n_cr` contour is therefore carried across the forward gap on a `L_vac/v_th,e` timescale —
1200 `d_e` in ~28 ps, which is exactly when `P1_vac_2d`'s `f_vac` reaches 0.01. Sizing the vacuum
gap from `c_s` would have over-estimated O2's lifetime tenfold.

`(L_vac(0) − v_th,e t)/L_tot` tracks `P1_vac_2d` closely but over-predicts the spot's decay, so it
is the mechanism and the timescale rather than a fit — the contour front is a rarefaction with a
velocity spectrum, not a step. **A tempting explanation for the spot was tested and falsified**: it
is *not* that only illuminated columns develop a halo. Dark columns retain **1.01×** the vacuum of
lit ones, because the halo crosses the 160 `d_e` transverse box in ~4 ps and fills it uniformly.

**Choose `n_th` from the trade-off, do not assume it.** Sweeping the threshold on the last dump
(same script, `--sweep`) gives, for `P1_vac_2d_spot`:

| `n_th` [`n_cr`] | march speedup | `τ_discarded` |
|---|---|---|
| 10⁻⁴ (the value assumed below) | 1.56× | 3.0×10⁻¹⁰ |
| 10⁻² | 1.93× | 2.7×10⁻⁵ |
| **3×10⁻²** | **2.00×** | **3.5×10⁻⁴** |
| 10⁻¹ | 2.10× | 6.0×10⁻³ |
| 3×10⁻¹ | 2.24× | 1.1×10⁻¹ |

**Take `n_th` = 3×10⁻² `n_cr`**: it buys the full 2.00× while discarding `τ` = 3.5×10⁻⁴, still
**300× below the 10.4 % 1σ seed spread on `f_abs(0)`**. Going to 10⁻¹ buys 5 % more speed for 17×
the error — a clear knee. The 10⁻⁴ originally assumed here is over-conservative by 0.44× in speedup
for no measurable accuracy gain.

> **FALSIFIED 2026-07-30, on implementation. There is no threshold, and this whole sweep asked
> the wrong question.** Built as specified, `n_th` = 3×10⁻² moved the 1D ramp CI deck's absorbed
> fraction by **+6.13 %** — from 1.2 % below the closed form to 4.9 % above it, against a 0.48 %
> tolerance. The discarded τ was never the only error available to a skip:
>
> - Below the threshold the medium still **refracts**, so the discrete march does not advance by
>   `h` per step. Measured on the ramp deck, it **lags the straight line by 1.6×10⁻³ h over 16
>   steps** — so an analytic jump of a whole number of steps lands the ray *ahead* of where the
>   march would have been.
> - That lead flips the discrete near-critical trigger `n_ref ≤ n_floor && drds > 0`. Pre-change
>   the trigger never fires on this deck (the ray turns by refraction alone); after the jump it
>   fires and the analytic layer deposits 4.6 % of the beam. **Discrete**, which is why skipping
>   one cell and skipping four gave the identical +6.13 %.
> - Not general fragility: perturbing `ray_cfl` by 1 part in 10⁷ moves the same total by 9×10⁻⁶.
>
> **A cheap approximation upstream of a discrete trigger is not bounded by its own smallness.**
> O2 as shipped is the no-op removal this section's first sentence claimed: it skips the five
> `sample()` calls of steps lying wholly in *exactly* empty field, keeping the arithmetic and its
> order, and is bit-identical on every deck tested. It gives up nothing where it was supposed to
> pay — `Vskip` on `P1_vac_2d_spot` at t = 0 is **0.47**, matching the 0.471 measured here with a
> 10⁻⁴ `n_cr` contour, because a vacuum gap is empty to the bit. Measured 1.53× on the march
> (a vacuum step still costs φ = 0.26 of a full one) against the 2.10× the threshold would have
> bought. See `studies/ray_march_perf/README.md`.

This is still the cost side of the rule that the launch plane must sit outside the plasma — but the
gap is only expensive **early**, and a long run pays the full march regardless.

**Implementation — one reduction, one analytic jump.** Per application, reduce the
already-gathered host field for the extreme `z` at which any cell exceeds `n_th`, then advance each
ray analytically from the launch face to that plane before entering the loop.

- The reduction is one pass over the gathered field (~0.5 ms against 771 ms).
- Take the **global** max over all columns, not a per-column value: then no ray of *any* direction —
  oblique, converging, or wandered — can have interacted above that plane. Conservative and exact,
  and it keeps `beam_focus` and `incidence_angle` correct for free.
- Run the exit test after the jump, so a ray that never meets plasma terminates immediately.
- It degrades to a no-op in exactly the documented awkward case (a corona that has reached the
  injection face), because then the entry plane *is* the face.
- Bonus: it removes exposure to `max_steps = 6·L_sum/h + 100`, since skipped steps no longer count.

**The error is computable, and that is the point.** With this deck's own coefficient
(`K` = 2.1054×10⁷ m⁻¹ at 1.5 `n_cr`, `τ` = 1411 over the 400 `d_e` flat top) and `K ∝ n_e²`, at
`n_th` = 10⁻⁴ `n_cr`: `K` = 0.094 m⁻¹, so over 500 `d_e` of skipped path
**`τ_skipped` = 7.9×10⁻⁶** — 8×10⁻⁴ % of the beam, **four decades below the 10.4 % 1σ seed noise
on `f_abs(0)`**. Refraction is equally safe (`n_ref` = 0.99995). Tightening the threshold is nearly
free because the corona is steep: its 10⁻³ and 10⁻⁴ `n_cr` contours sit only 20 `d_e` apart.

**Rejected alternative: adaptive `h` inside the march.** More general — it would also skip vacuum
*inside* the domain once the plume goes non-monotonic — but it changes the integrator everywhere,
and `ray_cfl` convergence is **non-monotonic for turning-point problems** with the 0.25 default
sitting near a 2.5 % excursion (G4). That is a re-validation of the whole accuracy suite for a
second-order win. Revisit only if O1+O2 miss the §7.5.5 target.

### 7.5.3 O3 — the redundant sample (free, exact)

Each march step calls `sample()` **six** times: four RK4 stages, one at the step midpoint for the
absorption, and one at the new position `c`. That last one recomputes exactly what the *next*
iteration's first RK4 stage computes at the same `c`. Cache it: 6 → 5 samples per step, **~17 %**,
bit-identical results. Do this first — it is the cheapest possible confidence-builder in the
harness.

### 7.5.4 Acceptance suite — tested against the EXISTING P1 corpus, and spatially

**The governing rule comes from §2.8: a conserved total is not a working operator.** The clamp bug
passed all five CI tests throughout its life because each reduces the operator to one number, and
the clamp *relocated* energy while conserving the total to 7 digits. So no acceptance test in this
phase may be a total alone.

**Tier 1 — upstream CI decks** (`Examples/Tests/laser_deposition/`), which are the analytic tests:

| deck | criterion |
|---|---|
| 1D uniform slab (A), 1D ramp/turning point (B1) | **bit-identical** to pre-optimization output, profiles and `EP.txt` |
| 2D oblique (B2) | per-column share stays **12.50 % (= 1/8) exactly**, per-column max/min **1.000**, `analysis_oblique.py` vs closed form ≤ 0.48 % |
| 2D gaussian, 2D focus | step-0 per-column distribution byte-identical; checksums within the committed tolerance |

The oblique deck is the decisive one and is sharper than any research deck: 30° tilt, rays drift
2.9 transverse domain widths, density uniform in `x`, so the correct answer is *exactly* uniform —
known analytically rather than to shot noise.

**Tier 2 — spatial re-validation on the P1 decks already on disk.** Two steps each
(`max_step = 2`), comparing the step-0 `laserdep_profile` dump cell by cell and column by column:

| P1 deck | what it tests | criterion |
|---|---|---|
| `P1_vac_1d_thick` | 1D, 36 ppc, thick target, rear truncation | per-cell `P_abs` **bit-identical** (1D has no transverse dimension, so O1's accumulator order is the only thing that could move it) |
| `P1_vac_2d_spot` | the Gaussian spot, 320 columns | per-column profile vs analytic `I₀exp(−(x/w₀)²)`: mean ratio **1.00010 ± 0.0002**, column-to-column scatter **2.54 % ± 0.1**, lag-1 autocorrelation **−0.51 ± 0.03**, 2 edge columns / peak column **2.33×10⁻⁷ ± 5 %** |
| `P1_vac_2d_spot` | total, as a cross-check only | absorbed `5.940787×10¹²` W/m vs analytic `I₀w₀√π`, agreement **≤ 3×10⁻⁵** (it is 2.2×10⁻⁵ today) |
| `P1_vac_2d` (invalid physics, valid cost) | the forward-gap geometry | O2's win must match `1/(1−f_vac)` **measured on the same dump** by `vacuum_fraction.py` — 2.75× at step 0, falling to 1.01× by 26.9 ps. (The earlier "~9×" was geometric and would have FAILED a correct implementation.) The step-0 column profile must stay flat to shot noise |
| `spot_leak_ppc` `t` = 0, either variant | that the deposition is an exact image of the beam, with **no shot-noise allowance at all** | `w_eff/w₀` **1.0000**, `f_ax` **0.9999**, `f(1w₀)` **0.9973**, `f(2w₀)` **1.0009**, leak > 2.5 `w₀` **0.00041** |

`scripts/spot_report.py` already prints every Tier-2 number; the acceptance test is a diff of its
output, not a new script.

The `spot_leak_ppc` row is the sharpest transverse criterion in the suite and deserves its
reasoning stated: those five numbers came out **identical at 36 and 144 ppc** (2026-07-29, see
`studies/spot_leak_ppc/README.md`). A quantity that does not move when the particle count
quadruples is geometry, not statistics — so unlike every other transverse number in this campaign
it carries no `1/√ppc` floor, and the tolerance is the precision it is printed to rather than a
noise budget. Any change to the ray march that shifts these has changed the operator.

Its companion warning for Tier 3: `w_eff/w₀` grows from 1.000 to ~1.5 by 1 ps because inverse
bremsstrahlung goes as `T_e^{−3/2}` and the spot suppresses its own coupling on the hot axis. That
is **real physics and must survive the optimisation** — it is not the shot-noise leak that sits in
the same profile, and an O2 vacuum threshold set carelessly could flatten it.

**Tier 3 — time-integrated agreement on a real slice.** Re-run 1–3 ps slices of
`P1_vac_1d_thick` and `P1_vac_2d_spot` and compare against the runs on disk:

- `E_abs(t)` within **0.5 %** — well inside the 10.4 % 1σ / 30.6 % full seed spread on `f_abs(0)`,
  and comparable to the 0.6 % at which `E_abs` agreed across geometries.
- the `spot_report` columns `f_ax`, `w_eff/w₀`, `leak>2.5w₀`, `wall/in` within their own
  dump-to-dump scatter.
- **`E_abs` is the comparison, never `f_abs(0)`** and never a median across dimensionalities.

**Tier 4 — determinism and thread invariance** (this is what buys the buffer design over atomics):

- same binary, same deck, run twice → **bit-identical**;
- `OMP_NUM_THREADS` = 1, 2, 4, 8, 12 → **bit-identical to each other**, by the fixed-`N_ACC`
  reduction of §7.5.1;
- CUDA build vs OMP build → *not* expected identical (device reductions and RNG streams differ);
  the criterion there is `E_abs` within the 2.5 % already measured between backends.

**Revert rule.** Any acceptance test outside its stated tolerance means the optimization is
reverted, not the tolerance widened. The tolerances above are written before the work, which is
the point of writing them here.

### 7.5.5 Cost target, and what it unlocks

| quantity | now | target | **ACHIEVED 2026-07-30** |
|---|---|---|---|
| `applyDeposition` share of a driven 2D step | 54 % (65.6 % of the planar run) | **≤ 10 %** | **6.1 %** ✓ |
| driven 2D step, spot deck | 0.140 s | **≤ 0.080 s** (control is 0.0702) | **0.0743 s** ✓ (control 0.0698, so +6.4 %) |
| per application, 320 rays | 771 ms | **≤ 60 ms** | ~100 ms at 36 ppc ✗ — but see below |
| `P1_vac_2d_spot` (9.96 ps) | 5.6 h | ~2.8 h | **~2.9 h** ✓ |
| a 40 ps 2D run to the formation time | ~22 h fixed-domain | ~11 h | ~11 h ✓ |
| H5-scale spot, `w₀` = 214 `d_e,cr` (~3 400 columns) | unaffordable | expensive but reachable | reachable; the march threads, and the last O(cells) serial host loop is gone |

Measured end to end on the real deck and real config (36 ppc, `intervals` = 10, GPU, 40 steps):
**0.1453 s/step before, 0.0743 s/step after** — the 0.1453 reproduces the 0.140 s this table was
written from. A driven 2D run is **1.96× faster**, and the laser now costs 6 % of a step.

The per-application row is the one miss, and it is a mis-specified target rather than a
shortfall: it was written when the march *was* the application, and 60 ms was the march's
budget. The march is now ~79 ms of a ~100 ms application on a **shared box at load 18**, where
`ray_threads` = 8 beats 16; the step-level target the row exists to serve is met with room.

Expected factors, partly replaced by measurements: O3 ~1.17×, O1 6–8× (still an estimate),
O2 **2.00× at `n_th` = 3×10⁻² on the spot at 8 ps, decaying to ~1.0× on a long run** (measured,
2026-07-29 — not the ~9× first assumed) — multiplicative on the same phase, so **~10× combined at
best and ~7× on a long run**, not ~15×, and the
driven step lands within ~6 % of the laser-off control.

**MEASURED 2026-07-30** on the `P1_vac_2d_spot` geometry, `rayTrace` timed directly by a
per-phase profiler region: O3 **1.27×**, O2 **1.92×** (the exact version, not the falsified
threshold), O1 **6.2×** — **10.9× combined** on the march, in line with the ~10× allowed for.

A fourth optimisation, which this section did not anticipate, came out of decomposing what was
left. The per-cell IB coefficient was built in a **serial host loop with a `pow(kT, 1.5)` per
cell**, on data that lives on the device, and it forced the full-domain gather to move all six
components to the host because the temperature moments were consumed only there. Forming the
coefficient on the device instead — into the measured field, over the momentum moments, which
are dead afterwards — makes the gather move 3 components instead of 6 and retires the pinned
`A_host` allocation. Bit-identical, `Tlocalfrac` included. Worth **−18 %** of the whole
operator on CPU and ~10 ms per application on GPU, and it matters more with grid size than the
current runs show: it was the last O(cells) serial host work in the operator.

**A correction to an earlier version of this paragraph.** It reported that everything except the
march cost "0.250 s per application, unthreaded", i.e. 81 % of the operator. That was a
benchmark artifact: `profile_intervals = 1000000` does **not** disable the per-cell dump — an
`IntervalsParser` period contains step 0 — so every benchmark run wrote a 74 MB table from
inside `applyDeposition` and charged it to the operator. Only `intervals = 0` disables a
diagnostic. The corrected floor is 0.057 s at ppc = 1 on CPU and **0.009 s on GPU**. The march
speedups were unaffected (the spurious time was in both the total and the subtracted floor).

### 7.5.6 Deliverables

1. An upstream commit in `warpx-cda` touching only
   `Source/Particles/LaserDeposition/LaserDeposition.{cpp,H}`, with the accumulator design and the
   `n_th` threshold documented in the header where the next reader will find them.
2. `studies/ray_march_perf/` — the benchmark ladder (threads × O1/O2/O3 on/off), reducing to a
   table of s/step and profiler shares, plus the Tier-4 determinism check as a script.
3. A `RESULTS.md` entry with the measured factors and any acceptance test that moved.
4. `CLAUDE.md` performance bullets updated — including retiring "the eikonal ray march is a plain
   host loop, so the GPU idles during it", which will no longer be true, and revising the
   `--gpu` forces `OMP_NUM_THREADS=1` guidance.
5. If `Examples/Tests/laser_deposition/` benchmarks move at all, the reason, per deck, in the
   commit message — never a bulk reset.

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
- [x] `P1_vac_1d` + `P1_vac_1d_off` (G3) + `ray_cfl` check (G4) — both reached max_step
      2026-07-28; `ray_cfl` ladder is `studies/exit_overshoot/` (0.05–1.0)
- [x] Energy budget closes (G6) — **−0.74 %** on `P1_vac_1d` at 0.0104 % WEIGHT loss (0.68 %
      of macroparticles; the escapers are the tenuous corona tail, which is why quoting weight
      rather than count is what let G6 close at all). Step-0 deposition profile analysed
- [~] `f_abs(t)` and `v_p` measured; **`t_s` RETIRED** as a quantity — absorption floors onto a
      plateau and then decays hydrodynamically when peak `n_e` drops below `n_cr`, so a half-peak
      shutoff time is meaningless (quote the plateau level, the `n_cr`-crossing time and `dE/dt`
      instead). **H3 CONFIRMED** (α = 1.5–2.4 from the MEASURED `<KE_e>`, §2.5). **H1 is what
      remains, and `T_e,shutoff` has to be redefined with it** — see §2.9
- [ ] Self-similar rarefaction / Schaeffer Eq. 1 recovered
- [ ] `P1_vac_2d` planar reproduces 1D on axis — **still open, and now a bookkeeping problem
      rather than a physics one**: `P1_vac_2d_omp` is valid but its control `P1_vac_2d_off`
      predates the c817b63 clamp fix, so the pair cannot be differenced. Only the control needs
      re-running (RESULTS 2026-07-31)
- [x] `P1_vac_2d_spot` + `_off` RAN (9.96 ps, 5 h 38 m). Operator **exact at `t` = 0** on a
      spatial measure (per-column ratio 1.00010, ac1 −0.521, total within 2.2e-5 of `I₀w₀√π`);
      c817b63 `wall/in` ≤ 1.16 on all 10 dumps. G3 −13.2 % (negative), G6 −16.86 % at 2.06 %
      weight loss
- [ ] **H5 still untested** — `P1_vac_2d_spot` loses transverse isolation after **1.99 ps**
      (`dark/lit` 0.135 → 0.946), so the predicted degradation appears only in the invalid window.
      Needs `L_t/2` ≳ 396 `d_e` (4.9× wider, 1 584 columns) for 10 ps — i.e. it waits on Phase 1.5
- [x] **A finite spot can be held together after all, but by changing the BOUNDARY, not the box**
      (`P1_vac_2d_spot_abl`, 2026-08-06). A periodic box needs `L_t/2 ≳ (v_th,e/v_crit)·D + 1.5w₀`
      for a crater of depth `D`, and the MEASURED ratio is `v_th,e/|v_crit|` = **23** —
      intensity-independent, since both speeds go as `√T_e`. So no affordable periodic box works.
      With **open** transverse faces the lateral heat leaves instead of accumulating: `dark/lit`
      0.116 → 0.394 (9 ps) → 0.523 (13.4 ps) against 0.946 by 10 ps periodic. Isolated ~5 ps,
      marginal to ~12 ps. **This is what makes an H5 `w₀` scan possible**, and the remaining lever
      is a wider box or a larger `w₀`, not the BC
- [x] `P1_vac_2d_spot_abl` — the first run built to make the ABLATION visible: crater **46.1 d_e
      = 2.30 `w₀` = 92 cells** at 14.94 ps, deepening at **3.56 d_e/ps** (predicted 3.2–4.7 ✓).
      Ablation removes mass on axis (areal density −16.8 % vs −2.7 % unlit) while ALSO acting as a
      piston (peak on-axis `n_e` rises 1.500 → 1.579 `n_cr`). Ran `refraction = 0`, validated
      against a matched refracting reference at `t` = 0 to **3.4e-6**
- [x] **`T_e` is nearly intensity-independent** — 236.0 eV at `I₀` = 1e18 → 355.9 eV at 1e19,
      ×1.51 for ten times the intensity, i.e. `T_e ∝ I^0.18` (same estimator on both, but
      different `t` and transverse BC, so indicative). This is **H1's signature**, and it is why
      H1 is now the live hypothesis — §2.9
- [~] **H1 half-settled at zero GPU cost** (§2.9). τ integrated straight off the existing profile
      dumps, since they carry `A` as well as `n_e` and `theta_e`. The optical-depth picture of the
      plateau is RIGHT — `1 − e^{−2τ}` reproduces `f_abs` to **1.8 %** on `P1_vac_2d_spot_abl` —
      and the corona really does thermostat, τ collapsing 6.4 → 0.13 in ~1.5 ps and then holding.
      But it holds at **τ ≈ 0.1–0.2, not τ ~ 1**, so H1's threshold is out by an order of
      magnitude (τ = 1 would mean `f_abs` = 0.86, not a shutoff), and τ is geometry-dependent
      (0.13–0.93 across the corpus). The `^{2/3}` EXPONENT is untested and needs Legs A/B
- [x] `w₀` scan NOT started, and deliberately deferred: a scan in a box this size would measure
      the box, not `w₀`
- [x] `rays_per_cell` convergence settled without a ladder — `ac1` negative on all 10 dumps
- [x] `scripts/spot_isolation.py` — the reusable check, and the `v_th,e` box-sizing rule (§7.2.1)
- [x] `studies/rays_per_cell/` — sub-ray convergence: scatter RISES x4.4 from rpc 1 to 4
      (my written prediction was falsified); `ac1` negative at every dump, so the developed-plume
      ladder is unnecessary and rpc 1 stands
- [x] `studies/spot_leak_ppc/` — the 7 % transverse leak is **two** effects. The far-wing
      pedestal is macroparticle noise (falls x0.25 = the noise POWER at 0.25/0.50 ps, and the
      wings absorb 4x the light incident on them, so it is transported core light). The ~1.5x
      broadening of the absorbed profile is **real and thermal**: `w_eff/w₀` = 1.000 at `t` = 0,
      transverse `n_e` flat to 0.6 %, `T_e` 2.0x hotter on axis, and IB goes as `T_e^{−3/2}` — the
      spot suppresses its own coupling where it is brightest. Consequences: 36 ppc under-reports
      `f_ax` by 16 %, the heated radius is ~1.5 `w₀` not `w₀`, and `f_ax` (0.39) is not `f_abs`
      (0.63). Unsettled: the converging ppc (2 points, and the weak-scattering law fails by
      0.75 ps)

**Phase 1.5 — the ray march (a CODE phase, §7.5)**
- [x] O3: cache the redundant end-of-step `sample()` (6 -> 5 per step, bit-identical) — **1.26×**
- [x] O1: OMP over rays, fixed `N_ACC` accumulators so the result is thread-count invariant —
      **6.2× at 12 threads**; parallel over BUCKETS, not rays (§7.5.1's `static,1` schedule would
      have raced whenever the thread count does not divide `N_ACC`), and `A_loc` retired as a
      shared side channel
- [x] O2: skip the vacuum — **but not by a threshold or a jump**: `n_th` = 3×10⁻² is FALSIFIED
      (+6.13 % on the ramp CI deck, §7.5.2). Empty steps keep their arithmetic and drop their
      samples; bit-identical, **1.53×**, and `Vskip` = 0.47 on the spot deck at t = 0
- [x] Tier 1: the five CI decks — **285/285 bit-identical** at `n_accumulators=1`; oblique 1/8
      exact; at the default 16 only the oblique `EP.txt` moves, by 1.3×10⁻¹⁵
- [x] Tier 2: `P1_vac_2d_spot` step-0 dump **byte-identical** with O2 active
- [x] Tier 4: every `LASERDEP` line byte-identical across `OMP_NUM_THREADS` 1/2/4/8/12. The
      residual 2–5×10⁻¹⁵ `EP.txt` thread-dependence is **pre-existing** — the pre-change binary
      gives the identical numbers — so `EP` is not a valid criterion for this claim
- [x] `studies/ray_march_perf/` benchmark ladder (`bench.sh`); measured factors in `RESULTS.md`
- [x] `CLAUDE.md` performance bullets updated (the "GPU idles during the march" note retires)
- [ ] Tier 3: `E_abs` within 0.5 % on 1-3 ps slices — not run, and largely retired by Tier 1/2
      bit-identity (there is no drift to integrate when the dumps are byte-equal). Worth one run
      on the GPU build, which is genuinely different code
- [x] `build_cuda_omp` built and benchmarked: **0.1453 → 0.0743 s/step** end to end on the real
      deck, the operator down to 6.1 % of a driven step. `launch.sh --gpu` now warns when a
      driven deck sets no `ray_threads` (`OMP_NUM_THREADS=1` stays right for the push)
- [x] **O4, unplanned**: form the IB coefficient on the device and gather 3 components instead
      of 6 — the last O(cells) serial host loop, −18 % of the operator on CPU, bit-identical
- [x] launch a physics run on `build_cuda_omp` — four now: `P1_vac_2d_omp`,
      `P1_vac_2d_spot_omp`, `P1_vac_2d_spot_long` (12 h 23 m) and `P1_vac_2d_spot_abl`
      (4 h 49 m, the first on **two** ranks / two GPUs)

**Phase 2 — ambient**
- [~] `scripts/phase_space.py` and `make_movies.py` **built**; `tune_shock.py` and
      `make_figures.py` still missing (both are only needed once there is a shock to fit)
- [ ] `P2_unmag` (+`_off`) — negative control, calibrates the pipeline
- [ ] `P2_mag` (+`_off`) retargeted for `M_ms ≈ 2.6`; seven criteria, three timescales
- [ ] Phase space checked **before** any shock claim
- [ ] `P2_mag_2d` quasi-1D, then finite spot

**Phase 3 — sweeps**
- [ ] `studies/sweep_intensity/` — `I₀`, `Z_eff lnΛ`, λ₀, `w_t`, `L_n`, duration
- [ ] Resolve the 16× vs 2.4× `Z_eff lnΛ` discrepancy — **now a defined 1D ladder, §2.9 Leg B**
      (3 runs, ~8 min each). Still inherited, not reproduced: nothing in this project has varied
      `Z_eff·lnΛ` yet
- [ ] **§2.9 Leg A — the `I₀` ladder** (1e17/1e19/1e20 in 1D at `Z_eff·lnΛ` = 25). Settles whether
      `T_e,plat` is *independent* of `I₀` or merely weakly dependent; the only datum is
      `T_e ∝ I^0.18` between two 2D runs at different times and BCs
- [ ] `studies/sweep_geometry/` — dims, `w₀`, profile, θ₀, focus, target shape, inject side
- [ ] Scaling summary: fitted exponents, H1–H5 verdicts, the working parameter box

**Throughout**
- [x] Every run dir has a `README.md` before it is launched (`launch.sh` enforces) — held for
      every run to date
- [x] `RESULTS.md` dated entry per substantive run or finding — held; ~25 entries
- [x] Gates G1–G7 reported for every run — held, including the ones that legitimately WARN
      (`P1_vac_2d_spot_abl` runs with G3 open by decision, recorded in its config and README)

**Phase 4 — cross-code validation (§12)**
- [ ] **D1–D8 steered** — `runs/P4/README.md` decision register signed off
- [ ] `deck.py` emits a `collisions:` block, in `--verify` (§12.3)
- [ ] `deck.py` emits a hybrid solver block, in `--verify` (§12.3)
- [ ] Collision-module gate: paper Appendix B `e-i` thermalisation vs Eq. (B1), and
      Appendix C conductivity — **before** trusting `P4_lez_kin` (§12.8 risk 1)
- [ ] `P4_lez_flash` deck + handoff note delivered to collaborator
- [ ] FLASH outputs returned to shared; `t` = 0.1 ns snapshot in hand (D1)
- [ ] `P4_lez_kin` ppc ladder 500 → 2000 → 10000, stopped on convergence
- [ ] `P4_lez_hyb` (`electron_energy_mode = advected`) — control for §12.4
- [ ] `scripts/xcode_compare.py` + the A1–A8 table
- [ ] Verdict on the §12.6 hybrid prediction (passes A1/A4/A8, fails A2 at the front)

---

## 12. Phase 4 — cross-code validation against Lezhnin 2025 (`runs/P4/`)

**The question.** Every result in Phases 0–3 is self-consistent: the operator is checked
against its own upstream, and the physics against scalings derived here. Nothing has yet
been checked against an **independent code solving different equations**. Phase 4 closes
that, by replicating the benchmark of

> K. V. Lezhnin et al., *Particle-in-cell simulations of expanding high energy density
> plasmas with laser ray tracing*, Phys. Plasmas **32**, 022701 (2025)

— which compared PSC (ray-traced PIC) against FLASH (radiation hydrodynamics) for
long-pulse laser ablation of solid aluminium, and found agreement to 20 % in `n_e`, `T_e`,
`T_i` and 10 % in flow speed.

**The extension.** The paper is a two-way comparison (FLASH ↔ kinetic PIC). We run a
**three-way** one, adding the hybrid solver in the middle:

| Run | Model | Electrons | Ions | Why it is here |
|---|---|---|---|---|
| `P4_lez_flash` | FLASH rad-hydro | fluid, conducting | fluid | the independent reference |
| `P4_lez_kin` | WarpX full PIC + ray tracing | kinetic | kinetic | the paper's PSC leg, in WarpX |
| `P4_lez_hyb` | WarpX hybrid + ray tracing | fluid (Ohm's law) | kinetic | **the leg the paper does not have** |

The hybrid leg is the scientifically new one. It sits exactly between the two published
models, so if FLASH and full PIC agree and the hybrid does not, the disagreement localises
to the electron closure — the one thing the hybrid changes. That is a sharper test of
`feature/hybrid-laser` than any run we could design from scratch.

### 12.1 The reference case, in numbers

From the paper's §II, with the quantities we will compare against:

| Quantity | Paper value | Derived here |
|---|---|---|
| Laser wavelength `λ₀` | 1.064 µm | `n_cr` = 9.848×10²⁶ m⁻³, `d_e,cr` = 0.1693 µm |
| Intensity `I₀` | 10¹³ W/cm² | **1.0×10¹⁷ W/m²** |
| Pulse | 0.9 ns flat-top + 0.1 ns linear rise | 1 ns total |
| Target | solid Al, 2.7 g/cm³, `x` ∈ [0, 50] µm | fully ionised `Z` = 13, `T_e` = `T_i` = 290 K |
| Ambient | Al vapour, 10⁻¹⁰ g/cm³ | FLASH only — PSC uses none |
| FLASH domain | 800 µm, AMR level 4, CFL 0.4 | = 110 `d_i0` |
| PSC domain | 1000 `d_e` = 100 `d_i0`, 5000 cells | 5 cells per `d_e` |
| PSC target | 4.5 `d_i0` thick, capped at `n_max` = 10 `n_cr` | real solid Al is ~700 `n_cr` |
| PSC particles | 10⁵ ppc per species **at** `n_cr` | resolves to 10⁻⁵ `n_cr` |
| Reduced params | `m_p/m_e` = 100, `m_e c²` = 60 keV | so `m_Al/m_e` = 2698 |

**The one analytic anchor worth stating up front.** The Manheimer steady-state ablation
temperature, the paper's Eq. (15), is

```
T_e,SS = 5.94 µ^(1/3) Z^(-1/3) (λ₀/1 µm)^(4/3) (I/I₁₀)^(2/3)  eV,     I₁₀ = 10¹⁰ W/cm²
```

Note **`Z^(−1/3)`, not `Z^(+1/3)`** — the exponent is negative, and a text-layer extraction
of the PDF drops the minus sign. With `µ` = 26.98, `Z` = 13, `λ₀` = 1.064 µm,
`I` = 10¹³ W/cm² this gives

```
T_e,SS = 823 eV
```

which is the horizontal dashed line in the paper's Fig. 4(b) and matches the ~800 eV `T_e`
plateau in Fig. 3(b). **Recovering 823 eV from the sign-correct formula is the cheapest
possible check that we have read the paper right, and it is a hard target for all three
runs.** The corresponding sound speed is `C_S` = 195 km/s, the proton skin depth at `n_cr`
is `d_i0` = 7.256 µm, and the hydrodynamic ion response time is

```
d_i0 / C_S = 37.2 ps      =>   the 1 ns pulse is 26.9 ion response times
```

### 12.2 The unit map — the trap in this phase

The paper carries **two different `d_i0`** and never reconciles them. Getting this wrong
silently rescales every profile.

- **In PSC's deck**, `m_p/m_e` = 100, so the proton skin depth at `n_cr` is `d_i0` = 10 `d_e`
  and the 1000 `d_e` box is "100 `d_i0`".
- **In the figures**, the top axis of Fig. 3 runs to 0.65 mm at `z/d_i` ≈ 85, i.e.
  `d_i0` ≈ 7.6 µm — the **real** proton skin depth at `n_cr`, 7.256 µm. That identification
  is what lets the paper set its "100 `d_i0`" box beside FLASH's 800 µm = 110 `d_i0`.

**Those two statements are not compatible in physical units**, and the gap between them is
exactly the mass-ratio reduction, `√(1836/100)` = **4.29**.

Our convention (`src/laserprod/units.py`) is the *real electron, light ion* one —
`m_i = mass_ratio · m_e` at the **real** `m_e`, so `d_e,cr = λ₀/2π = 0.1693 µm` always. A
1000 `d_e` box is therefore **169.3 µm of physical length**, not the 726 µm the paper's mm
axis implies. FLASH, which has no such freedom, really is 800 µm.

**Rule for this phase: compare in NORMALISED units — `(z/d_i0, t/(d_i0/C_S0))`, each code
using its OWN `d_i0` — with densities in `n_e/n_cr` and temperatures in absolute eV. Never
overlay two codes on a µm axis in this phase.**

What survives the rescaling, and is therefore the actual content of the benchmark:
`n_e/n_cr`, `T_e` and `T_i` in **eV**, the shape and integral of `P_abs`, and every
dimensionless ratio in §12.6. Temperature is the one absolutely-scaled quantity, and it is
absolute precisely because the laser pins it — which is the whole reason this benchmark
bites, and why a scale-free heater run could never do this job.

A second consequence: WarpX has **real `c` and real `m_e`** and cannot reproduce PSC's
`m_e c²` = 60 keV. We therefore match the *dimensionless* physics (`n_e/n_cr`, `T_e` in eV,
`Z`, `m_p/m_e`) and accept a different `C_S/c` (0.00279 vs PSC's 0.00813). At 823 eV the
flow is deeply non-relativistic, so `C_S/c` enters nothing but the step count — a cost
parameter here, not a physics one.

### 12.3 What must be built first (§12.0, a CODE sub-phase)

Phase 4 cannot be generated by the current tooling. Two gaps, both real:

1. **`deck.py` emits no collision block** (`grep -c collision src/laserprod/deck.py` = 0).
   The paper is explicit that collisions are load-bearing — *"auxiliary simulations with
   either collisions or laser heating turned off demonstrated drastically different plasma
   evolution"* — so `P4_lez_kin` is meaningless without them. Needs a `collisions:` schema
   block mapping to WarpX `collisions.*` (`BinaryCollision`, Coulomb, pairs `e-e`, `e-i`,
   `i-i`).
2. **`deck.py` emits no hybrid block.** `P4_lez_hyb` needs `algo.maxwell_solver = hybrid`,
   `hybrid_pic_model.electron_energy_mode = advected`, and the three laser-deposition
   hybrid swaps (`density_source = hybrid_rho`, `temperature_mode = hybrid_fluid`,
   `deposit_to = fluid`) — all of which exist in the operator but have no config path.

Both extend the existing `--verify` parse-back list, and both need tests in the style of
`tests/test_profile_columns.py`.

### 12.4 The known physics gap — no electron thermal conduction in the hybrid

`hybrid_pic_model.electron_energy_mode = conducting` **aborts as unimplemented**; the
message says so plainly: *"the energy equation is solved without a heat flux."* The
available `advected` mode integrates

```
∂T_e/∂t + u_e·∇T_e = −(2/3) T_e ∇·u_e + (2/3) S/n_e
```

— advection, compression and the laser source, and **no ∇·q_e**.

This matters more here than anywhere else in the project, because the paper's §III.C is
*entirely* about heat flux: FLASH's ablation-front structure is set by Spitzer conduction
with a Larsen flux limiter (`α_ele` = 0.06), and the paper's largest FLASH↔PSC discrepancy
is exactly the conduction-controlled region between the solid interface and the critical
surface. A hybrid run with no ∇·q_e should therefore **fail to reproduce the ablation-front
temperature profile while still reproducing the underdense rarefaction**, since the
rarefaction is advection-dominated.

That prediction is worth measuring rather than assuming, so the phase runs `advected`
first as a control. See decision **D2** in `runs/P4/README.md` for the two ways forward.

### 12.5 The runs

| Run | What it is | Cost |
|---|---|---|
| `P4_lez_flash` | FLASH 1D, `LaserSlab`-derived, paper parameters. **Deck only — we have no FLASH build.** Collaborator runs it and returns outputs to shared. | minutes (collaborator) |
| `P4_lez_kin` | WarpX 1D full PIC + ray tracing + Coulomb collisions | ~0.1–1.8 GPU-h (ppc-dependent) |
| `P4_lez_hyb` | WarpX 1D hybrid + ray tracing, `electron_energy_mode = advected` | ≪ the kinetic run (no electron macroparticles, no `ω_pe` step limit) |

Sizing for `P4_lez_kin`, from `T_total` = 26.9 `d_i0/C_S0` = 96 600 `d_e/c`:

| `dz/d_e` | CFL | cells | steps |
|---|---|---|---|
| 0.2 | 0.75 (paper) | 5000 | 644 000 |
| 0.5 | 0.35 (project default) | 2000 | 552 000 |
| 0.5 | 0.50 | 2000 | 386 000 |

and at `dz/d_e` = 0.5, CFL 0.35:

| ppc(e) at `n_cr` | particles | CPU-h | GPU-h |
|---|---|---|---|
| 500 | 0.53 M | 0.70 | 0.09 |
| 2 000 | 2.13 M | 2.79 | 0.35 |
| 10 000 | 10.7 M | 14.0 | 1.8 |

The paper's 10⁵ ppc is ~18 GPU-h and buys only the 10⁻⁵ `n_cr` tail. **Run the ppc ladder
500 → 2000 → 10000 and stop where the compared quantities stop moving** — the ladder is the
deliverable, not the largest run.

### 12.6 Acceptance — what "converge to the same effects" means

Quantitative, using the paper's own tolerances so our agreement is comparable to theirs.
All at `t` = 0.2, 0.4, 0.6, 0.8 ns, over the **underdense** region `n_e < n_cr`:

| # | Quantity | Tolerance | Source |
|---|---|---|---|
| A1 | `n_e(z)/n_cr` | 20 % | paper §III.A |
| A2 | `T_e(z)` [eV] | 20 % | paper §III.A |
| A3 | `T_i(z)` [eV] | 20 % | paper §III.A |
| A4 | `V_z(z)` | 10 % | paper §III.A |
| A5 | `P_abs(z)/n_e` deposition profile | shape + integral | paper Fig. 3(e) |
| A6 | `T_e` plateau vs `T_e,SS` = 823 eV | factor ~1; the paper's own runs exceed it late | Eq. (15) |
| A7 | critical-surface speed | `V_z(z_cr)` ≈ 0.8 `C_S` (the paper's *measured* value, not the Mach-1 SS assumption) | paper §III.B |
| A8 | rarefaction `n_e = n_cr e^(−z/C_S t)`, `V_z = C_S + z/t` | nominal agreement | Eqs. (16)–(17) |

**Explicitly not required to agree**: the region inside the solid target (`n_e` > `n_cr`).
The paper caps `n_max,PIC` at 10 `n_cr` against a true ~700 `n_cr`, so the overdense interior
is a different physical object in PIC than in FLASH, and the paper says so. Claims in this
phase are about the **ablated, underdense plasma** only.

**The hybrid-specific expectation**, stated in advance so it can be falsified: `P4_lez_hyb`
passes A1, A4, A8 (advection-dominated) and **fails A2 near the ablation front**
(conduction-dominated), while `P4_lez_kin` passes both. If the hybrid passes A2 anyway then
conduction is not setting the front at these parameters and §12.4's premise is wrong —
which is a result worth having.

### 12.7 Deliverables

- `runs/P4/README.md` — the decision register (D1–D8) and the unit map
- `runs/P4/P4_lez_flash/flash.par` + `README.md` + a collaborator-facing handoff note
- `runs/P4/P4_lez_kin/config.yaml` + `README.md`
- `runs/P4/P4_lez_hyb/config.yaml` + `README.md`
- `src/laserprod/deck.py` — `collisions:` and hybrid-solver emission, in `--verify`
- `scripts/xcode_compare.py` — reads FLASH output + both WarpX runs, emits the A1–A8 table
  and the paper's Fig. 3 / Fig. 4 analogues on the common `(z/d_i0, t/(d_i0/C_S0))` axes
- `RESULTS.md` entry with the A1–A8 verdicts

### 12.8 Risks specific to this phase

1. **Collision rates under a reduced mass ratio.** PSC implements a *special* correction to
   match `e-i` and `i-i` rates when `m_p/m_e` and `c` are reduced (their Ref. 47). WarpX's
   `BinaryCollision` is not known to have an equivalent. If it does not, the kinetic run's
   transport is distorted in a way that is invisible unless checked — so **reproduce the
   paper's Appendix B/C tests first**: `e-i` thermalisation against their Eq. (B1) in a
   2 `d_i` periodic box, and the conductivity test. Cheap, and it is the gate on trusting
   `P4_lez_kin` at all.
2. **The initial-plasma problem.** The paper does not start PSC from a cold solid — it
   starts from the FLASH `t` = 0.1 ns snapshot, because a sharp solid edge gives either
   `n_e ≫ n_cr` or `n_e` = 0 along a ray and the tracer fully reflects. Our runs inherit
   this exactly. See decision **D1**.
3. **No pulse ramp.** The operator expresses a pulse only through
   `intervals = start:stop:period`, i.e. flat-top. The paper's 0.1 ns linear rise cannot be
   represented. Since PSC starts at `t` = 0.1 ns — *after* the ramp — this is consistent for
   the WarpX legs, but the FLASH deck must keep the ramp or its snapshot will not match.
4. **`lnΛ` is a global constant in the paper.** PSC applies a single `lnΛ` box-wide; our
   operator computes it per cell (the `lnLambda` column). The paper flags this as a source
   of its FLASH↔PSC heat-flux discrepancy. Our per-cell treatment is *better*, so we should
   expect to differ from PSC here and agree with FLASH better. Do not "fix" this by forcing
   a global value without recording both.
