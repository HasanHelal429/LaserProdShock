# Overview — the ray-tracing laser-deposition model and laser-driven shocks

The physics reference for `LaserProdShock`. `TEST_PLAN.md` turns this into runs;
`RESULTS.md` records what they found.

**Primary references**

- A. S. Hyder, W. Fox, K. V. Lezhnin, S. R. Totorica, *Ray-tracing laser-deposition model
  for plasma particle-in-cell simulation*, **Comput. Phys. Commun. 318, 109419 (2026)**;
  arXiv:2412.08543. — the model the WarpX operator ports.
- K. V. Lezhnin, S. R. Totorica, A. S. Hyder et al., *Particle-in-cell simulations of
  expanding high energy density plasmas with laser ray tracing*, **Phys. Plasmas 32, 022701
  (2025)**; arXiv:2409.17327. — the PIC-coupling companion.
- D. B. Schaeffer, W. Fox, J. Matteucci, K. V. Lezhnin, A. Bhattacharjee, K. Germaschewski,
  *Kinetic simulations of piston-driven collisionless shock formation in magnetized
  laboratory plasmas*, **Phys. Plasmas 27, 042901 (2020)**; doi:10.1063/1.5123229. — the
  shock physics, the seven criteria, the three timescales. Replicated in
  `../KinShock2020/` with a *prescribed* piston; here the piston is driven by a laser.
- W. Fox et al., **Phys. Plasmas 25, 102106 (2018)**; arXiv:1712.00152. — the heating/
  ablation surrogate model this project's laser replaces.

**Implementation under test**: `warpx-cda/Source/Particles/LaserDeposition/`, documented in
`warpx-cda/Docs/source/usage/parameters.rst` under "Laser deposition (ray tracing)", with
its development history in `warpx-cda/laser_deposition/LASER_DEPOSITION_PLAN.md` and its
accuracy characterisation in `warpx-cda/laser_deposition/ACCURACY.md`. **Read both of those
before adding a test** — they are why §1.1 of `TEST_PLAN.md` is short.

---

## 1. Why ray tracing rather than an EM antenna

WarpX's native laser support (`Source/Laser/LaserProfiles.*`,
`LaserParticleContainer.*`) is an **antenna**: it injects a fully resolved electromagnetic
wave by depositing currents on a plane. That requires resolving the laser wavelength on the
PIC grid, and it models neither collisional absorption nor refraction in underdense plasma.
For a long-scale-length, underdense-to-near-critical HED plasma, resolving λ₀ would demand a
grid far finer than the plasma features of interest.

The ray-tracing model instead treats the laser in the **geometric-optics (WKB) limit**: a
bundle of rays that refract in the plasma and deposit energy by inverse bremsstrahlung. The
grid then only has to resolve the *plasma*, not the light.

## 2. The model

### 2.1 Propagation

Rays propagate through a plasma of refractive index

```
n(x)² = 1 − n_e(x)/n_cr ,      n_cr = ε₀ m_e ω²/e² ,      ω = 2πc/λ₀
```

The operator integrates the eikonal ray equation

```
d/ds ( n dr/ds ) = ∇n
```

with an **RK4 marcher in arc length** (`ray_cfl` sets the step as a fraction of the smallest
cell), using multilinear interpolation of `n_e` with a consistent analytic gradient. Rays
bend toward lower density and **turn** at the reduced critical density

```
n_e = n_cr cos²θ₀      (Snell invariant n sinθ = sinθ₀)
```

At (near-)normal incidence the remaining intensity **reflects specularly** off the critical
surface and refracts back out, making a return pass.

### 2.2 Absorption

Intensity is attenuated by inverse bremsstrahlung, `dI/ds = −K I`, with

```
K = (ν_ei/c) · (n_e/n_cr) / √(1 − n_e/n_cr)

ν_ei = (4/3)√(2π) · Z_eff e⁴ n_e lnΛ / [ (4πε₀)² √m_e (k_B T_e)^{3/2} ]
```

so **`K ∝ Z_eff lnΛ n_e² T_e^{−3/2} / √(1 − n_e/n_cr)`**. The `1/√(1 − n_e/n_cr)` factor is
the group-velocity/path-length enhancement that makes `K` singular at the critical surface;
the operator integrates it **analytically** over a locally linear density profile up to
critical, so the absorbed fraction between the last cell and the reflection point is finite.

Three consequences drive everything in `TEST_PLAN.md`:

