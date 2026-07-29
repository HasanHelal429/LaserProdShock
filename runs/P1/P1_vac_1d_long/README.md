# P1_vac_1d_long — the reference ablation run 10× longer (1D, vacuum, 100 ps)

**Phase.** 1, `TEST_PLAN.md` §7.1 and §2.4
**Question.** `P1_vac_1d` showed absorption **floors** at `f_abs` ≈ 0.23 instead of shutting
off, with `E_abs` still rising linearly at the final step. That established the drive does not
shut off *within 10 ps*. **Does it ever?**

**Why 10 ps was not enough, and why 100 ps is the right number.** 99 % of `P1_vac_1d`'s
`E_abs` arrived by 9.90 ps of a 10.02 ps run — the measurement was truncated by the run, not
by the physics. Three independent clocks say 100 ps:

- **13 gyroperiods** at the Phase-2 reference `ω_ci0⁻¹` = 7.61 ps. Schaeffer needs
  `t*` ≈ 1, 2.5, 5 `ω_ci0⁻¹` (7.6 / 19 / 38 ps) for shock formation, so **Phase 2 needs the
  piston to still be driven at ~38 ps.** Whether the drive survives that long is the single
  most consequential thing Phase 1 can hand to Phase 2.
- **~7 rear-rarefaction slab crossings** (`w_t/c_s` = 14.3 ps at the measured
  `T_e,ab` = 0.507 keV). At 10 ps only ~70 % of one crossing had happened, so ~30 % of the
  slab was still cold — which is exactly why **H3 could not be fairly tested**. With the whole
  target processed, the bulk *is* the ablated population.
- **The rarefaction must eventually take the peak below `n_cr`**, at which point the beam
  punches straight through, there is no turning point at all, and absorption should collapse.
  100 ps is long enough to look for that.

**Expected.**
1. **The plateau persists far beyond 10 ps, and `E_abs` reaches ~2×10⁷ J/m².** If `f_abs`
   held at 0.23 for the whole run, `E_abs` = 0.23 × 10¹⁸ × 100.2 ps = **2.3×10⁷ J/m²**, ~9.4×
   the 10 ps value. Anything much *below* that means the plateau does close, and **the fall-off
   time is then the most important number in Phase 1** — it is the drive duration Phase 2 gets.
2. **The target rarefies below `n_cr` at some point**, and `f_abs` should drop sharply when it
   does — a qualitatively different event from the initial 1.000 → 0.23 fall (which was the
   corona thinning, not the peak going underdense). Watch peak `n_e` and `f_abs` together.
3. **H3 becomes testable.** With ≥ 1 slab crossing complete, the weight-weighted bulk is the
   ablated population, so α = `v_p/c_s` is a fair number rather than the α ≥ 0.46 lower bound
   the 10 ps run could offer.
4. **G6 still closes**, because the domain was sized from measured drift rates (below). Weight
   loss should stay ≲ 1 %; the 10 ps run lost 0.0104 %.

