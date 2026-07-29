# `spot_leak_ppc` — is the finite-spot transverse leak physics or shot noise?

**The observation this exists to explain.** `runs/P1/P1_vac_2d_spot` (Gaussian, `w₀` = 20 `d_e`,
±80 `d_e` periodic transverse) puts **7 % of its absorbed power outside 2.5 waists** by 2 ps,
where the launch profile has `exp(−6.25)` = 0.2 %. The pattern rules out the pre-c817b63 index
clamp: it is a **broad flat pedestal** filling the box, and the wall columns sit *below* their
inward neighbours (ratio 0.62–0.74, where the clamp gave 20–25).

**The proposed mechanism.** The transverse `n_e` ripple at the critical surface goes from 0.07 %
at `t` = 0 to **9.43 %** at 1 ps — which is the **36 ppc shot-noise floor** (36 electrons per
cell → 16.7 %, smoothed by `particle_shape = 2`), not a coherent structure: `NUniformPerCell`
starts on a quiet sub-cell lattice and fills in to Poisson within a plasma period. And
`n_ref = √(1 − n_e/n_cr)` → 0 near critical, so the eikonal ray equation amplifies any density
gradient by `1/n_ref`. Rays therefore scatter off noise, and with periodic transverse faces the
scattered light **wraps and fills the box**.

**Hypothesis.** The leak is a resolution artifact and falls with ppc.

**What it varies.** `numerics.ppc` = 36, 144 — nothing else. 36 → 144 halves the per-cell density
noise, so a noise-driven leak must fall visibly.

**Falsified by** a leak share unchanged across the pair within its own scatter. Then the pedestal
is refraction off a *real* transverse gradient — a physical property of a finite spot — and it
belongs in every finite-spot error budget rather than being resolvable away.

**Why it is worth a GPU hour.** 7 % is the same size as the effects H5 is trying to measure, and
the two cases call for opposite fixes: more ppc (expensive, and 2D already runs at 36 rather than
the 400 the 1D runs use), versus a wider box with a beam negligible far from the wall. Until it
is settled, a finite-spot coupling number cannot honestly be quoted to better than ~7 %.

## What is deliberately NOT held fixed, and why it is still a fair test

The target is thinned from 400 to 100 `d_e` and `t_end` cut from 9.96 ps to 1 ps, so that 144 ppc
fits in 12 GB of device memory. At 1 ps the rarefaction has crossed only ~4 `d_e` of the slab, so
**the corona the rays actually refract in is the one the physics run has at that time** — the
leak at 1 ps in the physics run (4.7 %) is the number to compare the 36 ppc variant against. The
pair shares geometry, beam and duration, so the **ratio** is the result; neither leak on its own
transfers to the 9.96 ps run.

This bounds the study honestly: it tests the mechanism at 1 ps, not the saturated 7 % at 2 ps and
beyond. If the leak is noise-driven at 1 ps it is noise-driven later, but the *magnitude* of the
improvement at higher ppc is not measured for the saturated state.

## Files

```
config.base.yaml   the spot config, thinned target, 1 ps
run_variants.sh    launches the pair (-g N to pick a GPU)
analyze.py         leak share, ripple at n_cr, w_eff -> one verdict line
scratch/           the variant run dirs (gitignored)
```

## Result

(pending)
