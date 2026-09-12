Two stacked fixes to the `LaserDeposition` ray-tracing operator, plus the instrumentation that found them.

### Commits
- `2a4d36b0b` — expose `laser_deposition.n_floor` as an input, and report near-critical behaviour per application (`rmax`, `overfrac`, `layerfrac` on the LASERDEP line). Accumulators are passed as per-bucket reference params so the OpenMP reduction stays race-free.
- `9d07924ba` — **stop depositing the near-critical layer into evanescent cells.** Deposit at `c_old` rather than `c`, and measure `drds` over at least one cell.
- `cbec4a78d` — **do the physics with the species electron mass, not `PhysConst::m_e`.** `n_cr` is linear in electron mass, so a raised-mass electron species silently got the wrong critical density, the wrong absorption coefficient and the wrong energy budget.

### Why
A `ray_cfl` convergence study diverged by +18.3 %. A dedicated `n_floor` role-attribution sweep (4 decades, both march modes) showed the sensitivity is **95 % the refracting RK4 trajectory**, not the analytic layer width — which refuted the fix originally proposed for it. Straight-ray mode converges (+0.02 % on the last increment, against a measured 1σ of 1.32 % from GPU run-to-run scatter alone). The refracting march breaks below `n_floor` 1e-3, where `rmax` reaches ~10 and rays penetrate the 10 n_cr solid.

### Scope and deliberate non-changes
- θ remains referenced to the real `PhysConst::m_e`. It is a temperature unit there, not a dynamical mass, and rescaling it would change the meaning of every existing deck.
- The `refraction` default is unchanged. Straight rays are the right default for plane-stratified studies, but that is a deck-level choice, not an operator default to flip under other users.

### Verification so far
- Builds clean on Perlmutter (CUDA, 1D+2D, 0 errors).
- Binary key check passes: `n_floor`, `near_critical_fix`, `refraction`, `electron_mass` all present as contiguous literals.
- Physics validation is queued (`lp5_physval`): closed-form coefficient audit, Beer–Lambert residual, energy closure, near-critical overfrac, and a decisive species-mass test — particle KE gain ÷ tracer `E_abs` should be **1.0 with the fix** and **4.0 with `electron_mass` forced to the real value** at a 4× electron.

**Not yet merged pending that validation.**

🤖 Generated with [Claude Code](https://claude.com/claude-code)