**Falsified by.** `E_abs` rolling over *without* the peak density going underdense (that would
mean a mechanism neither the shutoff picture nor the plateau picture describes); or a weight
loss large enough to void G6, which would mean the domain scaling below is wrong.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
                                         ##~~                           
      ^                                                                ^
      open                                                          open
      z = -3000                                                  z = +2400

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 10800 cells, dz = 0.5 d_e, dt = 0.09783 fs, 1024000 steps = 100.2 ps
```

## Setup

Parent: **`P1_vac_1d`**. The target, laser, `dz`, `cfl`, ppc and boundaries are **identical**;
only the duration and the domain change, so this is a clean extension rather than a new run.

**1. Duration ×10: 102 400 → 1 024 000 steps = 10.018 → 100.18 ps.**

**2. Domain 2.7× larger: [−300, +700] → [−3000, +2400] d_e** (2000 → 10 800 cells).
**Sized from measured drift, not guessed.** `P1_vac_1d`'s ion-weight quantiles were tracked
across all 21 phase dumps; over the last few ps they move at:

| ion-weight quantile | drift rate | extrapolated to 100 ps |
|---|---|---|
| 1 % (rear of the bulk) | −14.3 d_e/ps | −1 510 |
| 99 % (front of the bulk) | +9.7 d_e/ps | +1 060 |
| 0.1 % / 99.9 % (tails) | −20 / +13 d_e/ps | −2 100 / +1 450 |
| 0.01 % (extreme rear) | −28 d_e/ps | −2 880 |

So [−3000, +2400] holds **99.9 % of the ion weight for the full 100 ps** with margin. The
0.01 % extreme tail will still leave — that is expected and cheap, and the weight-loss
fraction is the number to quote beside G6. **This is why the domain had to grow with the
duration**: `P1_vac_1d`'s rear expansion already reached its wall at t ≈ 7.5 ps, so simply
raising `max_step` on the old domain would have bled the plume into the boundary for 90 % of
the run and voided the energy budget.

Extra cells are affordable for the reason recorded in `CLAUDE.md`: `density_min = 1e-4·n_t`
still confines particles to z ∈ [−80, +182] at t = 0, so the macroparticle count is
**unchanged at 420 000** and the added 8 800 cells are empty field cells.

**3. Diagnostics scaled by 10× so the figure count is unchanged**, not the data volume:
`plotfile` 102 400, `field` 12 800 (80 frames), `phase` 51 200 (21 dumps), `reduced` 2 560.

**`laser.intervals` stays at 10 — it is NOT a diagnostic.** It is the deposition cadence, and
the kick amplitude goes as `√(H·Δt)` with `Δt = intervals·dt`, so changing it would change the
physics. The consequence is 102 400 `LASERDEP` lines in `run.log` (10× more), which is only a
parsing cost.

## Hazards specific to this run

- **The vacuum + `open` charge-imbalance concern from `P1_vac_1d` now has 10× longer to
  develop.** Electrons are absorbed at the wall while their ions remain, charging the box
  positive against a `pec` field boundary. It was benign at 10 ps (G6 closed to −0.74 %); it is
  the first thing to check if the late-time plume misbehaves. The larger domain helps.
- **Grid heating gets 1.024 million steps to accumulate**, which is why this run has its **own**
  10× control (`P1_vac_1d_long_off`) — the 10 ps control cannot bound a 100 ps run.

## Cost

10 800 cells, 420 000 macroparticles (unchanged), 1 024 000 steps → 100.18 ps.

**Measured** on this deck: 4 000 steps in 28.7 s on one RTX 4070 ⇒ ~123 min projected.
**Actual: 3 h 45 m** (control 3 h 10 m) — 1.8× the projection, because the host was
CPU-saturated by unrelated jobs (16 `flash4` processes plus an 8-thread CPU WarpX = 2882 %
demand on 32 cores). A CUDA run is latency-bound on a single host thread issuing kernel
launches, so when that thread is preempted the GPU idles: utilisation fell 71 % → 53 % and
power sat at 47–56 W of a 200 W cap. **Benchmark numbers here assume an otherwise idle host.**

There is also a genuine, physical component: the plume spread from 526 to 10 800 occupied
cells (20×) while the particle count stayed flat, so particle→grid deposition scatters over
20× the memory footprint and locality degrades. `warpx_rate` rose 0.0070 → 0.0132 s/step in
the driven run and 0.0062 → 0.0111 in the control — **it slows even with no laser**, which is
how the two causes were separated. Roughly 1.5× physics × 1.3× contention.
**`warpx.sort_intervals` is the fix worth benchmarking** for future GPU runs with expanding
plumes: `CLAUDE.md`'s "sorting is neutral-to-negative" note is an inherited *CPU* result and
should not be assumed to hold on the device.

For the record on grid scaling: at t = 0 the step cost was 7.19 ms at 10 800 cells against
4.70 ms at 2 000, so the 5.4× cell increase cost only **1.53×** — field work in 1D is real but
sub-linear against the particle push. Both runs went on their own GPU concurrently.

## Gates

`make_inputs.py --check`: **4 pass, 0 warn, 0 fail**, 2 info, 1 post-run — identical to
`P1_vac_1d`, since none of the gate inputs (`dz`, `cfl`, densities, ppc) changed.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial; hits 2 at 130.6 n_cr) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — bounded by G3 |
| G3 laser-off control | `P1_vac_1d_long_off`, same 100.18 ps | **pass** |
| G4 `ray_cfl` check | 0.25, ladder declared | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc; bias bound ≤ 0.31 % | **pass** |
| G6 energy closure | — | post-run; **quote the weight-loss fraction with it** |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm, as every run in this project | info |

## Media

- `media/P1/P1_vac_1d_long/checks.png` — initial density from the deck's own `density_function`, predicted `K(z)`/`tau(z)`, and the gate table
- `media/P1/P1_vac_1d_long/fields_lineouts.png` — `n_e(z)` profiles at selected times
- `media/P1/P1_vac_1d_long/fields_streak.png` — `n_e` and `E_z` as (z,t) maps over 100 ps — the plume filling the domain from ~55 ps is visible here
- `media/P1/P1_vac_1d_long/gates.png` — the G1-G7 gate panel on its own
- `media/P1/P1_vac_1d_long/laser_history.png` — **the headline figure**: `f_abs(t)` with a running median showing the plateau ending abruptly at ~30 ps, cumulative `E_abs(t)`, and `Tlocalfrac(t)`
- `media/P1/P1_vac_1d_long/laser_profile.png` — per-cell `n_e` and `P_abs` from the step-0 dump — deposition entirely coronal
- `media/P1/P1_vac_1d_long/movie_fields.mp4` — evolving `n_e(z)` lineouts with the laser history tracking below
- `media/P1/P1_vac_1d_long/movie_phase.mp4` — target-ion phase space over the full 100 ps
- `media/P1/P1_vac_1d_long/phase_space.png` — target-ion (z, u_z) — note the percentile front is boundary-truncated late; use the weighted bulk
- `media/P1/P1_long_g3/compare.png` — the **G3 subtraction**: this run against `P1_vac_1d_long_off`

## Result

Ran **1 024 000/1 024 000 steps = 100.18 ps in 3 h 45 m** on GPU 0 (slower than the 123 min
benchmark because the host was CPU-saturated by unrelated jobs — see Cost). Zero errors,
`--verify` OK, gates 4 pass / 0 warn / 0 fail.

### The headline: the plateau DOES close, and the target going underdense is why

**All four expectations were confirmed, including the mechanism.** The drive is not
capacity-limited (H2's picture) and it is not an indefinite plateau either — it holds, then
decays when the peak density falls through `n_cr` and the turning point disappears:

| t [ps] | mean `f_abs` | `dE/dt` [J/m²/ps] | peak `n_e`/`n_cr` |
|---|---|---|---|
| 0–10 | 0.256 | 2.27×10⁵ | 1.54 |
| 10–20 | 0.230 | 2.32×10⁵ | 1.33 |
| 20–30 | **0.274** | 2.70×10⁵ | 0.93 ← **crosses `n_cr` at 28.8 ps** |
| 30–40 | 0.189 | 1.81×10⁵ | 0.40 |
| 40–50 | 0.107 | 1.06×10⁵ | 0.25 |
| 60–70 | 0.065 | 6.44×10⁴ | 0.15 |
| 90–100 | **0.044** | **4.39×10⁴** | 0.090 |

**Peak `n_e` crosses `n_cr` at t = 28.8 ps, and that is exactly where the plateau breaks.**
The smoothed `f_abs` is at 0.90× its plateau by 20 ps, 0.75× by 34 ps, **half by 41.6 ps** and
a quarter by 68.9 ps. `media/P1/P1_vac_1d_long/laser_history.png` shows the plateau ending
abruptly at ~30 ps — the running-median overlay makes it unmistakable.

**So there is a real drive-decay timescale, ~40 ps, and it is set by hydrodynamics (the
rarefaction thinning the target below critical), not by a shutoff temperature.** This is the
number Phase 2 needs, and it is *right at the edge* of what Schaeffer requires: formation
wants drive at `t*` ≈ 5 `ω_ci0⁻¹` = 38 ps, and `f_abs` is down to ~0.19 → 0.11 there.

| | value |
|---|---|
| `E_abs` final | **1.3486×10⁷ J/m²** (5.48× the 10 ps run's, for 10× the time) |
| if the 0.234 plateau had held to 100 ps | 2.348×10⁷ J/m² — so it delivered **57 %** of that |
| overall absorbed fraction of incident energy | **13.5 %** (was 24.6 % over 10 ps) |
| `f_abs` peak → final | 1.0000 → **0.0421** |
| late/early `dE/dt` | **0.23** — decaying, but not extinguished |

**H2 remains falsified, and the refinement is important**: `E_abs` is neither
intensity-independent (H2) nor unbounded (the 10 ps reading in isolation). It is
`f_abs(t)·I₀·t` with `f_abs` set by the target's *hydrodynamic* state. `TEST_PLAN.md` §2.4
stands; the drive-duration law it asks Phase 3A to find now has a candidate mechanism.

### H3 is CONFIRMED — α ≈ 1.5–2.4

This is what the run was built for, and the 7 slab crossings delivered it. The bulk has
**saturated**, so α is a measurement rather than a lower bound:

| t [ps] | bulk (fwd, weight-weighted) | rms (weighted) |
|---|---|---|
| 25.0 | 0.00353 c | 0.00431 c |
| 50.1 | 0.00540 c | 0.00651 c |
| 75.1 | 0.00597 c | 0.00741 c |
| **100.2** | **0.00622 c** | **0.00774 c** |

`c_s` must come from the **measured** electron energy, not the implied `T_e,ab`: 66 % of the
coupled energy is in ions by 100 ps, so `laser_report`'s implied `T_e,ab` = 2.775 keV (which
assumes it is all electron thermal) is an upper bound and gives a spuriously low α. From
`<KE_e>` = 822 eV ⇒ **`T_e` = 548 eV ⇒ `c_s` = 0.00327 c**:

| measure | α = `v_p`/`c_s` |
|---|---|
| control-subtracted bulk | **1.52** |
| bulk forward, weighted | **1.90** |
| rms, weighted | **2.36** |
| *(against the implied `T_e,ab` — a lower bound)* | *0.84 – 1.05* |

**α ≈ 1.5–2.4, squarely inside H3's predicted 1–3.** The 10 ps run's α ≥ 0.46 was a lower
bound exactly as diagnosed, and the extra crossings closed the gap. Since `<KE_e>` includes
directed electron motion, `T_e` = 548 eV is itself an upper bound, so these α are still mild
*lower* bounds.

### Drive efficiency: the ion share triples

| t [ps] | `E_e` [J] | `E_i` [J] | ion share | `T_e` [eV] |
|---|---|---|---|---|
| 10.0 | 2.37×10⁶ | 1.00×10⁶ | 29.7 % | 293 |
| 50.1 | 5.06×10⁶ | 6.15×10⁶ | 54.9 % | 625 |
| **100.2** | 4.38×10⁶ | **8.42×10⁶** | **65.8 %** | 548 |

**62 % of the coupled energy ends up in ions** (8.42×10⁶ of 1.349×10⁷ `E_abs`) against 22.6 %
at 10 ps — the ablation converting absorbed electron heat into directed ion motion, which is
the quantity Phase 2 actually spends. `T_e` peaks near 625 eV at ~50 ps then *falls* as
expansion cools it and energy transfers to ions.

### Gate G3 holds at 10× the steps — grid heating does not accumulate

| | driven | laser-off control | ratio |
|---|---|---|---|
| net particle-KE gain | **+1.1975×10⁷ J** | **−7 962 J** | **−0.066 %** |
| weight lost | 1.1405 % | **0.0014 %** | — |

Essentially identical to the 10 ps run's −0.07 %, over **ten times the step count**. That
settles the worry that finite-grid heating would creep in over 1.024 M steps: it does not.
The control's internal split is the same ambipolar signature, 4× larger but still cancelling
(electrons −221.8 kJ, ions +213.9 kJ → net −8.0 kJ), not the shared net *gain* that grid
heating would produce.

### Gate G6: −9.56 % raw, and the deficit is fully accounted for

| | value |
|---|---|
| `E_abs` (tracer) | 1.3486×10⁷ J |
| particle-KE + field gain | 1.2196×10⁷ J |
| **raw gap** | **−9.56 %** |
| **boundary weight loss** | **1.1405 %** |

Worse than the 10 ps run's −0.74 % at 0.0104 %, **as flagged in advance** — and it is
boundary loss, not a violation. The arithmetic is self-consistent: the missing
1.29×10⁶ J is 9.6 % of `E_abs`, carried out by 1.14 % of the mass, i.e. the escaping
population has ~8.4× the mean specific energy — precisely a fast runaway tail. The sign is
right too (particles+field hold *less* than `E_abs`, because WarpX does not report energy
carried out by absorbed particles).

**The loss is entirely late**, so there is a clean window for strict budgeting:

| t [ps] | 25.0 | 50.1 | 75.1 | 100.2 |
|---|---|---|---|---|
| weight lost | **0.0000 %** | 0.0127 % | 0.2211 % | 1.1405 % |

**Use t ≲ 50 ps for any strict energy-closure claim from this run.**

### The domain was undersized for 100 ps — my extrapolation was too conservative

Stated plainly because it bounds the result. The domain was sized from the 10 ps run's drift
rates, but the real expansion is **faster**, because the target kept heating (`T_e` 293 → 625 eV):

| t [ps] | occupied cells | span [d_e] (domain is [−3000, +2400]) |
|---|---|---|
| 0 | 526 | −81 … +181 |
| 30.1 | 4 508 | −1 586 … +1 240 |
| 50.1 | 8 059 | −2 942 … +2 388 |
| **60.1 →** | 9 592 → **10 800** | **pinned at the walls** |

From ~55 ps the tenuous plume edge is against both walls. It costs 1.14 % of the weight and
the −9.56 % G6 gap, and it **truncates the percentile ion front**, which is why that measure is
non-monotonic (0.0536 c at 30 ps → 0.0245 c at 100 ps: the fast particles are being absorbed,
not slowing down). **The weight-weighted bulk is unaffected and is what the H3 numbers use.**
A future 100 ps run should use ≥ ±5000 d_e; the scaling rule is that the plume edge advances
at ~50 d_e/ps once `T_e` reaches ~600 eV, not the ~20 d_e/ps the 10 ps run showed.

### Numerics

`Tlocalfrac` 0.430 → **1.000**, saturated within ~2 ps and held for the whole run, so G5's
≤ 0.31 % bias bound is real throughout. No errors, no instability, `ω_pe dt` never a concern
(the target only ever *rarefies* from 1.5 `n_cr`).

## Retracted

Nothing.
