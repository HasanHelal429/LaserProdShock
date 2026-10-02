# P6_mr_light_sim — leg B rebuilt: reduced mass, similarity-scaled (μ = 0.0545)

**Phase.** 6, `runs/P6/README.md` (the mass-convention experiment)
**Question.** At m_i/m_e = 2698 and a real electron, built the project's way, does the plume
`T_e` fall by `mu^(1/3)` = 0.379 relative to the mu = 1 reference?
**Expected.** `T_e` light/full ~0.379 and optical depth down by `mu^0.490`, both fitted on
similarity-scaled legs. Geometry on the normalised axes should START on FLASH's.
**Falsified by.** light/full far from 0.379 on a leg whose IC is verified to match FLASH --
which would mean the 0.381 measured on the mis-built `P6_mr_light` was luck.

---

## What this run is

Replaces `P6_mr_light`, retracted 2026-09-23 because only the TIME family of HANDOFF.md 6 was
applied. Here all three are: lengths x s, times x s^2, velocities x 1/s, with
s = sqrt(2698/49542) = 0.23336 = 1/sqrt(18.3625). Because s is exactly 1/sqrt(me_scale), the
geometry in `d_e` is IDENTICAL to `P6_mr_heavy`'s, and so is the cell count.

`ic_flash.yaml` is the mu = 1 lift with `z_de` x s and `v_z/c` x 1/s; `n/n_cr` and `T` (raw eV,
HANDOFF 5) unchanged. An exact transform of the same handoff, not a re-fit.

**Verified before launch** against FLASH's handoff on the normalised axes:

| zeta | FLASH v/C_S0 | this leg | retracted leg |
|---|---|---|---|
| 2 | 1.726 | 1.733 | 0.200 |
| 5 | 3.398 | 3.410 | 0.299 |

n/n_cr at zeta 2 / 5: FLASH 0.093 / 8.35e-4, this leg 0.101 / 8.38e-4, retracted 0.58 / 0.27.

## Geometry

`d_e` = 0.1693 um (real electron), `dz` = 0.5 `d_e`, 5136 cells, axis -121.6819 -> 2446.3181 `d_e`,
497700 steps = 24.26 `tau_own` = 49.2 ps.

## Gates

As `P6_mr_heavy` for G1/G8 in `d_e`; G9 **warn**, mu = 0.0545 (intended).

## Cost

~1.2 h at the heavy leg's measured 7192 steps/min on the same cell count -- ~1/60 of the reference.

## Result

NOT YET RUN.

## Retracted

Nothing yet.
