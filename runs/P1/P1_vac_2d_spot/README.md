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
| macroparticles | 2.682×10⁷ at t=0 → 2.499×10⁷ (−6.81 %; **weight** −2.06 %, which is the number to quote) |
| benchmark | (fill in: s/step over a 2000-step slice, GPU) |
| wall time | 20 308 s = 5 h 38 m on GPU 0, mean 0.1411 s/step |

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

**2026-07-29. Complete: 144 000 steps, 9.961 ps, 20 308 s (5 h 38 m) on GPU 0, mean
0.1411 s/step.** Deck verified against `config.yaml`. Gates: G1 0.214 pass, G2 61.2 pass,
**G3 −13.17 % (pass, negative)**, G4 pass, G5 pass (`Tlocalfrac` 0.432 → 0.860),
**G6 −16.86 % at 2.06 % weight loss**.

### The headline: this run stops being a finite spot after ~2 ps

`python scripts/spot_isolation.py runs/P1/P1_vac_2d_spot --control runs/P1/P1_vac_2d_spot_off`
(figure `media/P1/P1_vac_2d_spot/spot_isolation.png`) measures the transverse profile of the
**net** absorbed energy — driven particle-KE gain minus the control's boundary drain, per band:

| `t` [ps] | 1.0 | 2.0 | 3.0 | 5.0 | 7.0 | 10.0 |
|---|---|---|---|---|---|---|
| dark/lit | **0.135** | 0.408 | 0.544 | 0.712 | 0.823 | **0.946** |
| min/max across the box | 0.069 | 0.340 | 0.477 | 0.675 | 0.793 | **0.931** |

By `t_end` the absorbed energy is **flat across the whole box to 7 %** — from a beam whose
intensity at the wall is **1.1×10⁻⁷ of peak**. With periodic transverse faces the run is an
infinite periodic *array* of spots at 8 `w₀` pitch, and once heat crosses half the pitch the
array merges: the last two-thirds of this run is planar physics with extra steps.

**The `expect` block sized the box with `c_s` and that was the mistake.** It predicted lateral
flow would reach the wall at (80−20)/4.3 = **14 ps**, comfortably beyond `t_end`. But electrons
carry the energy, not ions: at the measured coronal `T_e` = 227 eV, `v_th,e` = **37.7 `d_e`/ps**
against `c_s` = 4.0, so 80 `d_e` is crossed in **2.1 ps**, and the measurement says contrast was
lost after **1.99 ps**. Prediction and measurement agree; the original estimate was optimistic by
**7×** purely from using the wrong speed. `revision_2026_07_29` in the config corrected the
*magnitude* of the heated radius but repeated the same `c_s` error, so it too was wrong.

**What a valid run of this duration needs:** `L_t/2 ≳ v_th,e·t_end + w₀` = **396 `d_e`**, i.e.
**4.9× wider** than the 80 used — 1 584 transverse columns against 320, and the ray march scales
linearly with columns. Or keep this box and stop at **`t` ≲ 1.6 ps**.

### What is still valid, and it is not nothing

