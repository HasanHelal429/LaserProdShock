# P4_lez_kin — fully kinetic leg of the Phase-4 cross-code benchmark

> ## [DEFECTIVE] — diagnostics deleted 2026-08-28
> **Analytic Gaussian corona that fails the paper's own Fig-2 test (peak deposition zeta 4.13 vs FLASH 0.27), and `theta_e_init` 1.957e-4 = 100 eV, the retired IC convention. Its headline is retraction-ledger item 15.**
> 
> Superseded by: **P4_lez_kin_ic6**. `diags/` and `run.log` were removed to reclaim disk; the
> config, deck, `warpx_used_inputs` and this README are kept as the provenance record.
> Re-run from the config if the raw output is ever needed again.
> See `runs/P4/SUPERSEDED.md` for the full ledger.

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does the WarpX ray-tracing operator, driving a fully kinetic collisional
plasma, reproduce a *published, independently computed* radiation-hydrodynamics ablation
to the paper's own tolerances — 20 % in `n_e`/`T_e`/`T_i`, 10 % in flow speed?

**Status: config written, NOT LAUNCHED.** Blocked on the §12.3 tooling work (`deck.py`
emits no collision block) and gated on the D3 collision validation.

Spec: `TEST_PLAN.md` §12. Decisions: `runs/P4/README.md`. Reference: Lezhnin et al.,
*Phys. Plasmas* **32**, 022701 (2025).

---

## Hypothesis

The WarpX ray-tracing operator, driving a fully kinetic 1D plasma with Coulomb collisions,
reproduces the published FLASH radiation-hydrodynamics ablation of aluminium to the same
tolerances the paper reports for PSC: **20 % in `n_e`, `T_e`, `T_i` and 10 % in flow
speed**, over the underdense region, with the electron temperature plateauing near the
Manheimer steady-state value

```
T_e,SS = 5.94 mu^(1/3) Z^(-1/3) (lambda/1um)^(4/3) (I/I10)^(2/3) = 823 eV
```

This is the leg with the fewest closure assumptions. **If it disagrees with FLASH, the
prior should be that the fault is ours, not FLASH's** — and the first suspect is
collisions under a reduced mass ratio (see *Gate* below), not the laser operator, which
Phases 0–3 already characterised against its own upstream.

## Why it is worth running

Nothing in Phases 0–3 has been checked against an independent code. The operator was
verified against its PSC-derived upstream and the physics against scalings derived inside
this project. That is self-consistency, not validation. This run is the first external
check, and it is a strong one because the laser **pins the absolute density and temperature
scale** — a scale-free heater run could be re-labelled to match anything, and this cannot.

