# P4_lez_kin_thick_off — the G3 laser-off control for `P4_lez_kin_thick`

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** How much of `P4_lez_kin_thick`'s electron energy gain is grid heating rather
than laser absorption?

**Why this run exists even though G3 already passed.** `runs/README.md`: *a longer run needs
its own control, because grid heating accumulates with step count.* `P4_lez_kin_ic6_off`
measured the heating budget as **negative** (electrons *cool* by 35 %) — but that bounds
`ic6`'s cell×step budget. This run is **1.667 × the steps and 1.68 × the cells**, so it has
~2.8 × the opportunity, and the cold solid it adds is exactly the Debye-under-resolved region
(G2 = 58) where heating would originate.

**Differs from the physics run in `laser.intensity` ALONE** — verified by
`tests/test_structures.py`, which renders both decks and diffs them rather than trusting that
two configs stayed in step.

**Expected.** Electron energy **falls**, as it did on `ic6_off` (−1.7936e5 J against the
driven run's +1.3347e6 J), with the loss turning up in the ions via the ambipolar
rarefaction. A *positive* excursion of more than a few percent of the driven gain would
invalidate the parent measurement.

**Falsified by.** Net electron heating in the absence of a laser.

## Geometry
Identical to `P4_lez_kin_thick` — see that README. 8416 cells, 3686400 steps.

## Cost
Cheaper than the driven run: no ray march. `ic6_off` was 17 min against `ic6`'s 21 min
(0.81 ×).

## Gates
G1/G2/G4/G5/G7 identical to the physics run by construction. G3 is what this run *is*.

## Result
_Pending._

## Retracted
Nothing yet.
