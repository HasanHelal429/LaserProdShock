# P1_vac_1d — the Phase-1 reference ablation (1D, vacuum)

**Phase.** 1, `TEST_PLAN.md` §7.1
**Question.** Does the operator, coupled to PIC, ablate a target the way ablation physics
says it should — and **does absorption ever actually shut off?**

**Why this run exists, and why it is 4.3× longer than any Phase-0 run.** Phase 0 was about
boundaries; it nevertheless measured the thing Phase 1 has to explain. In `P0_thick_open`,
`f_abs` rose to **1.000** at 0.056 ps, collapsed to a noisy **0.05–0.10 plateau** within
0.1 ps — and then *stayed there*, with `E_abs` still rising **linearly** at the end of the
run (2.35 ps), at 60 % of its early rate. 50 % of the coupled energy arrived after 0.89 ps.

That is not the self-limiting shutoff `TEST_PLAN.md` §2.3 assumed. It is **drive-limited
coupling**: `E_abs ≈ f_abs·I₀·t` at a quasi-steady plateau, with no capacity ceiling in
sight. If that persists, **H2 is false** (coupled energy is *not* intensity-independent)
and H4 — the plan's most consequential prediction, that low intensity drives shocks better
— loses its mechanism. §2.3 already flagged this as the "known tension" (H1–H2 predict a
factor 2.4 for the `Z_eff·lnΛ` change; 16× was measured). This run is built to settle it.

**Expected.**
1. **`f_abs(0)` jumps from 0.248 to ~1.000, because the corona changes absorption REGIME.**
   This is the sharpest prediction the run makes, and it is not merely "more absorption".
   Integrating τ along the ray to the turning point (never through the overdense interior —
   the ray reflects) at the group `T_e`:

   | | `L_n` = 15 (`P0_thick_open`) | **`L_n` = 60 (here)** |
   |---|---|---|
   | turning point | +10.2 d_e | **+38.2 d_e** |
   | τ to the turning point | **0.14 — optically THIN** | **5.60 — optically THICK** |
   | τ = 1 reached at | *never*, before turning | **+53.6 d_e** |
   | predicted `f_abs(0)` | 0.244 | **1.0000** |
   | measured `f_abs(0)` | **0.248** | *this run* |

   At `L_n` = 15 the beam crosses a thin corona, reflects off the critical surface and
   leaves — absorption is **turning-point dominated**. At `L_n` = 60 it is extinguished at
   +53.6 d_e, **15.3 d_e short of the turning point**: a pure **coronal absorber** that
   never reaches the critical surface at all. The turning point becomes irrelevant to the
   drive, which also means gate G4's `ray_cfl` sensitivity (a turning-point effect) should
   *weaken* here.

   Note the predictor reproduced Phase 0's measured `f_abs(0)` (0.244 predicted, 0.248
   measured) — well inside the 10.4 % 1σ seed noise on that quantity, so treat it as
   consistency, not as three-digit accuracy.
2. Consequently `f_abs` should **start saturated and only fall.** In Phase 0 it *rose*
   from 0.248 to 1.000 over 0.056 ps as the heated corona expanded into a longer absorbing
   path; starting at 1.000 there is no room for that transient, so the early history should
   look qualitatively different — a plateau then a decay, with no initial rise.
3. **The decisive measurement:** does `E_abs(t)` roll over within 10 ps? 10 ps is
   **1.1 rear-rarefaction slab crossings** (`w_t/c_s` = 9.1 ps), i.e. long enough for the
   whole slab to be processed. If `E_abs` is still linear at 10 ps, H2 is dead and Phase 3A
   must be re-planned around a drive-limited law.
4. Deposition sits **entirely in the coronal gradient, with nothing at the turning point** —
   the direct consequence of (1). Checked on the **step-0** profile dump, before the kicks
   move anything: the per-cell `H(z)` should peak near z ≈ +54 d_e and be ~zero at the
   critical surface (+38.2 d_e) and everywhere below it.
