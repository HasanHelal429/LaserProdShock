# `rays_per_cell` — does one ray per transverse cell resolve a finite spot?

**Hypothesis (H5 support, `TEST_PLAN.md` §7.2).** `TEST_PLAN.md` puts `rays_per_cell`
convergence with the finite-spot run rather than with the planar one, because "a structured
beam on a structured plume is where sub-cell ray sampling first matters". This study tests the
**beam** half of that statement absolutely, and hands the **plume** half to a measurement on
the physics run itself rather than to a second expensive ladder.

**What it varies.** `laser.beam.rays_per_cell` = 1, 2, 4 on the finite-spot deck
(`runs/P1/P1_vac_2d_spot`: Gaussian, `w₀` = 20 `d_e`, 320 × 2200 cells, 36 ppc). Nothing else
differs, so the result transfers to that run directly.

**Why step 0 is the whole measurement.** At `t` = 0 the density is the one the deck built
(0.01 % ripple from `NUniformPerCell`) and the slab is optically thick (`τ` ≈ 1400), so every
ray is fully absorbed and the column-integrated absorbed power **must** equal
`I₀·exp(−(x/w₀)²)·dx`. That makes the test absolute — no reference run, no fitting — and it is
why each variant is two steps long.

**Prediction.** `rays_per_cell` = 1 launches one ray per transverse cell from the cell centre,
i.e. 2 samples per `d_e` and 40 per waist. The **mean** column profile should therefore already
be converged; what should fall is the column-to-column **scatter**, which is set by how far an
individual ray wanders through the density ripple, not by how many rays there are.

**Falsified by** a change in the mean absorbed power or in the measured 1/e radius with
`rays_per_cell` — that would mean one ray per cell mis-samples the beam itself, and the
finite-spot run would need re-running at higher sampling.

**Why the mean-vs-scatter distinction is the point.** The finite-spot result is quoted through
`f_ax`, the absorption in the central columns divided by the incident power in those same
columns (`scripts/spot_report.py`). Scatter that is exchanged between *neighbouring* columns —
which the step-0 dump of the physics run already shows, at 2.4 % rms with lag-1 autocorrelation
**−0.51** — averages out of that measure. A shift in the mean would not.

**What this study does NOT cover, and how that is handled instead.** A ladder on a *developed*
plume (where transverse density gradients are real rather than shot noise) would cost ~100×
this one: the driven 2D step is 58 % serial host-side ray march, and `rays_per_cell` = 2
doubles it. Rather than assume it away or pay for it, `spot_report.py` prints the scatter's
lag-1 autocorrelation for **every** dump of the physics run. Negative means neighbour exchange
(random wander, averages out); positive and growing would be coherent refractive channelling,
which is the case that would demand the expensive ladder. That is a measurement deciding
whether the study is needed, and it is free.

## Files

```
config.base.yaml   the finite-spot config with max_step = 2
run_variants.sh    launches the ladder (-g N to pick a GPU)
analyze.py         step-0 profiles vs analytic I(x) -> media/rays_per_cell/rays_per_cell.png
scratch/           the variant run dirs (gitignored)
```

The runner disables the plotfile diagnostics with ParmParse overrides, because a step-0
plotfile of this deck is 1.6 GB of particles the measurement never reads. `make_inputs.py
--verify` will therefore flag these decks — by design, and recorded in `run_variants.sh`.

## Result

(pending — run after `P1_vac_2d_spot_off` frees GPU 1)
