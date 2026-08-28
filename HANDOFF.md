# HANDOFF.md — FLASH → WarpX, and what the reduced ion mass does to it

How the Phase-4 benchmark is set up, quantity by quantity, and why the two codes end up
reporting different temperatures and different ablation sound speeds for what is nominally the
same problem. Written 2026-08-28 against the measured sweep; every number here is either read
from a deck or measured from a completed run.

Companion files: `OVERVIEW.md` (the deposition model), `TEST_PLAN.md` §12 (the plan),
`RESULTS.md` (`CURRENT STATE` block first — many older numbers are superseded),
`GOTCHAS.md` "Cross-code comparison" (the operating rules).

---

## 1. The FLASH scenario

FLASH runs the *real* problem, in real units, with no similarity transform anywhere.

| | value | where |
|---|---|---|
| geometry | 1D Cartesian, `xmin` 0 → `xmax` 0.08 cm = **800 µm** | `flash.par` |
| target | **50 µm** solid aluminium slab, ρ = **2.7 g/cm³**, starting at x = 0 | `sim_targetHeight`, `sim_rhoTarg` |
| target ionisation | A = 26.9815, Z = 13 (fully ionised in the corona) | `ms_targA`, `ms_targZ` |
| initial temperature | **290 K** — a genuinely cold solid, all three of `tele`/`tion`/`trad` | `sim_teleTarg` |
| chamber gas | 1e-10 g/cm³ aluminium vapour, a numerical floor | `sim_rhoCham` |
| laser | 1.064 µm, **1e13 W/cm²**, normal incidence, spatially uniform | `ed_wavelength_1`, `ed_power_1_2` |
| pulse | linear rise 0 → 0.1 ns, flat top to 1.0 ns, off at 1.001 ns | `ed_time_1_*` |
| physics | radiation-hydrodynamics, PROPACEOS EOS + 1-group opacity, ray-traced IB | `Al_1group_FLASH.prp` |
| duration | 1.0 ns, 51 plotfiles every 0.02 ns | delivered 2026-08-17 |

**The peak electron density is 795 n_cr.** Solid Al at 2.7 g/cm³ with Z = 13 gives
n_e = 7.83 × 10²⁹ m⁻³, and `n_cr` at 1.064 µm is 9.848 × 10²⁶ m⁻³. Remember that number — it
is the single reason the PIC codes cannot simply repeat this run.

What FLASH produces is an *ablation flow*: the laser burns through the low-density corona,
deposits by inverse bremsstrahlung near the critical surface, and drives a rarefaction that
carries mass off the target at roughly the sound speed. The quantities the benchmark cares
about are the plume electron temperature, the density scale length, and the flow velocity.

---

## 2. Why WarpX cannot just run the same thing

A PIC code must resolve the Debye length and the plasma period, both set by the **electron**.
At 795 n_cr and a cold solid, λ_D is Ångström-scale; the project's uniform grid already sits at
`dz/λ_D` = 58 in the *10 n_cr* target, which is a deliberate, documented departure (gate G2).
Resolving a real solid is not a matter of a bigger machine.

So the PIC legs make two concessions, and it is important that they are *separate*:

1. **Density is capped at 10 n_cr.** Both PSC and WarpX do this; it is the paper's Appendix-A
   choice. The overdense interior is simply not represented, which is why `ne_peak` is never
   comparable between FLASH and a PIC leg (795 vs 10).
2. **The run starts at t = 0.1 ns, not t = 0.** Rather than simulate the cold solid being
   heated, the PIC legs are handed FLASH's state at the end of the laser ramp — a plasma that
   is already hot, already expanding, and already has a corona.

Concession 2 is the handoff, and it is the subject of the rest of this file.

---

## 3. The normalisation both codes share

Three scales are built from the **laser** and the **real electron**, so they are identical in
FLASH, PSC and every WarpX leg:

```
n_cr    = eps0 m_e omega_0^2 / e^2          = 9.848e26 m^-3
d_e,cr  = c/omega_0 = lambda_0 / 2pi        = 0.1693 um
```