- **`n_e²`** — absorption is measured against `n_cr`, so the laser **pins the absolute
  density scale**. A scale-free heater run cannot simply be re-labelled as a laser run.
- **`T_e^{−3/2}`** — a cold target absorbs strongly and **shuts itself off as it heats**.
- **`Z_eff lnΛ`** — a linear, and empirically very strong, knob.

### 2.3 Coupling to the electrons

The absorbed power density `P_abs = K I` becomes a per-cell, per-electron heating rate
`H = P_abs/(n_e m_e)` [m²/s³], applied as an **isotropic Gaussian momentum kick**

```
Δu_i = √( (2/3) H Δt_dep ) · N(0,1) ,      i = x,y,z
```

so all absorbed energy goes to electron *heat* with **no bulk push**. This is the same
Monte-Carlo kernel as the `ParticleHeater` used in `../KinShock2020/`; the new physics is the
ray tracer that *produces* `H`, not the deposition. Ions are not heated directly (mass-ratio
suppression) — ion heating proceeds through the collision operator if enabled.

### 2.4 Temperature: `local` is the default and the right choice

`K ∝ T_e^{−3/2}` is evaluated from the **locally measured** electron temperature
(`temperature_mode = local`, the default): the CIC density pass also deposits `Σw u_i`,
`Σw|u|²` and a shape-weighted macroparticle count, so `k_B T_e = m_e(⟨|u|²⟩ − |⟨u⟩|²)/3` is
formed from the *group* moments on the *same* shape factor as `n_e`, with the local drift
subtracted. A per-cell coefficient `A = C/(k_B T_e)^{3/2}` is interpolated along the ray.

This matters for physics, not just accuracy. With a frozen `T_e` the drive is either
permanently full or permanently negligible depending on the number typed in — qualitatively
wrong for an ablating target. The upstream measurements: a frozen-`K` model over-deposits by
1.3× / 2.8× / 8.5× at 10²⁰ / 10²¹ / 10²² W/m². Guards: `temperature_floor` (defaults to
`electron_temperature`, so a cold plasma reproduces `fixed` exactly) and
`min_macroparticles_per_cell`. Because `T^{−3/2}` is convex, per-cell noise biases absorption
**high** — hence the several-hundred-ppc requirement (gate G5).

### 2.5 What the operator reports

With `warpx.verbose = 1`, one machine-parseable line per application:

```
LASERDEP step <n> t <s> Pabs <W> Eabs <J>   [Tlocalfrac <f>]
```

`P_abs` instantaneous, `E_abs` cumulative (per unit length in the invariant direction in
1D/2D), accumulated over all rays and reduced over ranks — **measured directly from the ray
tracer, so it is immune to grid heating**. `Tlocalfrac` is the `n_e²`-weighted fraction of
plasma that got a locally measured temperature rather than the floor.
`profile_intervals` / `profile_prefix` write the per-cell `(coords, n_e, H, P_abs)` table;
its sum matches `LASERDEP Pabs` to six digits. **Analyse the step-0 dump** — later dumps
drift as the kicks move electrons.

## 3. Units — everything hangs off λ₀

Since `ω_pe = ω₀` when `n_e = n_cr`, the skin depth at critical density is exactly

```
d_e,cr = c/ω₀ = λ₀/2π
```

At λ₀ = 1.053 µm: `n_cr = 1.005×10²⁷ m⁻³` (1.005×10²¹ cm⁻³), `d_e,cr = 0.1676 µm`.

This lands squarely on the experimental regime: **Schaeffer's Table I ablation density
(6×10²⁰ cm⁻³) is 0.6 `n_cr` and its upstream (4.8×10¹⁸ cm⁻³) is 0.0048 `n_cr` at 1 µm.** The
paper's HED realisation is therefore natural for a real 1 µm laser — the density contrast
(~125:1) is the hard part, not the absolute scale.

For a run with target 1.5 `n_cr`, ambient 0.06 `n_cr` (25:1), `m_i/m_e = 100`,
`v_A = 0.003 c`:

| | |
|---|---|
| `d_e,amb` | 0.684 µm |
| `d_i,amb` | 6.84 µm |
| `d_e(target)` | 0.137 µm — **5× smaller than the ambient's** |
| `B₀` | 74.7 T |
| `ω_ci0⁻¹` | 7.61 ps |
| `ρ_i0` at `v_p = 0.0196 c` | 44.7 µm = 65 `d_e,amb` |

