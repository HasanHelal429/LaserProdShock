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

- `media/P1/P1_vac_2d_off/checks.png`
- `media/P1/P1_vac_2d_off/fields_lineouts.png`
- `media/P1/P1_vac_2d_off/fields_map2d.png`
- `media/P1/P1_vac_2d_off/fields_streak.png`
- `media/P1/P1_vac_2d_off/gates.png`
- `media/P1/P1_vac_2d_off/laser_history.png`
- `media/P1/P1_vac_2d_off/laser_profile.png`
- `media/P1/P1_vac_2d_off/movie_fields.mp4`
- `media/P1/P1_vac_2d_off/movie_map2d.mp4`
- `media/P1/P1_vac_2d_off/movie_phase.mp4`
- `media/P1/P1_vac_2d_off/phase_space.png`

## Result

Ran **432 000/432 000 steps = 29.88 ps in 1 h 57 m** on GPU 1, zero errors, `--verify` OK.
(2.6× faster than its driven partner — the ray march is serial host code, so a run without it
keeps the GPU at a steady 82 % where the driven run oscillates 0 %/61 %.)

### 1. G3 passes at 36 ppc, but the excursion is 47× the 400-ppc value

| | this control (36 ppc) | 1D controls (400 ppc) |
|---|---|---|
| net particle-KE gain | **−1.8615 J/m** | −7 962 J (100 ps), −1 696 J (10 ps) |
| **as a share of the driven gain** | **−3.09 %** | **−0.066 %** |
| electrons / ions | −1.495 / −0.3666 J/m | −221.8 / +213.9 kJ |
| weight lost | 6.030 % | 0.0014 % |

**The sign is still negative**, which is the discriminator: grid heating appears as a net *gain*
shared by both species, and this is not that. So gate G2 (`dz/λ_D` = 61) remains bounded and
`P1_vac_2d`'s ablation is real. **But −3.09 % against −0.066 % is a 47× larger relative
excursion**, and that is the honest price of dropping ppc 400 → 36. A 2D result quoted at the
few-percent level must carry this term.

Note the electron and ion terms no longer cancel the way they did at 400 ppc (there both were
large and opposite; here both are negative). With 11× worse per-cell statistics the ambipolar
bookkeeping is simply noisier.

### 2. This run is what identified the 2D validation failure

Its most valuable output was not its energy budget. `P1_vac_2d` developed a **factor-250
transverse non-uniformity in laser deposition**, and the obvious first suspicion was that the
laser was driving a filamentation instability. **This control ruled that out:** it develops the
*same* transverse density modulation with no beam at all —

| transverse rms/mean of `n_e` | driven | **this control** |
|---|---|---|
| corona (0…120 d_e), 7.5 → 29.9 ps | 0.063 → 0.056 | **0.040 → 0.044** |
| slab (−380…−100 d_e) | 0.030 → 0.028 | **0.031 → 0.033** |

So the ~5 % density ripple is **ordinary PIC shot noise**, not laser-driven, and what the driven
run adds is *amplification of it by ray refraction*. Being able to say that — rather than
speculating about filamentation — is exactly why G3 controls are mandatory here. Full analysis in
`runs/P1/P1_vac_2d/README.md` §3.

Also worth recording: the ripple appears despite a **quiet start**. `NUniformPerCell` puts
particles on a regular sub-cell lattice, so the initial transverse variation is only **0.06 %**;
it reaches a few percent within ~3 ps as thermal motion decorrelates the lattice.

Boundary weight loss is **6.030 %**, essentially the driven run's 6.146 % — so the loss is the
rear free surface draining through the truncated boundary, not something the drive causes.

## Retracted

Nothing.