Two more are built from the **ion**, and these are where the trouble starts:

```
d_i0    = c/omega_pi at n_cr, PROTON mass   = 7.256 um   (real)
C_S0    = sqrt(Z k T_e0 / m_i), T_e0 = 823 eV, ALUMINIUM mass = 1.956e5 m/s   (real)
tau     = d_i0 / C_S0                       = 37.098 ps  (real)
```

`d_i0` uses the **proton** mass and `C_S0` uses the **aluminium** mass. That mixed convention
is the paper's, not ours, and it is kept because it reproduces their "0.1 ns = 2.69 ion
response times". The handoff time t = 0.1 ns is therefore **τ = 2.696**.

All comparison axes are `ζ = z/d_i0` and `τ = t/τ_own`, each leg on **its own** `d_i0` and
`τ_own`. On those axes the geometry of the problem is the same in every code.

---

## 4. The mass-ratio reduction, exactly

WarpX builds its ion as `m_i = mass_ratio × m_e` (`deck.py:303`), with
`reference.mass_ratio` = 2698 = 26.9815 × 100 — the paper's `m_p/m_e` = 100. So:

```
m_i,WarpX = 2698 x m_e = 2.458e-27 kg  =  0.0546 x real aluminium
```

Define **µ = m_i,leg / m_i,real**. The WarpX legs run µ = 0.0546; the real-mass leg runs µ = 1.

**The electron is never touched.** This is the fact that governs everything else:

| quantity | FLASH / real | WarpX at µ = 0.0546 | ratio | scales as |
|---|---|---|---|---|
| `m_e` | 9.109e-31 kg | 9.109e-31 kg | 1.000 | **µ⁰** |
| `d_e = λ₀/2π` | 0.1693 µm | 0.1693 µm | 1.000 | **µ⁰** |
| `dz`, `dt`, `λ_D`, `ω_pe·dt` | — | *bit-identical* | 1.000 | **µ⁰** |
| `m_i` | 4.480e-26 kg | 2.458e-27 kg | 0.055 | µ |
| `d_i0` | 7.256 µm | 1.693 µm | 0.233 | µ^(1/2) |
| `C_S0` (at 823 eV) | 1.956e5 m/s | 8.351e5 m/s | 4.270 | µ^(−1/2) |
| `τ_own` | 37.098 ps | 2.028 ps | 0.055 | µ |
| `T_ss` (Manheimer) | 823 eV | 312 eV | 0.379 | µ^(1/3) |

Two consequences worth stating plainly:

* **Reducing the ion mass buys nothing in resolution.** `dz` and `dt` are electron quantities
  and do not move — measured bit-identical across the whole 73× sweep. The entire saving is a
  smaller box (`∝ µ^(1/2)`) run for a shorter time (`∝ µ`), i.e. `cost ∝ µ^(3/2)` in 1D.
* **PSC does the opposite.** It reaches `m_i/m_e` = 100 by making the *electron* 18.4× heavier
  and keeps a real aluminium ion. Same ratio, opposite implementation, completely different
  physical system. See `GOTCHAS.md`.

---

## 5. The handoff, quantity by quantity

`xcode_compare.flash_series()` reads FLASH's plotfile at t = 0.1 ns and converts:

| FLASH variable | conversion | becomes |
|---|---|---|
| `dens` × `ye` | `× N_A × 1e6`, then `/ n_cr` | `n_e / n_cr` |
| `tele`, `tion` | `/ 11604.5` (K → eV) | `T_e`, `T_i` in **eV** |
| `velx` | `× 1e-2`, then `/ C_S0` | `v_z / C_S0` |
| block coordinate | `× 1e-2`, minus the interface, `/ d_i0` | `ζ` |

That profile is then fitted into the WarpX config as a small set of primaries
(`P4_lez_kin_mr100/config.yaml`):

