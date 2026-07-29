# P1_vac_2d_spot — a LOCALIZED laser spot: how fast does lateral rarefaction kill the drive?

**Phase.** 1, `TEST_PLAN.md` §7.2 (second sub-case), hypothesis **H5** (§2.3)
**Question.** With everything else held at the planar 2D run's values, what does replacing the
uniform plane wave with a **Gaussian spot of 1/e intensity radius `w₀` = 20 `d_e,cr`** do to the
drive — and on what timescale? This is the first run in the campaign whose transverse structure is
*intended*, so it is also the first that can measure lateral rarefaction, which neither 1D nor a
periodic planar 2D run can have at all.
**Expected.** On-axis quantities track the 1D baseline `P1_vac_1d_thick` while the lateral
rarefaction has not yet crossed the spot, then fall away from it. With `T_e` ≈ 300 eV over these
times (measured in `P1_vac_1d_long`, not `laser_report`'s implied `T_e,ab`), `c_s` = 0.0024 c =
**4.3 `d_e`/ps**, so `t_cross` = `w₀/c_s` ≈ **4.6 ps** and the 9.96 ps run covers ~2.2 crossing
times. Quantitatively: `E_abs` per unit spot area below the 1D value, with the deficit switching on
near 4–5 ps, and an on-axis `n_e` peak that falls faster than 1D because mass leaves sideways as
well as forward.
**Falsified by.** (a) No measurable deficit by 10 ps — then lateral loss is slower than `c_s`
predicts and a finite spot is cheaper than assumed. (b) A deficit present from `t` ≈ 0 — that is not
lateral rarefaction (which needs time to propagate) but a beam-geometry or boundary error, and the
step-0 deposition profile is where to look. (c) Structure in the **edge** columns, which the beam
does not illuminate (`exp(−16)` = 1.1×10⁻⁷ of peak) — that would mean the transverse-wrap fix
(`warpx-cda` c817b63) is incomplete.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #########################~~~~~~~~~
      ^                                                                ^
      open                                                          open
      z = -400                                                  z = +700

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  x  transverse     : -80 .. 80 d_e, boundaries periodic/periodic
  grid              : 320 x 2200 cells, dz = 0.5 d_e, dt = 0.06918 fs, 144000 steps = 9.961 ps
```

## Setup

Parent is **`P1_vac_2d`** (planar 2D); the 1D baseline for on-axis comparison is
**`P1_vac_1d_thick`**. Target, wavelength, **peak** intensity, `Z_eff·lnΛ`, `L_n`, `dz`, `cfl`,
`particle_shape` and ppc are all unchanged from both. Four things differ, each for a stated reason:

| | `P1_vac_2d` | this run | why |
|---|---|---|---|
| `beam_profile` | uniform | **gaussian, `w₀` = 20 d_e** | the point of the run |
| transverse extent | ±16 d_e (64 cols) | **±80 d_e (320 cols)** | 4 `w₀` per side, so the beam is `exp(−16)` = 1.1e−7 at the wall — the Phase-0 finite-spot rule |
| axial `hi` face | +1200 d_e | **+700 d_e** | measured, not guessed: see Cost |
| `t_end` | 29.9 ps | **9.96 ps** | ~2.2 lateral crossing times is what the question needs, and 320 columns of serial ray march is what it costs |

**`beam_waist` is the 1/e radius of the INTENSITY**, not of the field: `LaserDeposition.cpp`
applies `I = I₀·exp(−(r²/w²)^order)` with `order` = 1 for `profile = gaussian`. So `w₀` = 20 `d_e`
= 3.35 µm, FWHM = `2√(ln2)·w₀` = 33.3 `d_e` = 5.6 µm, and the total power per unit length is
`I₀·w₀·√π` = **5.94×10¹² W/m** — the same as a uniform beam 35.4 `d_e` wide. `intensity` is the
**peak**, so the on-axis drive at `t` = 0 matches `P1_vac_2d` and `P1_vac_1d_thick` exactly; that
is what makes a later on-axis difference a 2D effect rather than a power difference.

**Periodic transverse means a periodic ARRAY of spots** at 160 `d_e` pitch, not one isolated spot.
That is deliberate — Phase 0 measured that `open` transverse walls drain a hot population at ~40 %/ps
and cannot be fixed by enlarging the box — and it is only valid while the lateral flow has not
reached the wall. At `c_s` = 4.3 `d_e`/ps the flow leaves the spot edge (|x| = 20) and arrives at
|x| = 80 at **14 ps > `t_end`**. *This is the run's main validity condition and must be checked
post-run.*

**Scale honesty: `w₀` = 3.35 µm is 10.7× smaller than the spot H5 is about.** H5's criterion is
`w₀ ≳ 0.8 ρ_i0` ≈ 36 µm = **214 `d_e,cr`** (`TEST_PLAN.md` §2.1, §2.3). A run with `w₀` = 214 `d_e`
and the same 4-waist margin needs ±856 `d_e` transverse = 3424 columns, i.e. **10.7× this run's
columns** on top of a proportionally longer physical time — the serial ray march makes that
unaffordable at Phase-1's critical-density resolution. So this run does **not** test H5's threshold
directly. What it can do is measure the *degradation law* in the dimensionless variable
`w₀/(c_s t)`, which is the form in which the result transfers to Phase 2 — where lengths are
referenced to `d_e,amb` = 0.684 µm, cells are 4.08× coarser, and a 36 µm spot is only 52 `d_e,amb`
and therefore affordable. State the extrapolation as an extrapolation.

## Cost

**The axial `hi` face was cut from +1200 to +700 `d_e` on a measurement, not a guess.** In
`P1_vac_1d_thick` (same target, same laser, valid — 1D was never affected by the §2.7 bug) the
plume's 1e−4 `n_cr` front sits at **384 `d_e` at 8.97 ps** and 541 at 11.96 ps, and **99 % of
`P_abs` is below 160 `d_e` at 8.97 ps**. Nothing that absorbs measurably reaches +700 inside 9.96 ps.
This matters because the eikonal ray march is **serial host code** costing `path/(ray_cfl·dz)` RK4
steps per ray, and this run has 320 rays instead of 64: removing 500 `d_e` of vacuum from the front
of every ray is a ~30 % cut in the dominant cost.

Benchmarked, not scaled — `CLAUDE.md`'s rule after a 4× miss on `P1_vac_1d`.

| | value |
|---|---|
| cells | 320 × 2200 = 704 000 |
| macroparticles | (fill in from `PN.txt`) |
| benchmark | (fill in: s/step over a 2000-step slice, GPU) |
| wall time | (fill in from `progress.log`) |

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.214 (0.152 at t=0; 2.0 would need 261 n_cr) | pass |
| G2 `dz/lambda_D` (target) | 61.2 — the unavoidable cold-target value, bounded to 1.02 M steps by `P1_vac_1d_long` | pass |
| G3 laser-off control | `P1_vac_2d_spot_off` | post-run |
| G4 `ray_cfl` check | `studies/exit_overshoot`; note the turning point is *not* reached at `L_n` = 60 (0.000 % of `P_abs` at or below critical), so `ray_cfl` sensitivity is expected to be weak | pass (inherited) |
| G5 ppc / `Tlocalfrac` | 36 ppc (6×6); bias bound 3.5 % | post-run |
| G6 energy closure | | post-run |

## Result

(pending)

## Retracted

Nothing.
