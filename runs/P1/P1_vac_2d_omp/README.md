# P1_vac_2d_omp — the planar 2D vacuum run, redone with a working operator, to 30 ps

**Phase.** 1, `TEST_PLAN.md` §7.2 (and §2.7–2.8 for why the predecessor is void)
**Question.** What does a planar 2D laser-driven ablation look like out to **29.9 ps**, on an
operator whose transverse handling is correct — and how does it compare to the 1D baseline
`P1_vac_1d_thick`, which ran the same axial box for the same 29.9 ps?
**Expected.** Close to `P1_vac_1d_thick` on the energy budget: `E_abs` within ~1 %, an `f_abs`
plateau near 1.0 falling once the peak density crosses `n_cr`, and ion energy ≈ 60 % of `E_abs`.
The 2D-specific numbers (transverse structure) should be **shot noise**, not filamentation —
that is what its `_off` control is for.
**Falsified by.** Transverse structure exceeding the control's; `E_abs` differing from the 1D
baseline by more than a few percent; or the energy budget failing to close once the plume
reaches the walls (see the caveat below, which is expected, not a surprise).

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #################~~~~~~~
      ^                                                                ^
      open                                                          open
      z = -400                                                  z = +1200

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  x  transverse     : -16 .. 16 d_e, boundaries periodic/periodic
  grid              : 64 x 3200 cells, dz = 0.5 d_e, dt = 0.06918 fs, 432000 steps = 29.88 ps
```

## Setup

**This run exists because its predecessor is invalid.** `P1_vac_2d` on disk predates
`warpx-cda` c817b63: rays drifting past a periodic transverse face were neither wrapped nor
terminated, so each dumped its remaining power into column 0 or N−1 and the two edge columns'
share went 3.2 % at `t` = 0 to **98.8 % at 26.9 ps**, with absorption **+12 %** above matched
1D. `CLAUDE.md` records that it "must be re-run before any 2D claim". This is that re-run.

Differences from `P1_vac_2d`: the deck adds **one line**, `laser_deposition.ray_threads = 8`,
and it runs on `build_cuda_omp` — the fixed *and* optimised operator (Phase 1.5, §7.5). Nothing
else changed; the duration was already 432 000 steps = 29.88 ps.

Control: **`P1_vac_2d_omp_off`**, same build, same box, `intensity = 0`. Both are needed — the
old `P1_vac_2d_off` is invalid for the same reason, and `CLAUDE.md` requires a run and its
control on the same backend.

## Cost

64 × 3200 = 0.205 M cells, 36 ppc in the target (3.7 M macroparticles), 432 000 steps.
Measured over 200 steps on this deck: **17.08 ms/step** on `build_cuda_omp` against **37.57 ms**
on `build_cuda` (2.20×) ⇒ **~2.1 h**, was ~4.5 h.

Expect the back half to be slower than that projection: `Vskip` starts at **0.636** and decays
as the fast-electron halo crosses the 1200 `d_e` forward gap at `v_th,e` ≈ 50 `d_e`/ps, so O2's
contribution falls from ~1.9× toward 1.0× over the run. The laser is 16 % of a step here — a
larger share than in the spot run (6 %) only because this deck has 5× fewer particles, so the
PIC side is cheaper. **Budget ~2.1–2.3 h.**

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

## Result

*(after the run)*

## Retracted

*(nothing yet)*

**Known limitation, stated before the run so it cannot be discovered as a surprise.** The
forward gap is 1200 `d_e` and the plume edge advances at ~50 `d_e`/ps once `T_e` ≈ 600 eV, so
the plume reaches the `+1200` boundary at **~24 ps** and the last ~6 ps of 29.9 are
wall-affected. G6 will degrade there, exactly as `P1_vac_1d_long` did when its plume sat
against both walls for the last 45 % of the run (weight loss 1.14 %, G6 −9.56 %). Read the
energy closure **before 24 ps**. Fixing it means a bigger box, not a shorter run: the same
`v_th,e` rule that governs the transverse direction governs this one.