```yaml
density_over_ncr:      10.0        # CLIPPED from FLASH's 795 -- concession 1
thickness_de:          45          # = 4.5 d_i0, the paper's target
center_de:            -22.5        # so the solid-vacuum interface sits at z = 0
corona_profile:        exponential
scale_length_de:       6.955       # = 0.6955 d_i0, fitted to FLASH at 0.1 ns
corona_offset_de:      2.3144
theta_e_init:          7.4032e-4   # = 378.3 eV   <- FLASH's ablation layer, RAW eV
theta_i_init:          2.2622e-4   # = 115.6 eV   <- so T_e/T_i = 3.27 at t = 0
theta_e_solid:         2.466e-6    # = 1.26 eV    <- NOT FLASH's 290 K; see below
drift_uz_de:      [1.5271e-3, 1.5593e-4]   # v_z/C_S0 = 0.548 + slope, the rarefaction
```

Three things about this list are load-bearing.

**The handoff state is already in motion.** FLASH's corona at 0.1 ns carries
`v/C_S0 = 0.548 + 0.05598 ζ`. Starting the PIC leg at rest would be a different problem, so
`drift_uz_de` seeds that ramp. It matters more than it looks — see §7.3.

**The temperatures transfer in RAW eV, not in similarity units.** `theta_e_init` = 378.3 eV is
FLASH's actual ablation-layer temperature. Lengths and times transfer in **similarity** units
(`d_e`, `d_i0`, `τ_own`). That mixture is a deliberate choice — it keeps the IC physically the
state FLASH computed — and it is the single origin of the absorption discrepancy in §7.4.

**The cold solid is not transferred.** FLASH's 290 K = 0.025 eV solid is Debye-unresolvable on
a uniform grid, so the WarpX solid starts at 1.26 eV. A known departure, not a fit.

---

## 6. The transfer rules: three scaling families

Changing `mass_ratio` requires rescaling the config by `s = √(mass_ratio / 2698)`, and there
are **three** families, not two. The run READMEs list only the first two; the third was found
on 2026-08-27 after it corrupted a run.

| family | keys | factor |
|---|---|---|
| **lengths quoted in `d_e`** | `thickness_de`, `center_de`, `scale_length_de`, `corona_offset_de`, `axis.lo_de`, `hi_de`, `max_grid_size` | `s¹` |
| **times and step counts** | `mass_ratio`, `max_step`, `laser.profile_intervals`, the four `diagnostics.*_intervals` | `s²` |
| **velocities** | `drift_uz_de[0]` (`uza`) | **`1/s`** |
| **velocity ramps per `d_e`** | `drift_uz_de[1]` (`uzb`) | **`1/s²`** |
| *held fixed* | `dz_over_de`, `cfl`, `ppc`, `particle_shape`, every `theta_*`, `density_over_ncr`, `charge_state`, all laser and collision keys | 1 |

Why the third family exists: `uza` is a momentum in units of `c`, and the physics needs
`v/C_S0` preserved. Since `C_S0 ∝ µ^(−1/2) ∝ 1/s`, a *fixed* `uza` gives a starting corona `s`
times too fast in normalised units. `uzb`'s ramp is quoted *per `d_e`* while the flow is per
`d_i0`, so it takes the square.

**Check `uza/C_S0` against FLASH's 0.548 on every new leg.** Only `mr100` had it right by
accident — `1.5271e-3` was chosen against *its* `C_S0`.

| leg | `uza/C_S0` as built | correct |
|---|---|---|
| `mr25` | 0.274 (2× too slow) | 0.548 |
| `mr100` | **0.548** ✓ | 0.548 |
| `mr400` | 1.096 (2× too fast) | 0.548 |
| `mrreal` | 2.349 (4.29× too fast) | 0.548 |

All four legs have now been re-run on the corrected drift, and both fitted exponents moved
*toward* their theories while the scatter nearly halved — `T_e` `µ^0.293 → µ^0.322` (theory
0.333) and optical depth `µ^0.454 → µ^0.490` (theory 0.500), scatter 8.3 % → 4.5 %. The drift
error was adding real scatter to the sweep, and removing it sharpens both results.

