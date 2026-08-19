# P4_lez_kin_thick — a target thick enough to reach quasi-steady ablation

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** Does the kinetic leg reach a *measurable plateau* in `T_e`, and does that
plateau sit at the value `P4_lez_kin_ic6_long` extrapolated — **381.5 ± 21.5 eV** at the
critical surface, **1.22 ×** its own reduced-mass `T_e,SS` of 312 eV?

**Why the parent could not answer it.** `ic6_long` (2026-08-19) ran 4× longer and still found
`T_e` rising at 4.0 σ. It was converging — an exponential fit gave `τ_relax` = 44.3 — but it
could never arrive, because **the target ran out first**. The measured facts:

- the above-critical areal density is ablated at **3.0–3.25 `n_cr·d_e` per τ** (linear fit
  over τ 0–108), exhausting the 450 `n_cr·d_e` reservoir at **τ ≈ 130–153**;
- `n_peak` = 18.66 exp(−τ/38.7) crosses **1 `n_cr` at τ ≈ 113**, after which there is no
  critical surface and `Te_at_cr` stops existing as a diagnostic;
- **no mass is lost** — total areal density is conserved to 0.9 % (= the boundary weight
  loss). The slab **decompresses**; it is not consumed. So the fix is a bigger mass
  reservoir, not a longer run.

**The fix, sized from those numbers.** 200 `d_e` at 10 `n_cr` = **2000 `n_cr·d_e`**. At a
budgeted 4.0 per τ (the 3.25 late rate, raised ~25 % for the hotter asymptotic state),
τ 180 consumes ~720 and leaves **~1300 unconsumed** — the reservoir is still deep when the
measurement is made, which is what "quasi-steady" requires.

**Thicker, not denser.** Density is the other lever on areal mass and it is blocked by G1:
`ω_pe dt` ∝ √n, and 10 `n_cr` already sits at 0.783 at 2× compression against a limit of 2.
50 `n_cr` would read 1.75 at 2× compression. Thickness costs particles; density costs
stability.

**The slab grows BACKWARDS.** `center_de` −22.5 → −100 keeps the solid–vacuum interface at
z = 0, so the corona, the critical surface and the drive are bit-for-bit the parent's. The
only thing that changes is how much cold mass sits behind them.

**Expected.**
1. `T_e` at the critical surface **plateaus**, with a fitted slope consistent with zero.
2. **`τ_relax` FALLS, from 44.3 toward ~17.** This is the sharp prediction. FLASH's own
   approach was fitted (2026-08-19) at **`τ_relax` = 3.99** (`Te_at_cr`) — it is 99.9 %
   converged by τ 27, where `ic6_long` was only 46 % converged. The reduced mass ratio
   accounts for a factor **4.285** = √(49542/2698) = the ratio of `v_th,e`/`C_S`, i.e. how
   much slower electron transport is on the ion clock. That predicts FLASH ≈ 44.3/4.285 =
   10.3, but FLASH measures 3.99 — so mass ratio explains only 4.285 of the observed 11.1×,
   and the **residual 2.6× is the missing mass reservoir**: FLASH ablates a thin front off a
   deep solid (`n_peak` 795 → 4141 `n_cr`) while `ic6_long` decompressed its whole slab.
   Restoring the reservoir should recover that 2.6×, giving `τ_relax` ≈ 3.99 × 4.285 ≈ **17**.
3. **The converged `T_e` comes DOWN, toward 1.0 × its own `T_e,SS`.** `ic6_long` extrapolates
   to **1.22 ×** (`Te_at_cr`) and **1.99 ×** (band mean) where FLASH converges to **0.77 ×**
   and **0.99 ×** of its own. If that overshoot is an artifact of decompressing a
   reservoir-less slab, a real reservoir removes it.
4. `n_peak` stays **above 1 `n_cr` throughout** (predicted ≳ 6 `n_cr` at τ 180).

**Falsified by — and this is the whole point.** If `T_e` still converges to ~2 × its own
`T_e,SS` **with a deep reservoir intact and `τ_relax` reduced**, then the WarpX↔FLASH
disagreement is **real physics, not target design**, and the prime suspect becomes collisions
under a reduced mass ratio (`controls.collision_gate`). That is a far more valuable outcome
than a confirmation, and it is the reason this run is worth 2.5 h.

