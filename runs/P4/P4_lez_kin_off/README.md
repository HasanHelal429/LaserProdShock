# P4_lez_kin_off — G3 laser-off control for `P4_lez_kin`

**Phase.** 4, `TEST_PLAN.md` §12, gate G3 (§6)
**Question.** How much of `P4_lez_kin`'s electron temperature rise is inverse
bremsstrahlung, and how much is numerical grid heating at `dz/λ_D` = 113?

**Status: config written, NOT LAUNCHED.** Runs with, and is only meaningful beside, its
parent `P4_lez_kin`.

Spec: `TEST_PLAN.md` §12, gate G3 (§6).

---

## Why this run exists

`P4_lez_kin` measures an electron temperature and compares it to FLASH at **20 %**. Gate G2
reports `dz/λ_D` = **113** in the cold dense target — badly under-resolved, which is normal
for this project and harmless when the quantity of interest is a piston speed, but *not*
harmless when the quantity of interest is `T_e` itself.

Numerical grid heating raises `T_e` for free. Without this control there is no way to tell
an inverse-bremsstrahlung temperature rise from a finite-grid one, and a cross-code
disagreement could not be attributed to either. The comparison against FLASH does **not**
substitute for it: grid heating would corrupt both the measurement *and* our reading of the
disagreement.

At 500 ppc this costs ~0.09 GPU-h. It is the cheapest insurance in the phase.

## Geometry

Bit-identical to `P4_lez_kin` in every respect except `laser.intensity = 0`.

`intensity = 0` rather than `intervals = 0` is deliberate: `config.py` detects a
control by `intensity == 0` (so gate G3 recognises the pair), and the deck generator
keys off the same value. Gating `intervals` alone would have left the run looking
un-controlled to the gates.

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ####~~~~~~                                                        
      ^                                                                ^
      open                                                          open
      z = -50                                                  z = +950

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : Gaussian, L_n = 27 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 2000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 552960 steps = 54.66 ps
```

**The diagram above is the parent's.** `geometry_diagram()` renders this run with an
explicit `x  LASER OFF (I = 0)` marker in place of the arrow, since it reads
`laser.intensity` — one more reason `intensity` is the right lever. The box, target and grid
are otherwise exactly the parent run's.

## What to measure

| | Expectation |
|---|---|
| `T_e(t)` in the target | should stay near its 100 eV initial value. Any *rise* is grid heating, and it must be subtracted from — or at minimum quoted alongside — the parent's `T_e` |
| `LASERDEP Pabs`/`Eabs` | identically zero. A non-zero value means the operator was not gated, which is a deck bug, not a physics result |
| Total energy | should be conserved to the same tolerance G6 asks of the parent |

**The pass condition is a number, not a vibe:** the `T_e` rise here must be small compared
with the 20 % tolerance the benchmark is judged at. If grid heating alone moves `T_e` by
more than a few percent over 54.66 ps, the resolution has to change before `P4_lez_kin`
means anything.

## Result

**Not yet run.** Launches with its parent.

## Retracted

Nothing yet. One design correction before launch: the run was first written with
`intervals: 0` as the off switch. `config.py` detects a control by `intensity == 0`, so the
gates did not recognise it as one and G3 still warned on the pair. Switched to
`intensity: 0.0`, the project's established lever.