The temperature is **not** a sensitive tell for this bug: the broken real-mass leg's `T_e` was
off by 5 % while its density scale length was off by **4×**. Check the geometry — `ζ_cr` and
`L_n` against FLASH — not the temperature.

---

## 7. Why the numbers come out different

### 7.1 Temperature in raw eV — expected, and *not* a discrepancy

Manheimer's steady state for an ablating plasma is

```
T_e,SS  =  5.94  mu^(1/3)  Z^(-1/3)  lambda^(4/3)  I^(2/3)
```

with `mu` the ion mass factor. **`T_ss` carries `µ^(1/3)`.** A leg run at µ = 0.0546 is
*targeting* 823 × 0.0546^(1/3) = **312 eV**, not 823 eV. Comparing raw eV across legs shows a
2.638× "disagreement" that is the unit map working correctly.

Measured across the sweep, all at `τ_own` = 5.39:

| leg | µ | plume `T_e` | `T_e / (823 µ^(1/3))` |
|---|---|---|---|
| `mr25_drift` | 0.0136 | 113.9 eV | 0.580 |
| `mr100` | 0.0545 | 157.7 eV | 0.506 |
| `mr400_drift` | 0.218 | 271.0 eV | 0.547 |
| `mrreal_drift` | 1.000 | **440.2 eV** | 0.535 |
| FLASH | 1.000 | 647.0 eV | 0.786 |

Fitted over all four corrected legs, `T_e ∝ µ^0.322` against the predicted `µ^(1/3)` = 0.333 —
**3.3 % over a 73× mass range**, with 4.5 % scatter. **So compare `T_e/T_ss(own µ)`, never raw eV.** The remaining
WarpX↔FLASH gap, 0.69×, is a real code difference and is discussed in §8.

### 7.2 The ablation sound speed — and the trap in it

There are **two** sound speeds in play and they scale differently. This has produced a
retracted claim (`RESULTS.md` ledger item 13, a "36 % slow" that was pure normalisation).

```
C_S0  = sqrt(Z k * 823 eV / m_i)      the NORMALISATION CONSTANT, fixed at the reference T
C_S   = sqrt(Z k T_e,measured / m_i)  the PHYSICAL sound speed of that leg's own plume
```

`C_S0 ∝ µ^(−1/2)` — a 4.27× effect at µ = 0.0546. But the leg's own temperature is also lower
by `µ^(1/3)`, so the *physical* speed is

```
C_S(leg) / C_S(real)  =  sqrt( mu^(1/3) / mu )  =  mu^(-1/3)  =  2.638
```

| leg | `C_S0` at 823 eV | `C_S` at its own `T_e` | ratio |
|---|---|---|---|
| FLASH / real | 1.949e5 m/s | 1.728e5 (647 eV) | 0.887 |
| WarpX `mr100` | 8.351e5 m/s | 3.656e5 (157.7 eV) | 0.438 |
| WarpX real mass | 1.949e5 m/s | 1.425e5 (440.2 eV) | 0.731 |

So a reduced-mass leg ablates **2.64× faster in m/s** than the real problem, while its
normalisation constant is **4.27×** larger. Divide a velocity by the wrong one and you
manufacture a 1.6× discrepancy out of nothing.

**Rule: normalise velocities by `C_S` at each leg's own MEASURED plume `T_e`, not by `C_S0` at
the shared 823 eV.** Doing that took the rarefaction coefficient from a 1.45× "disagreement"
to 1.002×.

### 7.3 The plume geometry, if the drift is wrong

`d_i0 ∝ µ^(1/2)`, so at µ = 0.0546 the whole plume is **4.29× more compact in microns** and
evolves **18.4× faster in seconds**. Both are absorbed exactly by plotting `ζ` and `τ_own`.
What is *not* absorbed is a velocity transferred in the wrong family (§6) — that puts the
corona on a different trajectory in `ζ` and shows up as a stretched `L_n`, an over-run front,
and in the worst case a density notch propagating out of the target.