**The operator is exact at `t` = 0**, on a *spatial* measure (TEST_PLAN §2.8's rule):

| step-0 quantity | measured | analytic |
|---|---|---|
| per-column mean ratio to `I₀exp(−(x/w₀)²)` | **1.00010** | 1 |
| column-to-column spread | 2.537 % | shot noise at 36 ppc |
| lag-1 autocorrelation of the residual | **−0.521** | negative ⇒ neighbour exchange, not boundary pile-up |
| total absorbed | **5.940787×10¹² W/m** | `I₀w₀√π` = 5.940916×10¹² (2.2×10⁻⁵ apart) |
| `f_abs(0)` | 0.999978 | 1.000 (`τ` = 1411) |

**c817b63 regression test passes across all 10 dumps.** `wall/interior` column ratio runs
0.02 → 0.95, peaking at 1.16 — never near the **20–25** the index clamp produced. The raw edge
share grows to 1.9×10⁻³, but with a ratio ≤ 1 that is light *filling* the box, not piling at a
clamped edge.

**Coupling, in the valid window.** `f_abs` peak 1.0000, final **0.5193**; `E_abs` = **31.01 J/m**;
shutoff (½ peak) **1.227 ps**. Against `P1_vac_1d_thick` at matched physical time, the
time-integrated on-axis coupling is **0.5240 vs 0.3034 (ratio 1.73)** — but read the two opposite
finite-spot effects before quoting it: lateral rarefaction *lowers* the coupling while the cooler
wings (less heating ⇒ higher `K ∝ T_e^{−3/2}`) *raise* it. `f_ax/f_abs(1D)` is 1.09 at `t` = 0 and
0.80–1.01 through 7 ps with no trend, then 0.62 and 0.56 at 8 and 9 ps — **inside the invalid
window**, so this run does not establish the H5 degradation.

Note the periodic images would push the result *toward* planar, i.e. toward ratio 1, so they do
not explain a drop to 0.56. The late fall is therefore unexplained rather than attributed, and
should not be read either way.

### `w_eff` is not the heated radius

`w_eff/w₀` grows 1.000 → **2.39**, well past the ≥1.5 lower bound `studies/spot_leak_ppc`
predicted. But `w_eff` is the second moment of the absorbed power and the shot-noise leak
inflates it: the leak reaches **16 %** here. Two temperature measures separate cleanly, and the
gap between them is the point:

| | `t` = 0 | `t_end` |
|---|---|---|
| `T_e` on axis, absorption-weighted (the corona the rays cross) | 52.5 eV | **243 eV** |
| `T_e` on axis, density-weighted (the bulk mass) | 52.6 eV | **81 eV** |

The laser drives a tenuous corona to 243 eV while the bulk target reaches only 81 eV. **Quote
which weighting you used** — `c_s` differs by √3 between them, and every timescale with it.

### Where the wing heating comes from — 71 % physics, 29 % artifact

Time-integrated, **9.5 %** of the absorbed energy is deposited beyond 2.5 `w₀` (2.67 of
28.08 J/m by dump-trapezoid; the coarse 10-dump integral reads 9 % low against `E_abs` = 31.01,
so treat these as ±10 %). The dark region's particle-KE gain is 9.18 J/m, so:

* **29 %** is direct deposition of the leaked light — a 36 ppc artifact (`studies/spot_leak_ppc`);
* **71 %** is lateral transport from the spot — real.

So the loss of isolation is **mostly physical**, and would not be fixed by more particles. Even
with the leak removed the dark bands would sit at ~2/3 of the lit bands' energy.

### G3 restricted to the illuminated columns — and my reason for building it was wrong

`scripts/g3_spot.py` exists because a whole-box G3 looked structurally unfair to a spot that
lights only 25 % of the transverse extent. Measured: **−12.93 % on the lit columns vs −13.17 %
whole-box — restricting changes the verdict by ×0.98.** The premise is falsified, and by the same
finding as above: the dark region is not dark. Its per-band gain (1.740 J/m) is 95 % of the lit
bands' (1.840 J/m). The script was still worth building — it is the only way to have known — and
its whole-box column reproduces `ParticleEnergy` to **0.000 %**, which is what makes the −12.93 %
trustworthy.

G3 is **−13.2 %**: negative, so not grid heating, but 4× the planar run's −3.09 %. Quote it beside
any few-percent number from this run.

### G6

**−16.86 % at 2.06 % weight loss** (6.81 % of *macroparticles*, 12.0 % of electron
macroparticles — quote the weight, not the count). A larger deficit than `P1_vac_2d`'s −8.42 % at a
*smaller* weight loss, because the escapers are the hot tenuous corona: few in weight, heavy in
energy per unit weight.

### Verdict

**The operator is validated; the physics question is not answered.** H5 is **untested** — the
effect it predicts appears only after the box has demonstrably stopped representing an isolated
spot. The deliverable is the box-sizing rule (`v_th,e`, not `c_s`) and a reusable check
(`scripts/spot_isolation.py`) that would have caught this before 5 h 38 m of GPU time.

**Media.** `media/P1/P1_vac_2d_spot/`: `spot_isolation`, `spot_transverse`, `spot_vs_baseline`,
`checks`, `gates`, `laser_history`, `laser_profile`, `fields_streak`, `fields_lineouts`,
`fields_map2d`, `phase_space`, and the three movies.

## Retracted

Nothing.
