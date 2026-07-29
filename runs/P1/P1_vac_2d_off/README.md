# P1_vac_2d_off — the laser-off control for `P1_vac_2d` (gate G3, 2D, 36 ppc)

**Phase.** 1, `TEST_PLAN.md` §7.2 and §6 (gate G3)
**Question.** Does grid heating stay negligible at **36 ppc**, the 2D-affordable value?

**Why the 1D bound cannot simply be inherited.** The 1D controls measured grid heating at
**−0.066 %** of the driven gain over 1.024 M steps — a strong result, but measured at **400
ppc**. This run uses **36**, an 11× reduction, and finite-grid heating gets worse as per-cell
statistics get worse. An 11× ppc cut is precisely the case where a bound established at high
ppc must be re-measured rather than assumed. At `dz/λ_D` = 61 the target is
Debye-under-resolved by construction (gate G2), and this run is the only thing that turns G2
into a bound for `P1_vac_2d`.

**Expected.** The same picture as the 1D controls, and in particular the same *sign*:

- **net particle-KE change ≈ 0, and NOT a net gain.** The discriminator is the sign, not the
  magnitude: the 1D controls showed a large internal **electron→ion ambipolar transfer that
  cancels** (at 100 ps: electrons −221.8 kJ, ions +213.9 kJ, net −8.0 kJ). Grid heating instead
  appears as a net **gain shared by both species**.
- `LASERDEP` reports `Pabs = 0` on every line.
- a slow, undriven thermal expansion of the corona — which, as the 1D controls showed, is **not
  negligible for velocity measurements** (their bulk reached 0.17 `c_s`, ~20 % of the driven
  value) and must be subtracted before quoting any `v_p`.

**Falsified by.** A net particle-KE **gain**, or one that grows with step count. Either would
mean `P1_vac_2d`'s ablation is partly numerical at 36 ppc — and since 36 ppc is what makes 2D
affordable at all, that would force either a much more expensive 2D campaign or an explicit
error bar on every 2D number.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                    x  LASER OFF (I = 0)
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

`P1_vac_2d` with `laser.intensity: 1.0e18 → 0.0`. **Nothing else** — verified, not asserted:
stripping comments, the two generated decks differ in exactly one line,

```
< laser_deposition.intensity            = 1e18      (P1_vac_2d)
> laser_deposition.intensity            = 0.        (this run)
```

and `tests/test_structures.py` enforces that invariant for every `_off` run in the repo. Same
64 × 3200 grid, same 432 000 steps, same 36 ppc, same 400 d_e target, same rear truncation,
same periodic transverse, same diagnostics.

`controls.ray_cfl_ladder` is declared only so the two configs are indistinguishable to the
gates; with no beam, `ray_cfl` is moot.

## Cost

Same grid and particle count as `P1_vac_2d` — 204 800 cells, ≈ 5.4 M macroparticles, 432 000
steps → 29.88 ps; **≈ 4 h**, slightly cheaper in practice because the ray trace and the
per-cell temperature reduction never run.

Both runs use the **same backend deliberately**: CPU and GPU agree on integrated `E_abs` only
to ~2.5 % (different `ParallelForRNG` streams), so mixing backends across a G3 pair would fold
that difference into the subtraction. Launched after `P1_vac_1d_thick` frees its GPU.

## Gates

`make_inputs.py --check`: **3 pass, 0 warn, 0 fail**, 3 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.214 at 2× compression (0.152 initial) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — **this run is what bounds it at 36 ppc** |
| G3 laser-off control | *this run IS the control* (`intensity = 0`) | info |
| G4 `ray_cfl` check | 0.25 — moot, no beam | **pass** |
| G5 ppc / `Tlocalfrac` | 36 ppc; bias bound ≤ 3.5 % | **pass** |
| G6 energy closure | — | post-run: with `E_abs` ≡ 0, the **entire** particle-energy gain is the grid-heating budget |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm | info |

## Media

*(not generated yet)*

## Result

*(queued)*

## Retracted

Nothing.