5. `v_p ≈ α c_s` with α ≈ 1–3 (H3), and `v_p` measured from both the ion front and the bulk.
6. The energy budget closes (G6) **once boundary losses are subtracted** — see Hazards.

**Falsified by.** `f_abs` never reaching ~1 (the predictor and the operator disagree about
the corona); the τ = 1 surface not where WKB puts it; a piston with no `c_s` scaling; or
a total particle-energy gain that the laser-off control `P1_vac_1d_off` can account for —
which would mean the "ablation" is grid heating.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
                    #######~~~~~~~~~~                                   
      ^                                                                ^
      open                                                          open
      z = -300                                                  z = +700

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 2000 cells, dz = 0.5 d_e, dt = 0.09783 fs, 102400 steps = 10.02 ps
```

## Setup

Parent: **`P0_thick_open`**. Three changes, each deliberate.

**1. `L_n` 15 → 60 d_e — this closes the last gap to the intended setup.** `P0_thick_open`
held the coronal scale length at 15 d_e on purpose, so that thickness was the only variable
under test, and its README recorded the leftover as a Phase-1 item: *"matching the upstream
`L_n/w_t` = 0.75 would put it at 60 d_e … it changes where the τ = 1 surface sits."* Done
here. With `w_t` = 80 d_e that is `L_n/w_t` = **0.75**, exactly the upstream
`run_laser_shock` ratio, and it reproduces the upstream's coronal mass split: the corona now
holds **40 % of the target's areal electron density** (79.4 of 200.2 n_cr·d_e), against 14 %
at `L_n` = 15. Consequences, computed from the deck's own density expression:

| | `L_n` = 15 (Phase 0) | **`L_n` = 60 (here)** |
|---|---|---|
| critical surface, above the face | +10.2 d_e | **+38.2 d_e** |
| absorbing path before the turning point | 10.2 d_e | **38.2 d_e** |
| corona share of areal `n_e` | 14 % | **40 %** |
| initial plasma edge (`density_min`) | +53 d_e | **+182 d_e** |

(Critical surface = where the **total** density the ray sees reaches `n_cr`. In Phase 0 the
0.06 `n_cr` ambient contributes, moving it from the target-only 9.6 to 10.2 d_e; this run is
in vacuum, so target-only and total coincide.)

**2. Vacuum, no `B₀`** (`plasma.ambient: null`, `field.orientation: none`) — §7.1. Two
species only, so the ablation scalings can be measured with nothing else in the box. Note
this also **removes the Phase-2 ambient-drain blocker** from consideration: there is no
ambient to drain.

**3. Duration 2.35 → 10.02 ps** and **ppc 200 → 400** (G5 bias bound 0.63 % → 0.31 %).

**The rear boundary is deliberately NOT truncated, and that is not a reversal.** Phase 0
verified truncating at the target's rear face with `open` at both 20 and 80 d_e thickness
(total `p_z` to −0.54 %), and that finding stands. It does not apply *here* for two
independent reasons:

- It was validated over **2.35 ps = 26 %** of a slab crossing. This run is 10 ps = **110 %**:
  the rear rarefaction traverses the whole slab, the two faces couple, and the validated
  window simply does not cover it.
- **In vacuum the cushion is nearly free.** `density_min = 1e-4·n_t` confines particles to
  z ∈ [−80, +182] d_e — **525 of 2000 cells**. The other 1475 cells are empty field cells,
  and in 1D the field solve is a rounding error next to the particle push. Truncation saved
  15 % of cells in Phase 0 *because the ambient filled the cushion at 48 ppc*; with no
  ambient there is nothing to save, so we buy a genuine free surface at both faces instead.

So: 220 d_e of vacuum behind the target (rear expansion at ~3 c_s ≈ 26 d_e/ps reaches the
wall at ~8.3 ps, near the end) and 518 d_e ahead of the initial plasma edge (the bulk plume
front would need ~20 ps to reach it). The **bulk stays in the box for the whole run**; only
the runaway tail leaves, which is exactly the population §7.1 wants measured.

## Hazards specific to this run

- **Vacuum + `open` is a charge-imbalance geometry.** Electrons outrun ions and are
  *absorbed* at the wall while their ions stay, so the box slowly charges positive against a
  `pec` field boundary. The ambipolar sheath that drives the expansion is physical; a
  boundary-pinned potential is not. This is the main reason for the generous cushions, and
  it is the first thing to check if the plume misbehaves. No Phase-0 run tested it — they all
  had an ambient everywhere.
- **G6 needs the boundary-loss term.** Phase 0 established the raw tracer-vs-particle gap
  reads +218 % / +235 % at 5.8 % / 17 % particle loss. Quote the loss fraction beside the
  closure, always.
- **Quote `E_abs`, never `f_abs(0)`,** when comparing runs: `f_abs(0)` carries a 10.4 % 1σ
  from RNG seed alone (`studies/fabs_noise/`).

## Cost

2000 cells (525 particle-bearing) × 400 ppc × 2 species = **420 000 macroparticles**,
102 400 steps → 10.018 ps.

**Measured** on this deck (2000 steps, diagnostics off, so this times the push):

| backend | 2000 steps | projected 102 400 steps |
|---|---|---|
| CPU, 8 threads (`build/`) | 117.9 s | **100.6 min** |
| **GPU, 1× RTX 4070 (`build_cuda1d/`)** | **9.3 s** | **7.9 min** |

**12.7× on the GPU**, which is what this run used. Note the *estimate* by scaling from
`P0_thick_open` (particles ×3.15, steps ×4.27 ⇒ ×13.4 ⇒ ~25 min at 8 threads) was **wrong by
4×** — the real CPU cost is 100.6 min. Cell count matters much more than that scaling
allowed for (2000 cells vs 440), so **benchmark rather than scale** when the grid changes
size. See `progress.log` for the run's own wall-clock record.

## Gates

`make_inputs.py --check`: **4 pass, 0 warn, 0 fail**, 2 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial; hits 2 at 130.6 n_cr) | **pass** (budget 1.2) |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — a measurement, made meaningful by G3 |
| G3 laser-off control | `P1_vac_1d_off` (exists; deck differs *only* in `intensity`) | **pass** |
| G4 `ray_cfl` check | 0.25, ladder declared (`studies/exit_overshoot`) | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc, `local` mode; bias bound ≤ 0.31 % | **pass** (budget 400) |
| G6 energy closure | — | post-run; **quote the boundary-loss fraction with it** |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm, same as every Phase-0 run | info |

## Media

- `media/P1/P1_vac_1d/checks.png` — initial density from the deck's own `density_function`, predicted `K(z)`/`tau(z)` at the group `T_e`, and the gate table
- `media/P1/P1_vac_1d/fields_lineouts.png` — `n_e(z)` profiles at selected times
- `media/P1/P1_vac_1d/fields_streak.png` — `n_e` and `E_z` as (z,t) maps, with the laser history on the same time axis
- `media/P1/P1_vac_1d/gates.png` — the G1-G7 gate panel on its own
- `media/P1/P1_vac_1d/laser_history.png` — `f_abs(t)`, cumulative `E_abs(t)`, `Tlocalfrac(t)` - **the H2 verdict is in the middle panel's computed title**
- `media/P1/P1_vac_1d/laser_profile.png` — per-cell `n_e` and `P_abs` from the **step-0** dump - where the energy actually lands
- `media/P1/P1_vac_1d/movie_fields.mp4` — evolving `n_e(z)` lineouts with the laser history tracking below
- `media/P1/P1_vac_1d/movie_phase.mp4` — target-ion phase space over the run
- `media/P1/P1_vac_1d/phase_space.png` — target-ion (z, u_z) - the arbiter
- `media/P1/P1_g3/compare.png` — the **G3 subtraction**: this run against `P1_vac_1d_off`

## Result

Ran **102 400/102 400 steps = 10.018 ps in 8 min** on one RTX 4070 (GPU 0), zero errors,
`--verify` OK, gates 4 pass / 0 warn / 0 fail.

### The two headline results

**1. `H2` IS FALSIFIED. Coupling is drive-limited, not capacity-limited.**
This was the decisive measurement, and the answer is unambiguous: **`E_abs` never rolls
over.** `f_abs` falls from 1.000 to a **plateau near 0.23** — not to zero — and the drive
keeps delivering for the remaining 97 % of the run:

| | value |
|---|---|
| `E_abs` final | **2.4626×10⁶ J/m²** — **11.5× `P0_thick_open`'s 2.135×10⁵** |
| fraction of the incident energy absorbed | **24.6 %** (mean `f_abs` = 0.2458) |
| late/early `dE/dt` | **0.41** (0.665 by first-vs-last quarter) — *not* 0 |
| 50 % / 90 % / 99 % of `E_abs` delivered by | **3.98 / 8.86 / 9.90 ps** |

Energy is still arriving at essentially a constant clip at the final step. So
`E_abs ≈ f_abs·I₀·t` with `f_abs` quasi-steady, i.e. **`E_abs ∝ I₀`** — the opposite of H2's
"coupled energy is intensity-independent". §2.3's "known tension" (H1–H2 predict a factor
2.4 for the `Z_eff·lnΛ` change; 16× was measured) is now explained: the shutoff picture is
simply the wrong model, because absorption floors instead of switching off.

**Consequence for the campaign: H4 loses its stated mechanism.** H4 — "low intensity may
drive shocks better", the plan's most consequential prediction — rests on H2, i.e. on
raising `I₀` shortening the drive rather than strengthening it. With `E_abs ∝ I₀` and a
plateau that does not close, raising `I₀` raises the coupled energy *and* keeps the drive on.
**Phase 3A must be re-planned around a drive-limited law**; there may still be an optimum
`I₀`, but not for the reason §2.3 gives. `TEST_PLAN.md` §2.3 and §9.1 updated.

Note the reported "shutoff (½ peak) = 0.2505 ps" is a real crossing but **not a shutoff in
any physical sense** — it is the fall onto the plateau. Quoting `t_s` from a half-peak
crossing is misleading for this configuration; quote the plateau level and `dE/dt` instead.

**2. The ablation is 99.93 % laser-driven — NOT grid heating (gate G3).**

| | driven | laser-off control | control / driven |
|---|---|---|---|
| particle-KE gain | **+2.4212×10⁶ J** | **−1 696 J** | **−0.07 %** |
| weight lost at the boundaries | 0.0104 % | 0.0000 % | — |

The control's *net* particle energy change is **negative and four orders of magnitude
smaller** than the driven gain, despite `dz/λ_D` = 61. Its internal shuffle is physical, not
numerical: electrons **−51.4 kJ**, ions **+49.7 kJ** — ambipolar electron→ion transfer as a
51 eV corona relaxes, summing to ≈ 0. **G2 is now bounded**, and this is the check the
retracted upstream shock claim never had.

### Gate G6 — the first clean energy closure in this project

| | value |
|---|---|
| `E_abs` (tracer, grid-heating-immune) | 2.4626×10⁶ J |
| particle-KE gain + field-energy gain | 2.4445×10⁶ J |
| **raw gap** | **−0.74 %** |
| gap after subtracting the control | −0.67 % |
| **boundary weight loss (quote beside it)** | **0.0104 %** |

Phase 0 could only report +218 % / +235 % at 5.8 % / 17 % particle loss. **The generous
vacuum cushions are what bought this**: 0.68 % of *macroparticles* left the box but they
carried only **0.0104 % of the weight** (the escaping population is the tenuous corona tail),
so the closure is meaningful rather than swamped. The macroparticle-count and weight loss
figures differ by 65×; quote the **weight**.

### Predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | `f_abs(0)`: 0.248 → **1.000** (regime change to optically thick) | **CONFIRMED** — measured **1.0000** |
| 2 | starts saturated, only falls (no initial rise) | **CONFIRMED** — peak 1.000 at 0.034 ps, then monotone decay to plateau |
| 3 | does `E_abs` roll over in 10 ps? | **NO** — H2 falsified (above) |
| 4 | deposition entirely coronal, **nothing** at the turning point | **CONFIRMED** — see below |
| 5 | `v_p ≈ α c_s`, α ≈ 1–3 (H3) | **not confirmed; test is not yet fair** — see below |
| 6 | G6 closes | **CONFIRMED** — −0.74 % |

**Prediction 4, from the step-0 profile dump, is confirmed to the cell.** Predicted τ = 1 at
+53.6 d_e; measured peak deposition at **+53.8 d_e** (where `n_e` = 0.672 `n_cr`):

- deposition extends **z = +38.2 → +182.3 d_e** — it stops *exactly* at the critical surface;
- **0.000 % of `P_abs` at or below the critical surface** (+38.2 d_e);
- the densest cell that absorbs anything is at `n_e` = **0.9990 `n_cr`** — right up to, never past;
- 50 % / 90 % / 99 % of `P_abs` lands by z = +57.3 / +44.2 / +38.8 d_e marching from +z.

So this configuration is a **pure coronal absorber**: the ray is extinguished ~15 d_e before
the critical surface and the turning point plays no role in the drive. `media/P1/P1_vac_1d/laser_profile.png`
shows it directly. This also means **G4's `ray_cfl` sensitivity should be weaker here than in
Phase 0**, since that is a turning-point effect — worth confirming, not yet measured.

### The piston, and why H3 is not yet fairly tested

| measure of target-ion `v_z` at 10 ps | driven | control |
|---|---|---|
| **weight-weighted mean over forward-moving ions** | **0.00144 c** | 0.00089 c |
| unweighted 99.9th percentile ("the front") | **0.0267 c** | 0.0091 c |

With `c_s` = 0.003149 c from the implied `T_e,ab` = 0.5068 keV (energy per target ion
0.7602 keV), the bulk gives **α ≈ 0.46** — *below* H3's α ≈ 1–3. **But this is a lower bound,
not a refutation**, for a concrete reason: at `c_s` = 5.6 d_e/ps the rarefaction has crossed
only ~**70 %** of the 80 d_e slab in 10 ps, so ~30 % of the target mass is still cold and
unmoved and is being averaged into the "piston". A fair H3 test has to restrict to the
**ablated** population — which is exactly what `plot_ablation.py` (§3, not yet built) is for.
**H3 is therefore open, not falsified**, and that tool is the next Phase-1 item.

Note also the 19× spread between the bulk (0.00144 c) and the front (0.0267 c): the fast
population is real but carries little mass. Energy partition at 10 ps is
**77.4 % electrons / 22.6 % ions** (1.8729×10⁶ / 5.4828×10⁵ J), so only ~23 % of the coupled
energy is in ion motion — the drive efficiency Phase 2 will care about.

### Numerics

`Tlocalfrac` rose **0.432 → 1.000** and saturates at 1.000 by ~1.5 ps: at 400 ppc every
absorbing cell has a *measured* `T_e`, never the floor, so G5's bias bound (≤ 0.31 %) is real
rather than nominal. Raw `E_z` rms is 1.2×10⁹ V/m at `dz/λ_D` = 61 — mostly grid noise, which
is why the streak is boxcar-smoothed over 9 cells and the raw rms is quoted on the panel.

**Domain sizing was well judged.** The streak shows the rear expansion reaching the `pec`
wall at z = −300 at **t ≈ 7.5 ps** against a predicted ~8.3 ps, and the bulk plume never
approaches z = +700. The bulk stayed in the box for the whole run, which is what made the
G6 closure possible.

## Retracted

Nothing.
