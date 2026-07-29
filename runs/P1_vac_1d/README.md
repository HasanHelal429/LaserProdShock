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

Scaled from `P0_thick_open` (133 280 particles, 24 000 steps, 3.4 min at 4 threads):
particles ×3.15, steps ×4.27 ⇒ ×13.4 ⇒ **~25 min at 8 CPU threads**. To be replaced by the
measured number from `progress.log`.

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

- `media/P1_vac_1d/checks.png` — pre-run: initial density from the deck's own `density_function`, predicted `K(z)` and `tau(z)` at the group `T_e`, and the gate table.

## Result

*(not run yet — awaiting approval)*

## Retracted

Nothing.