**Why the τ = 27 agreement must not be quoted as validation.** In each code's own similarity
units the two agree at τ 27 to **12–14 %** (`WarpX/FLASH` = 0.875 on `Te_at_cr`, 0.858 on the
band mean) — inside the paper's 20 % tolerance. But FLASH is **99.9 %** converged there and
WarpX only **36–46 %**. The agreement is WarpX crossing FLASH's converged value *on the way
up*; it is a coincidence of timing, not a validation. Extrapolated to convergence the same
comparison reads **1.59×** and **2.00×**. See RESULTS.md 2026-08-19 (convergence).

**Not a FLASH benchmark.** FLASH ends at τ 27 and there is no data beyond it. This measures
the WarpX leg's own converged state, which is the thing that can then be compared with
FLASH's own converged state — see RESULTS.md 2026-08-19 (extended) on why the τ = 27
comparison was reading a WarpX transient against a FLASH steady state.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -208                                                  z = +4000

  #  target flat top : 10 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 8416 cells, dz = 0.5 d_e, dt = 0.09885 fs, 3686400 steps = 364.4 ps
```

## Why the domain is 4208 `d_e` and not 2500

**Not** to contain the plume — it cannot be contained, and it does not need to be. Two
measurements from the parent decide this:

- **The far plume absorbs nothing.** 0.0 % of `P_abs` lands beyond 1500 `d_e` at every
  profile dump (2.7e-4 at τ 81, and 5.9e-5 beyond 2000 `d_e`); 84.8 % is still inside
  500 `d_e` at τ 81. Box size does **not** set `f_abs`.
- **The outflow at the wall is supersonic — Mach 2.3 to 4.8, always.** The open boundary is
  causally disconnected from the ablation region, so letting the far plume go costs nothing
  upstream.

What *does* set the domain is keeping the **injection face out of the absorbing corona**.
Rays launch exactly on that face (`CLAUDE.md`), so once plume reaches it the drive becomes a
boundary quantity. `L_n` grows ~5.3 `d_e`/τ (205 at τ 54 → 491 at τ 108), so holding
n(face) ≲ 1e-2 `n_cr` at τ 180 needs hi ≈ 4.6 `L_n` ≈ **4000 `d_e`**. The parent's face had
already reached 3.2e-2 `n_cr` by τ 108, which is the one respect in which its late data are
compromised.

## Cost — **measured, ~2.0–2.8 h** (best estimate 2.5 h) on one RTX 4070

Benchmarked before launch, not scaled — `CLAUDE.md` records a particle×step estimate that was
wrong by 4× because cell count dominates. Two slices of this exact deck on GPU 0:

| steps | wall |
|---|---|
| 2 000 | 5.145 s |
| 8 000 | 21.760 s |

Marginal rate **2.769 ms/step**. At 3 686 400 steps that is **2.84 h** flat out; the parent
sped up 2.4 → 1.2 ms/step as 53 % of its macroparticles left the domain, and applying the
same 0.71 factor gives **2.01 h**. This target keeps its reservoir, so it will shed a smaller
fraction and land nearer the top of that range.

**The benchmark also confirms the cost model.** The marginal rate is **1.67 ×** the parent's
1.66 ms/step, against a cell ratio of **1.68 ×** and a particle ratio of 2.2 × (254 800 →
564 774 macroparticles). Cost tracks **cells**, not particles — exactly the trap `CLAUDE.md`
warns about, now measured on this deck.

`P4_lez_kin_thick_off` has no ray march; `ic6_off` ran at 0.81 × its driven twin, so ~**2 h**.
Both GPUs are free, so the pair can run concurrently in ~2.8 h wall rather than ~5 h serial.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` | 0.783 at 2× compression | PASS |
| G2 `dz/lambda_D` solid | 58 | INFO (G3 makes it meaningful) |
| G3 laser-off control | `P4_lez_kin_thick_off` — **its own**, per `runs/README.md` | declared |
| G4 `ray_cfl` | 0.25 | PASS |
| G5 ppc | 500 | PASS |
| G6 energy closure | — | post-run |
| G7 `dz` | 0.5 `d_e`, unchanged from the parent | INFO |

## Result
_Pending._

## Retracted
Nothing yet.
