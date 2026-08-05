# P1_vac_2d_spot_omp — P1_vac_2d_spot re-run on the Phase-1.5 operator

**Phase.** 1.5, `TEST_PLAN.md` §7.5 (the run is Phase-1 physics; the *question* is Phase-1.5)
**Question.** Does the optimised operator — 1.96× faster end to end — reproduce
`P1_vac_2d_spot`, a result the campaign already has?
**Expected.** Every physics observable within run-to-run GPU noise of the parent:
`f_abs` plateau, `E_abs(t)`, `Tlocalfrac`, and the `spot_report` columns (`f_ax`,
`w_eff/w₀`, leak > 2.5 `w₀`, wall/in). `E_abs` is the sharp one — it integrates hundreds of
applications and agreed to **0.6 %** between geometries in this campaign, so a disagreement
above ~1 % would be a real signal. `f_abs(0)` is **not** a criterion (10.4 % 1σ seed spread).
**Falsified by.** Any observable moving beyond that band, or `Vskip` behaving unphysically
(it should start at 0.47 and fall as the corona crosses the forward gap at `v_th,e`).

## Geometry

```
2D  |  z = propagation axis (across), x = transverse (down)  |  lengths in d_e at critical density = 0.1676 um

        x = +80   (periodic)
       +----------------------------------------------------------+
   +80 |######################~~~~~~~~                            |
   +70 |######################~~~~~~~~                            |
   +60 |######################~~~~~~~~                            |
   +50 |######################~~~~~~~~                            |
   +40 |######################~~~~~~~~                            |<
   +30 |######################~~~~~~~~                            |<=
   +20 |######################~~~~~~~~                            |<===
   +10 |######################~~~~~~~~                            |<=======
    +0 |######################~~~~~~~~                            |<=========
   -10 |######################~~~~~~~~                            |<=======
   -20 |######################~~~~~~~~                            |<===
   -30 |######################~~~~~~~~                            |<=
   -40 |######################~~~~~~~~                            |<
   -50 |######################~~~~~~~~                            |
   -60 |######################~~~~~~~~                            |
   -70 |######################~~~~~~~~                            |
   -80 |######################~~~~~~~~                            |
       +----------------------------------------------------------+
        x = -80   (periodic)
        ^                                                        ^
        open                                                  open
        z = -400                                          z = +700

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0), drawn out to 1e-3 n_cr
  ' ' vacuum        : no ambient plasma
  <  laser          : gaussian, w0 = 20 d_e (1/e radius of INTENSITY), I0 = 1e+18 W/m^2 peak, enters the hi z face
                      bar length is proportional to the LOCAL intensity, so the beam is drawn to scale against x
  grid              : 320 x 2200 cells (x by z), dz = dx = 0.5 d_e, dt = 0.06918 fs, 144000 steps = 9.961 ps
```

## Setup

Parent: **`P1_vac_2d_spot`** (2026-07-29, `build_cuda`, 5 h 38 m). The config is copied
verbatim; the rendered decks differ by **exactly one line**:

```
laser_deposition.ray_threads          = 8
```

That knob cannot change the answer — ray `i` always lands in accumulator `i % 16`, and the
accumulators are reduced in bucket order, so the result is invariant to the thread count by
construction (verified byte-identical across `OMP_NUM_THREADS` 1/2/4/8/12 on the CI decks).

The binary differs: **`build_cuda_omp/bin/warpx.2d`** instead of `build_cuda/bin/warpx.2d`.
Same source tree except for the Phase-1.5 patch, and configured `-DAMReX_OMP=ON` so that host
OpenMP exists at all (`build_cuda` is `AMReX_OMP=OFF`, which leaves O1 inert).

**The operator changes, and why none of them is a physics change** —
`studies/ray_march_perf/patches/o123-ray-march.patch`:

| | what it does | why the answer cannot move |
|---|---|---|
| O3 | RK4 stage 1 reuses the sample the previous step already took at that same point | `sample()` is a pure function of position and a field frozen for the march |
| O2 | steps lying wholly in *empty* field skip their five field samples | in vacuum `sample` returns `(n_ref, ∇n_ref) = (1, 0)` exactly, so the same arithmetic runs with the samples removed |
| O1 | the ray loop is threaded over 16 deposition accumulators | rays are independent; the accumulators are summed in a fixed order |
| O4 | the IB coefficient is formed on the device, and 3 field components are gathered instead of 6 | same per-cell expression on the same inputs; the `Tlocalfrac` sums stay on the host in their original order |

Verified before this run: 285/285 CI-deck files byte-identical at `n_accumulators=1`; the
parent deck's own step-0 dump byte-identical at 36 ppc with `Tlocalfrac` unchanged to every
digit; and on **this** deck on GPU, the step-0 and step-10 dumps are identical between the old
and new binaries.

## Cost

320 × 2200 cells, 36 ppc, 144 000 steps. Predicted **~2.9 h** on one RTX 4070 against the
parent's 5 h 38 m, from 0.0743 s/step measured over 40 steps of this deck (parent: 0.1453).

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | | |
| G2 `dz/lambda_D` (target / ambient) | | |
| G3 laser-off control | | |
| G4 `ray_cfl` check | | |
| G5 ppc / `Tlocalfrac` | | |
| G6 energy closure | | |
| G7 | | |

**G3 needs its own note.** The parent's control, `P1_vac_2d_spot_off`, was run on
`build_cuda`. `CLAUDE.md`'s rule is that a run and its control share a backend, so a G3
subtraction of this run against that control mixes builds. Either re-run the control on
`build_cuda_omp`, or read G3 from the parent pair and treat it as unchanged — the operator is
bit-identical, and G3 measures grid heating, which none of O1–O4 touches.

## Result

*(after the run)*

## Retracted

*(nothing yet)*

**A caveat that belongs here, not in the result.** GPU runs of this deck are **not
reproducible run-to-run**: the CIC density deposit uses device atomics, whose summation order
varies, so two runs of the *same binary* diverge. Measured on this deck at 21 steps — same
binary twice: `n_e` worst-cell 5.7×10⁻³ by step 20, totals agreeing to 1.6×10⁻¹³. Old vs new
binary: 4.5×10⁻³ and 2.9×10⁻¹³ — **the same size**. So a bit-level comparison against the
parent is impossible in principle, and any difference must be judged against that noise, not
against zero.
