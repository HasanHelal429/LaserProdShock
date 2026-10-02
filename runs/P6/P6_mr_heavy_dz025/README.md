# P6_mr_heavy_dz025 — the heavy leg at twice the resolution (decision D6)

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** Is the heavy leg's geometry offset from the mu = 1 reference a GRID effect or a
PHYSICS effect of the heavy electron?
**Expected.** Two hypotheses, opposite predictions. Under-resolution (heavy resolves the
physical profile 4.29x more coarsely than full): `zeta_cr`, `L_n`, `zeta_front` move TOWARD
`P6_mr_full`. Suppressed conduction (Spitzer kappa ~ m_e^-1/2, 4.285x weaker at me_scale
18.36): they do NOT move, and the `T_e` overshoot persists.
**Falsified by.** Neither hypothesis survives a result that moves AWAY from full.

---

## What this run is

`P6_mr_heavy` with `dz_over_de` 0.5 -> 0.25 and nothing else changed: same mass convention,
same rescaled IC table, same ppc per cell, same duration. Condition for running it (D6: "if C
disagrees with A, the first suspect is the grid") was met on 2026-09-23: at tau_own 23.73,
heavy's `zeta_cr` / `L_n` / `zeta_front` sit at 0.42 / 0.70 / 0.69 of full's.

Halving `dz` halves `dt` (cfl fixed), so steps double; all diagnostic intervals double to keep
the physical dump cadence identical to the parent's, so frames compare one-to-one.

## Geometry

`d_e` = 0.7257 um, `dz` = 0.25 `d_e` = 0.181 um (full: 0.0847, parent: 0.363), 10272 cells,
axis as parent, 4266000 steps = 903.5 ps.

## Gates

G1 `omega_pe*dt` halves (0.277). G2 `dz/lambda_D` 249 -> 124.5. G8 doubles. G9 pass, mu = 1.

## Cost

~20 h estimated (2x cells, 2x steps on the parent's ~4.9 h); chained across two 24 h segments.

## Result

NOT YET RUN.

## Retracted

Nothing yet.
