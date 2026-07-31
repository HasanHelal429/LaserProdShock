# P1_vac_2d_spot_long — the finite-spot 2D run taken to 29.9 ps

**Phase.** 1, `TEST_PLAN.md` §7.2 (H5), run on the Phase-1.5 operator (§7.5)
**Question.** `P1_vac_2d_spot` ended at 9.96 ps with `f_ax/f_abs(1D)` flat at 0.80–1.01 through
7 ps and then **0.62 and 0.56 at 8 and 9 ps** — a late drop this campaign recorded as
*"unexplained rather than attributed"*. Does that drop continue, level off, or reverse when the
run is carried to **29.9 ps**, the mark `P1_vac_1d_thick` and `P1_vac_2d` reach?
**Expected.** No prediction is registered for the drop itself — that is the point of running it.
What *is* expected: the `f_abs` plateau decays hydrodynamically once peak `n_e` falls below
`n_cr`, and by 30 ps the drive should be well past the ~38 ps a shock needs, so this also
measures how much drive is left at the far end.
**Falsified by.** Nothing about H5 — see the limitation below. This run cannot test H5.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      ############~~~~
      ^                                                                ^
      open                                                          open
      z = -400                                                  z = +2000

  #  target flat top : 1.5 n_cr, 400 d_e thick, centred at -200 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  x  transverse     : -80 .. 80 d_e, boundaries periodic/periodic
  grid              : 320 x 4800 cells, dz = 0.5 d_e, dt = 0.06918 fs, 432000 steps = 29.88 ps
```

## Setup

Parent: **`P1_vac_2d_spot`** (9.96 ps). Following the `_long` rules in `runs/README.md`:

* **`max_step` 144 000 → 432 000** (9.96 → 29.88 ps), the same duration as `P1_vac_1d_thick`
  and `P1_vac_2d`, so the 1D↔2D↔spot comparison is at one time.
* **The domain grew with the duration**, and it was sized from a *measurement*, not a guess.
  The parent's forward gap was 700 `d_e`. The validation re-run `P1_vac_2d_spot_omp` reports
  `Vskip`, the fraction of the axial domain the ray march finds **exactly empty**, and it falls
  0.4700 → 0.2477 over the first 2.92 ps — **85.3 `d_e`/ps**, which would consume a 700 `d_e`
  gap by 6.1 ps. Applying this campaign's box rule, `L ≳ v_th,e·t_end + initial extent` with
  `v_th,e` ≈ 61 `d_e`/ps at a 600 eV corona, gives ≥ 1830 `d_e` for 29.9 ps. **Forward gap set
  to 2000 `d_e`**, which `v_th,e` reaches at 32.8 ps and the 50 `d_e`/ps plume edge at 40 ps.
* **Diagnostics scaled by the same ×3** (plotfiles 14 400 → 43 200, fields 1 800 → 5 400, phase
  7 200 → 21 600, reduced 360 → 1 080), so this is the same *number* of dumps rather than 3×
  the data — ~30 GB, as the parent's 21 GB scaled by the larger grid.
* **`laser.intervals` is NOT a diagnostic and is untouched at 10.** The kick amplitude goes as
  `√(H·Δt)` with `Δt = intervals·dt`, so changing it would change the physics.
* `ray_threads: 8` added; runs on `build_cuda_omp`.

The rear stays truncated at −400 `d_e` on an open boundary. That is validated by core
decoupling, and it costs energy budget — 6.13 % weight loss at 30 ps in 1D — so **G6 cannot be
closed tightly here**; take strict closure from an untruncated run.

## Cost

320 × 4800 = 1.54 M cells, 18.4 M macroparticles, 432 000 steps. From a two-point cost model
fitted to this build (33.7 ms per M cells + 2.75 ms per M macroparticles, which reproduces both
measured decks exactly): **0.102 s/step ⇒ ~12.3 h**. Expect somewhat more at the far end —
`Vskip` decays as the plume fills the forward gap, so O2's contribution falls from ~1.9× toward
1.0×, and the deposition scatters over a growing set of occupied cells. **Budget 12–14 h.**

On the pre-Phase-1.5 build this run would have been ~26 h.

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

**G3 has no control of its own.** The `_long` convention says an extended run needs its own
`_long_off`, because grid heating accumulates with step count — so a G3 number quoted here from
`P1_vac_2d_spot_off` (9.96 ps, smaller box) is **not** a valid subtraction and must be labelled
as indicative only. Running the control is a deliberate deferral, not an oversight.

## Result

*(after the run)*

## Retracted

*(nothing yet)*

**The limitation that governs how this run may be read.** It is **not** a valid finite-spot run
and cannot test H5. Its parent lost transverse isolation at **1.99 ps** — `dark/lit` went 0.135
at 1 ps to 0.946 at 10 ps, i.e. the deposited energy ended flat to 7 % across a box the beam
illuminates at 1.1×10⁻⁷ of peak — because periodic transverse faces make the run an infinite
array of spots at 8 `w₀` pitch, and the array merges once heat crosses half the pitch. Widening
the transverse box to fix that needs `L_t/2` ≳ `v_th,e`·30 ps ≈ 1830 `d_e` — **4 752 columns
against 320**, ~32 M cells and ~270 M macroparticles, which is ~21 GB (a 12 GB device) and
several days. That run is not affordable and this one does not substitute for it.

What this run therefore *is*: a **planar-equivalent** 2D run with a transversely non-uniform
drive, carried to 30 ps. Read it for the axial physics and the late-time drive history —
which is what the question above asks — and not for anything transverse.
