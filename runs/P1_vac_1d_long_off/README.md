# P1_vac_1d_long_off — the laser-off control for `P1_vac_1d_long` (gate G3, 100 ps)

**Phase.** 1, `TEST_PLAN.md` §7.1 and §6 (gate G3)
**Question.** Does grid heating stay negligible over **1.024 million steps**?

**Why the 10 ps control cannot be reused.** Finite-grid heating accumulates with *step count*,
so a bound measured over 102 400 steps says nothing about a run that is 10× longer. That is
also why this deck keeps the physics run's exact duration rather than being a shorter, cheaper
stand-in — the whole value of a G3 control is that the only difference is the drive.

At `dz/λ_D` = 61 the target is Debye-under-resolved by construction (gate G2), and this run is
the only thing that converts G2 from a number into a bound. **This is a considerably sharper
test than the 10 ps control was**, and if it fails, `P1_vac_1d_long`'s ablation numbers go with
it.

**Expected.** Essentially a repeat of `P1_vac_1d_off`, scaled:

- **net particle-KE change ≈ 0**, and in particular *not* a net gain. The 10 ps control read
  **−1 696 J** (−0.07 % of the driven gain) and it should stay small in *relative* terms.
- the same **electron→ion ambipolar split** rather than a heating signature: at 10 ps electrons
  lost 51.4 kJ while ions gained 49.7 kJ, cancelling to ≈ 0. Grid heating would instead appear
  as a net **gain shared by both species** — that is the discriminator to look for, not the
  magnitude alone.
- `LASERDEP` reports `Pabs = 0` on all 102 400 lines.
- essentially no boundary loss (the 10 ps control lost 0.0000 % of the weight), though over
  100 ps its own slow thermal expansion will start to reach the walls.

**Falsified by.** A net particle-KE **gain** growing with step count, or an ion population that
looks like a piston. Either would mean `P1_vac_1d_long`'s ablation is partly numerical, and
every number from it — including the `E_abs` history that Phase 2's drive budget rests on —
would have to be withdrawn.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                    x  LASER OFF (I = 0)
                                         ##~~                           
      ^                                                                ^
      open                                                          open
      z = -3000                                                  z = +2400

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 10800 cells, dz = 0.5 d_e, dt = 0.09783 fs, 1024000 steps = 100.2 ps
```

## Setup

`P1_vac_1d_long` with `laser.intensity: 1.0e18 → 0.0`. **Nothing else** — verified rather than
asserted: stripping comments, the two generated decks differ in exactly one line,

```
< laser_deposition.intensity            = 1e18      (P1_vac_1d_long)
> laser_deposition.intensity            = 0.        (this run)
```

and `tests/test_structures.py` enforces that invariant for every `_off` run in the repo.

Same 10 800 cells, same 1 024 000 steps, same 400 ppc, same domain, same `open`/`open`
boundaries, same diagnostics. `controls.ray_cfl_ladder` is declared only so the two configs are
indistinguishable to the gates; with no beam, `ray_cfl` is moot.

## Cost

Same grid and particle count as `P1_vac_1d_long` — 10 800 cells, 420 000 macroparticles,
1 024 000 steps → 100.18 ps. Slightly cheaper in practice, since the ray trace and the per-cell
temperature reduction never run. **~123 min**, on GPU 1 concurrently with the physics run on
GPU 0.

Both use the **same backend deliberately**: CPU and GPU agree on integrated `E_abs` only to
~2.5 % (different `ParallelForRNG` streams), and comparing a GPU physics run to a CPU control
would fold that into the G3 subtraction.

## Gates

`make_inputs.py --check`: **3 pass, 0 warn, 0 fail**, 3 info, 1 post-run.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — **this run is what bounds it** |
| G3 laser-off control | *this run IS the control* (`intensity = 0`) | info |
| G4 `ray_cfl` check | 0.25 — moot, no beam | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc; bias bound ≤ 0.31 % | **pass** |
| G6 energy closure | — | post-run: with `E_abs` ≡ 0, the **entire** particle-energy gain is the grid-heating budget |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm | info |

## Media

*(not generated yet)*

## Result

*(running)*

## Retracted

Nothing.