### 7.4 Absorption — the one that genuinely breaks

The similarity transform is supposed to leave the inverse-bremsstrahlung optical depth
invariant:

```
tau_abs = int K dz ,   K ~ n^2 Z lnLambda T^(-3/2) ,   L ~ d_i0 ~ mu^(1/2)
```

`K ∝ T^(−3/2)` falls as `µ^(−1/2)` exactly as the path length grows as `µ^(1/2)`, so
`τ_abs ∝ µ⁰`. **That cancellation requires `T` to scale as `µ^(1/3)`.**

The handoff (§5) pins `T` in **raw eV**. So `K` does not move, `L` does, and

```
tau_abs  ~  mu^(1/2)          measured: mu^0.490, 4.6% scatter  -- 2% from the prediction
```

Measured `⟨f_abs⟩` across the sweep: **0.205 → 0.364 → 0.624 → 0.840**. At `m_p/m_e` = 100 the
leg absorbs roughly **4.3× less** than the real problem.

The reason the initial condition wins over the steady state is that these runs reach only
5.39 `τ_own` and never reach quasi-steady ablation, so absorption is a transient set by the
handoff temperature rather than by each leg's own equilibrium.

**This is the fork.** You may hand off the real state in raw eV — comparable to FLASH in eV,
absorption wrong by `µ^(1/2)` — or transfer everything in similarity units including
`T ∝ µ^(1/3)` — absorption preserved, raw-eV comparison meaningless. **Mixing them is what
produces the `µ^0.454`.** Note also that no post-hoc `f_abs^(2/3)` correction repairs it:
applied across the sweep it makes the scatter worse, not better.

### 7.5 Collisionality — irreducible

`λ_ei ∝ T²/(n lnΛ)` is **mass-independent**, while `L ∝ µ^(1/2)`. So

```
lambda_ei / L  ~  mu^(1/6)
```

At µ = 0.0546 the reduced plasma is **1.62× more collisional relative to its own scale** than
the real one. No handoff convention fixes this; only more ion mass does.

---

## 8. What the corrected comparison actually says

With the real-mass leg (`P4_lez_kin_mrreal_drift`, µ = 1, real electron, no transform):

| code | ion | plume `T_e` | `⟨f_abs⟩` |
|---|---|---|---|
| FLASH | real Al | 647.0 eV | 0.870 |
| PSC | real Al | 508.8 eV | 0.583 |
| **WarpX, real mass** | real Al | **440.2 eV** | **0.840** |

WarpX's absorbed fraction lands within 3.4 % of FLASH's, so that pair is very nearly a
matched-`f_abs` comparison needing no correction: **WarpX runs 0.69× FLASH's plume `T_e`**,
with the critical surface at 1.03× and the density scale length at 0.81×. That is the
project's cleanest cross-code number — real ion, real electron, matched absorption, no
normalisation anywhere.

PSC's 0.583 is not matched to either, so its 0.79× is not a like-for-like figure.

---

## 9. Checklist for a new leg

1. Rescale by all **three** families (§6), not two.
2. Verify `uza/C_S0` = 0.548, and `ζ_cr` and `L_n` against FLASH. Not the temperature.
3. Quote `T_e/T_ss(own µ)`, never raw eV.
4. Normalise velocities by `C_S` at the leg's **measured** `T_e`.
5. Quote `⟨f_abs⟩` beside every temperature, and say which convention (time-integrated, not
   the final instantaneous value the older tables use).
6. Expect `f_abs` to scale as `µ^(1/2)` on a raw-eV handoff — it is not a code difference.
7. Keep `n_cell` divisible by `blocking_factor` 8 and reset `max_grid_size` to match.
8. Check gates G1 and G2 are unchanged from `mr100`; if they moved, something in the electron
   sector was touched that should not have been.
