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

**2026-07-29.** Both variants ran the full 14 400 steps (1.00 ps): 36 ppc in 1103 s, 144 ppc in
2331 s, on GPU 1. `python studies/spot_leak_ppc/analyze.py` reproduces everything below.

### The hypothesis is confirmed, and it was hiding a second effect

The leak **is** noise. But the single "7 % of the absorbed power is in the wrong place" number
turned out to contain two things that scale differently, and only one of them is an artifact.

| | 36 ppc | 144 ppc | scaling |
|---|---|---|---|
| ripple at `n_cr` | 9.32 % | 4.56 % | x0.49 (amplitude, x0.50 predicted) |
| peak `n_e` excess over nominal | 0.540 `n_cr` | 0.232 `n_cr` | x0.43 (amplitude, x0.50) |
| **leak beyond 2.5 `w₀`** | 2.99 % | 1.46 % | **x0.25, x0.27, x0.49** (see below) |
| **`w_eff/w₀`** | 1.625 | 1.523 | **does not scale -- 1.000 at `t` = 0 in both** |
| `f_ax` | 0.329 | 0.393 | +16 % of its own value |
| `f_abs` (whole beam) | 0.614 | 0.629 | +2.4 % |

### `t` = 0 is exact, and ppc-blind

Before the plasma has evolved, `T_e` and `n_e` are uniform, so the absorbed-power profile must be
the intensity profile and nothing else. It is, to the digits the dump carries:

| ppc | `w_eff/w₀` | `f_ax` | `f(1w₀)` | `f(2w₀)` | leak > 2.5 `w₀` |
|---|---|---|---|---|---|
| 36 | 1.0000 | 0.9999 | 0.9973 | 1.0009 | 0.00041 |
| 144 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 0.00041 |

The 0.00041 is the launch Gaussian's own tail beyond 2.5 waists, identical at both ppc because it
is geometry rather than plasma. This is the third independent confirmation of `warpx-cda` c817b63
and, being a **spatial** profile rather than a total, it is the acceptance baseline for any change
to the ray march (TEST_PLAN Phase 1.5, Tier 2).

### The leak: noise, on every dump -- but do not extrapolate the saturated state

The wings absorb **four times** the light that falls on them (`f(2w₀)` = 4.1 at 36 ppc, 4.3 at
144). A column cannot absorb power that was never incident on it, so the pedestal is core light
transported outward, exactly as the mechanism predicts. Its ppc scaling then dates the mechanism:

| `t` [ps] | leak ratio 144/36 | expected |
|---|---|---|
| 0.249 | **x0.25** | x0.25 if the leak is a weakly-scattered power (`∝ δn²`) |
| 0.498 | **x0.27** | x0.25 |
| 0.747 | x0.49 | x0.25 |

At 0.25 and 0.50 ps the leak falls as the noise **power**, which is what weak scattering off a
`δn` field predicts and which extrapolates to zero. By 0.75 ps that law has broken: the 36 ppc
leak **turns over** (0.0466 -> 0.0299) while 144 ppc is still rising. So the saturated state is
not weakly scattering, and **the ppc needed for a quotable `f_ax` is bounded by this pair, not
predicted by it** -- a third ppc would be needed to claim convergence rather than a trend.

### The width: thermal, real, and a genuine finite-spot result

`w_eff/w₀` is 1.000 at `t` = 0 and grows to ~1.5-1.6 at both ppc, so it is not the noise. The
transverse `n_e` profile stays **flat to 0.6 %** at every dump (`n_e(0)/n_e(2w₀)` = 0.98-1.05),
which rules out refraction off a density structure -- and 0.75 ps of `c_s` = 1.7e5 m/s motion is
0.13 µm, 4 % of a waist, so the density had no time to respond transversely anyway. What changed
is `T_e`: **248 eV on axis against 126 eV at two waists** (36 ppc; 271/115 at 144 ppc). Inverse
bremsstrahlung goes as `T_e^{-3/2}`, so **the spot suppresses its own coupling where it is
brightest**, and the absorbed-power profile ends up ~1.5x wider than the beam that made it.

Two consequences that outlive this study:

* **the heated radius is not `w₀`.** For H5, a spot of waist `w₀` heats a profile of ~1.5 `w₀`,
  so `t_cross = w₀/c_s` understates the crossing time and the peak `T_e` is lower than a
  `w₀`-wide deposition would give.
* **`f_ax` is not `f_abs`.** 0.39 against 0.63 here. Quoting a whole-beam absorbed fraction for
  a finite spot overstates what the axis receives by 60 %.

### What it costs the runs already taken at 36 ppc

`f_ax` reads 0.329 where 144 ppc reads 0.393, so **36 ppc under-reports the on-axis coupling by
16 % of its own value**. The sign settles the cause: the 36 ppc axis is *cooler* (248 vs 271 eV),
which on its own would *raise* its absorption, so the deficit is scattering loss out of the core
and not a thermal difference. The two effects push opposite ways, which is what makes them
separable at all.

Only the **ratio** transfers to `runs/P1/P1_vac_2d_spot` (thinned target, 1 ps, per the section
above); the 0.329 does not.

### An unplanned cross-check on the Phase 1.5 premise

The pair also measures the ray march's cost share, a completely different way from the profiler.
The march is independent of ppc while the particle work is proportional to it, so from
`T(36)` = 1103 s and `T(144)` = 2331 s:

```
ppc-independent cost   694 s      march share at  36 ppc:  62.9 %   (profiler: 65.6 %)
particle work @36 ppc  409 s      march share at 144 ppc:  29.8 %
```

694 s bounds the march from *above* (it also contains the field solve and diagnostics), and it
lands within three points of the 65.6 % the profiler reported on the physics run. Two independent
routes to the same number.

It also says something Phase 1.5 cannot fix: **a faster march does not buy ppc.** 144 ppc is why
this study had to thin the target to 100 `d_e` -- 144 ppc at the headline geometry does not fit in
12 GB, and that is a memory limit the march has no bearing on. Phase 1.5 buys transverse extent
and sweep points; converging `f_ax` needs a bigger card or a smaller box.

### Verdict

**NOISE-DRIVEN, as hypothesised** -- the far-wing leak is a resolution artifact and a finite-spot
coupling number needs a ppc budget rather than a physics caveat. **But** the absorption profile's
~1.5x broadening is real, thermal, and must be kept: it was inside the same 7 % and would have
been "fixed" away with it.

**Not settled by this pair:** the ppc at which `f_ax` converges (two points, and the late-time
scaling law fails), and whether the broadening saturates at ~1.5 or keeps growing past 1 ps.
