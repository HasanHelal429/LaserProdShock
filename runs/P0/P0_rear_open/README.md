# P0_rear_open — is the region behind the target removable? (rear material removed)

**Phase.** 0, follow-up to the boundary decision
**Question.** The laser enters at +z and the ablation flows back toward +z, so the region
*behind* the target looks like it need not be simulated. Can the domain be truncated at the
target's rear face — saving 20 % of the cells here — without changing the front-side
ablation?

**Two facts established before running this** (RESULTS 2026-07-28):

1. **The laser genuinely cannot see behind the target.** Peak `n_e/n_cr` *rises* 1.55 →
   1.81 over the run — the target **compresses** rather than rarefying — so the ray always
   turns at the critical surface inside the slab and never reaches the rear boundary. The
   exit-overshoot therefore does not apply there either.
2. **But the rear is not quiescent.** By 2.35 ps, **6.95 % of the target ion mass** has
   moved behind z = −60, reaching z = −87 with `u_z` down to **−8.7 C_s** — a real
   rear-side rarefaction moving away from the laser. Truncating changes what happens to
   that momentum, so the question is empirical, not obvious.

**Expected.** The rear rarefaction drains through an absorbing wall, so its mass and momentum leave immediately instead of expanding into a resolved region. Expect the front side to be **closer** to the reference than the reflecting case, since the reference also lets the rear material go — just after resolving 40 d_e of its flight first.
**Falsified by.** Any front-side difference from `P0_bc_open_B` larger than the ppc noise
floor — in `f_abs(t)`, `E_abs(t)`, `n_e(z)` for z > −40, the front-side ion phase space, or
the target ions' net +z momentum. A difference means the rear region is dynamically coupled
to the front and cannot be truncated at this target thickness.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #########~~~~~~~~~~~~~~~~~........................................
      ^                                                                ^
      open                                                          open
      z = -60                                                  z = +100

  #  target flat top : 1.5 n_cr, 20 d_e thick, centred at -50 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = -40)
  .  ambient        : 0.06 n_cr, theta_e = 0.005  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 320 cells, dz = 0.5 d_e, dt = 0.09783 fs, 24000 steps = 2.348 ps
```

## Setup

`P0_bc_open_B` with `geometry.axis.lo_de: −100 → −60` (the target's initial rear face) and
`geometry.boundary.axis.lo: open → open`. Everything else — target, laser, field, `dz`,
duration, ppc — is unchanged, so the front side is identical by construction and any
difference is attributable to the truncation. 320 cells instead of 400.

*Caveat on `reflecting`:* it is `pec` fields + **specular** particle reflection, which flips
`v_z` but leaves the gyro-coupled `v_perp` untouched. `KinShock2020` documents a ~5 %
near-wall artifact from exactly that and prefers a π-rotation `symmetry` boundary, which
this project's boundary map does not yet offer. The wall here is at the target rear, far
from the shock region, but the caveat belongs on any near-wall reading.

Parent: `P0_bc_open_B` (declared as `controls.full_domain_reference`).

## Cost

320 cells × 4 species (200 ppc target, 48 ambient), 24 000 steps → 2.348 ps.
**20 % fewer cells than the reference** — which is the point. See `progress.log`.

## Gates

Unchanged from `P0_bc_open_B` (same `dz`, `cfl`, densities, ppc): G1 = 0.303, G2 target 61 /
ambient 1.73, G5 pass at 200 ppc. G3 and G4 warn as before.

## Media

*(not generated yet)*

## Result

Ran 24 000 steps (2.348 ps) in 3.5 min at 4 threads (vs 4.7 min for the 400-cell
reference). `--verify` OK.

**VERDICT: valid. Truncating the domain at the target's rear face with an `open` boundary
reproduces the front-side ablation, at 20 % fewer cells.** Against `P0_bc_open_B`:

| front-side observable | agreement |
|---|---|
| target-ion count at z > −40 | **+0.1 %** |
| `n_e(z)` at z > −40, t = 2.348 ps | median 5.6 %, 90th pct 12.5 % — at the ppc noise level |
| `E_abs` (integrated over the run) | **−0.6 %** (2.141e5 vs 2.155e5 J/m²) |
| total target-ion `p_z` | **−3.4 %** (−0.0305 vs −0.0315) |
| plume front position | within **1.0 d_e** (2 cells) of 30 d_e travelled |

The 5.6 % median density difference is not a systematic: `P0_rear_reflect` shows 4.8 % on the
same measure, so both sit in the run-to-run scatter rather than trending.

**Do NOT read the `f_abs(0)` difference as evidence.** It reads 0.3108 here vs 0.2827 for the
reference (+9.9 %), which looks damning until you measure the noise floor:
`studies/fabs_noise/` shows `f_abs(0)` has a **10.4 % 1σ and a 30.6 % full spread across six
runs differing only in RNG seed**. The step-0 profile dumps localise it — essentially the
whole difference sits in the single cell containing the critical surface, where
`K ∝ 1/√(1 − n_e/n_cr)` turns per-cell density noise into large power swings. Use `E_abs`,
which integrates hundreds of applications and agreed to 0.6 %.

**Why it works.** The ray turns at the critical surface inside the slab and never reaches the
rear boundary (peak `n_e/n_cr` *rises* 1.55 → 1.81, so the target never goes transparent), and
an `open` rear lets the rear rarefaction leave — which is what the full domain also does,
just after resolving 40 d_e of its flight first. Nothing that matters to the front side is
lost.

**Caveat on scope.** This is verified for *this* target (20 d_e thick, 1.5 n_cr) over *this*
duration (2.35 ps ≈ the rear rarefaction's slab-crossing time). A thinner target, or a longer
run, couples the two faces more strongly. Re-check if either changes materially.

## Retracted

Nothing.