The 5× skin-depth ratio *is* the scale-separation problem: one uniform grid, no AMR (the
operator asserts `finestLevel() == 0`).

## 4. The shock physics being driven

From Schaeffer 2020 (full treatment in `../KinShock2020/OVERVIEW.md`):

**Chain of events for a laser-driven perpendicular shock.** Laser crosses the tenuous
magnetized ambient nearly unabsorbed → absorbed in the target's coronal gradient and at the
critical surface → target electrons heat → ambipolar expansion drives an ion piston back up
the beam → piston sweeps up ambient plasma and magnetic flux (a **diamagnetic cavity**) →
compressed field reflects ambient ions → a perpendicular collisionless shock forms and
separates from the piston.

**Expansion-speed model (Eq. 1).** The ablation density follows the scale-free
`n_e = (n_ab − n_0) exp[−(z−z₀)/z₀] + n_0`, giving

```
v = (C_s,ab/2) · [ 1 − ln( (n_e − n_0)/(n_ab − n_0) ) ]
```

with `C_s,ab = √(Z k_B T_e,ab/m_i)`. Without an ambient, `v_p → 6.5 C_s,ab`; `v_sh → (4/3) v_p`
at low field, rising with `B₀` per the perpendicular RH relation (Eq. 2).

**The seven criteria.** A structure is a shock *precursor* if (1)–(6) hold, and a *shock*
once (7) does: (1) super-magnetosonic `M_ms > 1`; (2) collisionless `L/λ_ii > 1`; (3)
`n_e/n_e0 > 2`; (4) `B/B₀ > 2`; (5) ramp steepness on ~`d_i0`; (6) **magnetically reflected
ambient ions** (`v_z > v_sh`); (7) **separation from the piston** by ≥ ¼ `ρ_i0`. Criteria
(3)–(5) distinguish a real shock from interpenetrating flows or a mere piston compression;
(6) is the kinetic dissipation signature; (7) makes it dynamically independent.

**The three timescales**, nearly independent of `M_A` and `β_ab`, defined through the
reflected-ion functions `F(z,t)` and `G(t)`: `t*₁ ≈ 1 ω_ci0⁻¹` (onset, `z*₁ ≈ 1 ρ_i0`),
`t*₂ ≈ 2.5 ω_ci0⁻¹` (separation → a shock, `z*₂ ≈ 2.5 ρ_i0`), `t*₃ ≈ 5 ω_ci0⁻¹` (a
downstream develops, RH begins to apply). Formation needs only ≳ 1 `ω_ci0⁻¹` of drive —
which is why the laser's **shutoff time** `t_s` is a first-class quantity here.

**Negative controls.** With `B₀ = 0`: ambient ions are still accelerated, but there is no
magnetic compression, no strong ion heating, no secondary compression — no shock. With
`n_e0 = 0`: no ambient-ion structures at all. These prove the signatures are shock-specific,
and they are `TEST_PLAN.md`'s Phase 1 and Phase 2A.

## 5. Why this is hard, and the cautionary tale

**The tension.** A laser needs a near-critical target to absorb; a magnetized collisionless
shock wants a tenuous ambient with a large `ρ_i0`. One uniform grid must resolve both. That
scale separation is exactly why Fox 2018 and PSC prescribe a *heating operator* instead of a
laser — the surrogate is scale-free and can put the target wherever it likes.

**The cautionary tale.** `warpx-cda/laser_deposition/run_laser_shock/` produced compression
~2 in both `B` and `n_e`, a real diamagnetic cavity, and a front at 2.63 `v_A` — and was
reported as a "marginally supercritical shock". Phase-space analysis retracted it: **0.00 %
ion reflection**, upstream/downstream `f(u_z)` differing only by a −0.83 `v_A` shift and a
0.56 → 0.72 `v_A` broadening, and a **piston at only ~1 `v_A`, slower than the 2.63 `v_A`
compression it had launched**. A piston slower than its own wave is not driving it, and at
`v_ms = 1.15 v_A` that piston was subsonic — no shock could form at those parameters however
long the run. What the run actually produced was a freely-propagating fast magnetosonic pulse
from a genuine laser-driven ablation.

**The lesson, which is a working rule.** The `B` and density streaks look shock-like on their
own. Only the phase space distinguishes a driven shock from a decaying pulse. **Run the
phase-space diagnostic before making any shock claim** — see `CLAUDE.md`.
