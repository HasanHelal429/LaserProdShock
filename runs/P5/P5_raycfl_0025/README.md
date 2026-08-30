# P5_raycfl_0025 — G4 ray_cfl ladder, fifth rung `ray_cfl = 0.025`

**Phase.** 5, `TEST_PLAN.md` §13. **Read the five rungs as a set, never one alone.**
**Question.** The first four rungs did not converge. Does halving the march once more put
`E_abs` inside the 1 % acceptance band, i.e. is `ray_cfl = 0.05` safe to produce on?
**Expected.** If `E_abs(0.025)` is within 1 % of `E_abs(0.05)`, the ladder has found its
asymptote and 0.05 is the production value. If it is not, absorbed energy on this target is
resolution-limited at every march tested and the phase's absorption numbers carry an
unquantified floor.
**Falsified by.** `E_abs` still moving by more than 1 % between 0.05 and 0.025, or the
deposition peak moving by more than one cell.

---

## Why this rung exists

Added 2026-08-29, after the original ladder ran on Perlmutter (array 57728667, all four
COMPLETED, `--verify` OK on each). Measured `E_abs`, J per absent dim, at 2.006 ps:

| `ray_cfl` | `E_abs` | Δ vs next coarser | `f_abs` peak | shutoff |
|---|---|---|---|---|
| 0.50 | 8.871e4 | — | 1.0000 | 0.460 ps |
| 0.25 (default) | 9.560e4 | +7.8 % | 1.0000 | 1.246 ps |
| 0.10 | 1.017e5 | +6.4 % | 0.6529 | not reached |
| 0.05 | 1.029e5 | **+1.18 %** | 0.7516 | not reached |

Three things came out of that, and each is worse than D4 anticipated:

* **0.05 is not demonstrably converged.** +1.18 % between the two finest rungs is above the
  1 % threshold this ladder set for itself. Not by much — but the threshold was not chosen
  arbitrarily, and the honest reading is "not shown to be converged", not "close enough".
* **The default 0.25 is 7.1 % below the 0.05 rung.** D4 inherited a "2.5 % excursion"; the
  real figure on this target is about three times that. Any P5 leg run at 0.25 understates
  absorbed energy by ~7 %, and absorption is the headline observable.
* **Coarse and fine disagree qualitatively, not just numerically.** 0.50 and 0.25 saturate
  at `f_abs` peak = 1.0000 and reach laser shutoff; 0.10 and 0.05 peak at 0.65 / 0.75 and
  never shut off within 2 ps. That is a different absorption *history*. A single converged
  number would not have revealed it — reading the rungs as a set did.

Non-monotonicity is confirmed as documented: `f_abs` peak rises 0.653 → 0.752 from 0.10 to
0.05 while `E_abs` rises monotonically throughout. This is exactly why the ladder has rungs
rather than a pair, and why a small 0.05 → 0.025 change would still not on its own prove
convergence — it has to be read against the whole set.

The deposition peak is the reassuring half: all four rungs put it within 0–2 cells (cell
1067 identically at the mid dump), so acceptance criterion A5 is essentially met. It is the
energy integral, not the deposition *location*, that has not settled.

## What it involves

Identical to `P5_raycfl_005` except `ray_cfl`. 20 300 steps = 2.0 ps = 0.054 `τ_own`,
~2030 `LASERDEP` samples, 10 deposition-profile dumps.

**Cost: ~12 min.** The four rungs ran 5:33 / 5:56 / 7:06 / 9:03 on one A100 (coarse to
fine), so halving again lands near 12–14 min. Fits `--qos debug` with room to spare.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

Identical to every other rung and to `P5_flashic`: the ladder varies `ray_cfl` and nothing
else, so any difference between rungs is the march and not the setup.

## Result

**Ran 2026-08-30, job 57753369, COMPLETED exit 0 in 12:53, `--verify` OK.
`E_abs` = 1.050e5 J per absent dim — `+2.04 %` on the 0.05 rung.**

**The ladder does not converge.** The step-to-step change does not shrink:

| `ray_cfl` | `E_abs` | Δ vs next coarser | `f_abs` peak |
|---|---|---|---|
| 0.50 | 8.871e4 | — | 1.0000 |
| 0.25 (default) | 9.560e4 | +7.77 % | 1.0000 |
| 0.10 | 1.017e5 | +6.38 % | 0.6529 |
| 0.05 | 1.029e5 | +1.18 % | 0.7516 |
| **0.025** | **1.050e5** | **+2.04 %** | 0.7188 |

The increment sequence is +7.77 / +6.38 / **+1.18** / **+2.04 %** — it goes *up* at the
finest step. The 1.18 % at 0.05 was therefore **not** an approach to an asymptote but a
coincidentally narrow step in a non-monotonic sequence, which is exactly the failure mode
D4 warned about and precisely why this ladder was specified to be read as a set rather than
as a pair. `E_abs` has risen **+18.4 %** in total from 0.50 to 0.025 and is still rising at
the finest march tested. `f_abs` peak oscillates rather than settling: 1.000, 1.000, 0.653,
0.752, 0.719.

**No march tested is demonstrably converged**, and the default 0.25 is **9.0 % below** the
finest rung.

The deposition peak remains stable — cell 1066–1068 across all five rungs, within ±1 cell at
every dump — so acceptance criterion A5 still holds. The failure is confined to the energy
integral, i.e. to *how much* is absorbed, not *where*.

## Retracted

**The plan to produce at `ray_cfl = 0.05` (set 2026-08-30) is retracted the same day.** It
rested on the 0.05 rung's 1.18 % residual reading as near-convergence; the 0.025 rung shows
it was not. Any P5 absorption number is resolution-limited until this is understood, and the
size of the limit is unbounded by the data in hand — `E_abs` has not turned over.

The four-rung result that "0.10 → 0.05 moves 1.18 %, marginally over threshold" is not
retracted, but it must not be read as "nearly converged". It is one step of a sequence that
does not settle.

## Retracted

Nothing yet. The claim this rung exists to test — that `ray_cfl = 0.05` is converged — is
explicitly **not** yet established; the four-rung ladder left a 1.18 % residual against its
own 1 % threshold. If 0.025 does not close it, the spine legs launched at 0.05 on
2026-08-30 inherit a resolution-limited absorption number and must be re-read in that light.