It is also the arbiter for `P4_lez_hyb`, which differs from it in exactly one thing: the
electron closure.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~~~~~~                                                        
      ^                                                                ^
      open                                                          open
      z = -50                                                  z = +950

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : Gaussian, L_n = 27 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 2000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 552960 steps = 54.66 ps
```

```
lambda0 = 1.064 um      I = 1e17 W/m^2 (= 1e13 W/cm^2)      Z = 13, fully ionised Al
mass    = m_Al/m_e = 2698, i.e. the paper's reduced m_p/m_e = 100
duration= 552960 steps = 26.9 ion response times = the paper's 1 ns pulse
```

The laser enters from `+z` and burns *into* the target, which sits against the `lo` end of
the box. The long 950 `d_e` vacuum run-out on the laser side is where the ablated plume
expands — that plume, not the target, is what the benchmark measures. The 50 `d_e` behind
the target is deliberately short: the paper compares the *ablated, underdense* plasma, and
the overdense interior is explicitly excluded from the acceptance criteria (§12.6), so
there is nothing to be gained by resolving more of the rear.

Three numbers in that diagram deserve to be read carefully:

- **10 `n_cr`, not 1.5.** Everywhere in Phases 0–3 the target is 1.5 `n_cr`. The paper's
  Appendix A scan (2/5/10/20 `n_cr`) finds `T_e` matches FLASH only for `n_max` ≥ 5 `n_cr`,
  and real solid Al is ~700 `n_cr`. A Phase-4 config is not a Phase-1 config with the laser
  turned up. The consequence is that **there is an interior critical surface** — the ray
  turns *inside* the plasma, which is the case where `ray_cfl` convergence is non-monotonic
  (gate G4, and why a ladder is declared).
- **`L_n` = 27 `d_e` is an analytic stand-in**, derived as the self-similar rarefaction
  scale `C_S t` at 0.1 ns = 2.69 ion response times. The paper does not use an analytic
  ramp — it starts PSC from the FLASH 0.1 ns snapshot. This is decision **D1** and the ramp
  is to be replaced once FLASH output lands.
- **54.66 ps is the full duration**, and it *is* the paper's 1 ns. See below.

### The two rescalings, which have different powers

| quantity | factor vs the paper's real-mass values | why |
|---|---|---|
| length | `√(1836/100)` = **4.29** | `d_i0 ∝ √m_i` |
| time | `1836/100` = **18.36** | `t ∼ L/v ∝ √m·√m = m` |

So the 1000 `d_e` box is **169.3 µm** of physical length where FLASH's is 800 µm, and this
run's **54.66 ps is the paper's 1000 ps**. Both facts are consequences of the reduced mass
ratio, not errors — but a figure that puts this run on a µm axis is wrong by 4.29×, and one
that puts it on a picosecond axis is wrong by 18.36×. Compare in normalised units only
(`TEST_PLAN.md` §12.2).

**The target is 10 `n_cr`, not the 1.5 `n_cr` used everywhere in Phases 0–3.** The paper's
Appendix A scan (2/5/10/20 `n_cr`) finds `T_e` matches FLASH only for `n_max` ≥ 5 `n_cr`.
A Phase-4 config is not a Phase-1 config with the laser turned up.

**The initial condition is analytic** (`scale_length_de: 27`), derived as the self-similar
rarefaction scale `C_S t` at 0.1 ns = 2.69 ion response times. The paper instead starts PSC
from the FLASH 0.1 ns snapshot. This is decision **D1** and the analytic profile is a
stand-in to be replaced once FLASH output lands.

## Gate — do not believe this run until D3 passes

PSC implements a *special correction* to keep `e-i` and `i-i` collision rates right under
reduced `m_p/m_e` and reduced `c` (their Ref. 47). **WarpX's `BinaryCollision` is not known
to have an equivalent.** If it does not, transport is distorted and nothing crashes — the
numbers are just wrong, which is the worst way for a run to fail.

So, before this run is interpreted: reproduce the paper's **Appendix B** (`e-i`
thermalisation against their Eq. B1, 2 `d_i` periodic box) and **Appendix C**
(conductivity). Both are seconds of compute. This is the same discipline as the project's
standing rule that no shock claim is made before the phase-space diagnostic runs.

Collisions cannot simply be dropped: the paper reports that turning off *either* collisions
*or* laser heating gives "drastically different plasma evolution".

## Cost, and the ppc ladder

| ppc(e) at `n_cr` | particles | CPU-h | GPU-h |
|---|---|---|---|
| 500 (configured) | 0.53 M | 0.70 | 0.09 |
| 2 000 | 2.13 M | 2.79 | 0.35 |
| 10 000 | 10.7 M | 14.0 | 1.8 |

**The ladder is the deliverable, not the largest run** — stop where the A1–A8 quantities
stop moving. Gate G5 (`T^(−3/2)` is convex, so per-cell noise biases absorption *high*)
means the low rungs should over-absorb; watching that bias shrink up the ladder *is* the
convergence evidence.

The paper's 10⁵ ppc is ~18 GPU-h and buys only the 10⁻⁵ `n_cr` tail. Note also that its ppc
is quoted **at `n_cr` with equal weights**, so it scales with density; ours does not. The
two numbers are not the same convention — compare resolved dynamic range, not ppc.

## Known deviations from the paper, all deliberate

| | Paper | Here | Why |
|---|---|---|---|
| Rear boundary | reflecting | `open` | the paper itself reports unphysical boundary reflection as a low-`n_max` artifact (Appendix A); `open` is Phase-0 validated |
| `lnΛ` | one global value | configured global (6.3), per-cell available | our operator is *better* here; §12.8 risk 4 says record both rather than silently switch |
| `dz` | 0.2 `d_e` | 0.5 `d_e` | project default and first rung of the resolution ladder |
| Chamber gas | none in PSC, 10⁻¹⁰ g/cm³ in FLASH | none | matches PSC; PIC cannot resolve that density |
| `m_e c²` | 60 keV (reduced `c`) | real `c`, real `m_e` | WarpX cannot reduce `c`; at 823 eV the flow is non-relativistic so this affects step count only |

## Reading the output

**Compare in normalised units** — `(z/d_i0, t/(d_i0/C_S0))` with each code using its own
`d_i0`, densities in `n_e/n_cr`, temperatures in absolute eV. Never overlay this run on
FLASH against a µm axis: our 1000 `d_e` box is 169.3 µm of physical length while FLASH's is
800 µm, and the ratio is the mass-ratio reduction `√(1836/100)` = 4.29. This is
`TEST_PLAN.md` §12.2 and it is the trap most likely to produce a wrong figure in this phase.

Note also that `deck.py` forms `di = de*sqrt(mass_ratio)`, which is the **aluminium** skin
depth (51.94 `d_e`). The paper's `d_i0` is the **proton** skin depth at `n_cr`, = 10 `d_e`.
Comparison figures use the paper's.

## Result

**Not yet run.** Blocked on the §12.3 tooling (`deck.py` emits no `collisions:` block) and
gated on D3 (the collision-module validation). Nothing is claimed here until both clear.

Expected, recorded now so it can be falsified: passes A1–A8 at the paper's tolerances, with
the `T_e` plateau near `T_e,SS` = 823 eV.

## Retracted

Nothing yet. Two corrections were made to this run's *design* before launch, both worth
keeping visible because each would have produced a confidently wrong number:

1. **G3 was initially declared unnecessary**, on the argument that the cross-code comparison
   is a stronger attribution test than a laser-off control. That is wrong. With
   `dz/λ_D` = 113, grid heating would have contaminated `T_e` — the one quantity the whole
   benchmark turns on — and it would have corrupted both the measurement *and* our reading of
   any disagreement. `P4_lez_kin_off` now exists.
2. **The `ray_cfl` ladder was initially pointed at `studies/exit_overshoot`.** That ladder was
   measured on a 1.5 `n_cr` target with *no interior critical surface*. This run is 10 `n_cr`,
   the ray turns inside the plasma, and that is precisely the regime where G4 warns that
   `ray_cfl` convergence is non-monotonic. A fresh ladder at this density is required.
