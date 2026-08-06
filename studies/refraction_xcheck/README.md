# `studies/refraction_xcheck` — a free `refraction = 1` reference for the `P1_vac_2d_spot_abl` geometry

## Where this came from (it was an accident, and it is worth keeping)

`P1_vac_2d_spot_abl` was launched 2026-08-05 20:26 and killed 7 minutes later at step ~2000
of 216 000, because `make_inputs.py --verify` reported

    laser_deposition.refraction: missing from warpx_used_inputs

The deck sets `refraction = 0`, but `build_cuda_omp/bin/warpx.2d` was built **2026-07-31
14:37** and `refraction` was added to the operator **2026-08-04 13:58** — four days later.
`strings` on that binary finds no `refraction` at all. WarpX does not abort on unused inputs
(`amrex.abort_on_unused_inputs` defaults to 0), so the flag was **silently ignored** and the
run was marching with **full refraction**.

That is a provenance failure, not a physics result, so the run was stopped and the tree
rebuilt. But the seven minutes it did run produced something the campaign wants anyway: the
step-0 deposition of the **refracting** march on exactly the geometry the straight-ray run
uses. `P1_vac_2d_spot_abl`'s config says a refracting companion "is the clean way to bound
this" — this is a third of that companion, for free.

**The 167 MB profile dump was NOT kept.** It was reduced to the three files below and then
deleted, along with 2.4 GB of plotfiles from the same invalid binary.

## Files

| file | what |
|---|---|
| `rays_refr1_step0.txt` | the operator's own dumped ray paths, 40 rays (`ray_stride` 16, `ray_step_stride` 40). Read with `scripts/plot_rays.py --dump`. **2 turn rows** — the near-critical specular branch fired twice. |
| `pabs_refr1_step0_transverse.txt` | column-integrated `P_abs` [W/m] vs `x/d_e` — the transverse deposition profile |
| `pabs_refr1_step0_axial.txt` | on-axis (`abs(x) < 5 d_e`) `P_abs` [W/m^3] and `n_e/n_cr` vs `z/d_e` |
| `scalars_refr1_step0.txt` | the three numbers below |
| `zcrit_profile_spot_abl.txt` | **the crater.** `z_crit(x)` at `t` = 0 and at 13.45 ps for the completed `refraction = 0` run — the critical surface goes from a flat 37.7 d_e to 4.2 d_e on axis against 50.3 d_e at \|x\| ~ 90, i.e. 46.1 d_e = 2.30 `w0` deep. Kept here rather than under the run because its natural companion is the refracting reference above. |

## The numbers

    total P_abs = 5.940809e+13 W/m
    incident    = 5.9410e+13 W/m          (I0 w0 sqrt(pi) at I0 = 1e19)
    f_abs(0)    = 0.999968
    peak on-axis n_e = 1.5004 n_cr

`f_abs(0) = 0.99997` is the expected answer, not a surprise: at `L_n` = 60 d_e the single-pass
`tau` through the flat top is 706, the target is optically thick long before the critical
surface, and `run_checks` predicts `f_abs ~ 1.000`. It is still worth having as a *measured*
number on this deck.

**Caveat on `w_eff`.** The transverse file's plain second moment gives `w_eff/w0 = 0.7071`,
which is `1/sqrt(2)` — i.e. exactly what an *unbroadened* Gaussian intensity profile
`exp(-(x/w0)^2)` must give, since `<x^2> = w0^2/2`. It is **not** a narrow beam. The
`w_eff/w0 = 1.000` convention quoted elsewhere in this project (RESULTS 2026-07-29,
`spot_report.py`) carries the `sqrt(2)`, so multiply by 1.4142 to compare. Stated because
comparing the two conventions without noticing would look like a 41 % discrepancy.

## What to do with it

When `P1_vac_2d_spot_abl` finishes on the rebuilt binary, compare its **step-0** dumps
against these. At `t` = 0 the target is plane-stratified, and a straight march carrying the
Snell invariant is *exact* there — so the two modes should agree to the print precision, and
any disagreement at step 0 is a bug rather than a modelling difference. That makes this the
cheapest possible acceptance test of `refraction = 0` on a production geometry.

It says nothing about later times. The whole reason the straight-ray mode is approximate here
is the crater, which does not exist at step 0.

## The lesson, which is not about refraction

**A silently ignored ParmParse key is indistinguishable from a working one, unless something
checks.** `--verify` is that something, and it is the only reason this was caught before 4.6 h
of GPU time went into a run whose README claimed a mode it was not using. Two habits follow:

1. **Run `--verify` right after the run starts**, not only at the end. It needs
   `warpx_used_inputs`, which WarpX writes at initialization, so it is answerable within
   seconds of launch — and that is when the answer is cheap to act on.
2. **A binary's date is part of a run's provenance.** Check the build against the commit that
   introduced whatever the deck newly relies on; `strings <binary> | grep -x <key>` settles it
   in one line.
