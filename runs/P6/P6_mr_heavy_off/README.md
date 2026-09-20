# P6_mr_heavy_off — G3 laser-off control for `P6_mr_heavy`

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** How much of `P6_mr_heavy`'s heating is the GRID rather than the laser?
**Expected.** A heating background that differs BETWEEN legs — the full and light legs run
`dz/λ_D` = 58.1, the heavy leg 249.0 — so the subtraction is not a common-mode cancellation.
**Falsified by.** A background indistinguishable across the three legs, which would mean
`dz/λ_D` is not driving grid heating in this regime and the heavy leg's main risk is absent.

---

## What this run is

Identical to `P6_mr_heavy` in every respect — same mass convention, same grid, same lifted FLASH
initial condition, same duration, same seed — except `laser.intensity = 0`.

**Why it is mandatory rather than optional here.** The three legs do NOT share a
grid-heating background. An unsubtracted comparison would read that difference as physics,
which is precisely the error G3 exists to prevent.

A G3 subtraction is only meaningful against a run differing in the laser **alone**, which is
why each leg carries its own control rather than sharing one. Pointing a leg at another
leg's control was a real defect once: `P5_flashic` briefly pointed at `P5_full_off`, which
carries a different initial condition.

## Geometry

Identical to `P6_mr_heavy`.

## Gates

Identical to `P6_mr_heavy` except G3, which this run exists to satisfy.

## Cost

Identical to `P6_mr_heavy`.

## Result

NOT YET RUN.

## Retracted

Nothing yet.
