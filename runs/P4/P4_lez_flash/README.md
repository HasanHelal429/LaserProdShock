# P4_lez_flash — FLASH leg of the Phase-4 cross-code benchmark

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** What does an independent radiation-hydrodynamics code say the answer is?
This is the reference the other two legs are judged against, not a result of ours.

**Status: deck written, NOT RUN. We have no FLASH build.** This directory is a handoff
package for a collaborator with FLASH 4.6.2.

Spec: `TEST_PLAN.md` §12. Decisions: `runs/P4/README.md` (D1, D8 are the ones that touch
this run). Reference: Lezhnin et al., *Phys. Plasmas* **32**, 022701 (2025), §II.A.

---

## What this run is

1D radiation-hydrodynamics of a long-pulse laser ablating solid aluminium — the reference
leg against which our two WarpX runs (`P4_lez_kin`, `P4_lez_hyb`) are judged. It is
deliberately the *published* configuration, so that agreement with it means something.

```
lambda0 = 1.064 um      I = 1e13 W/cm^2      pulse = 0.1 ns rise + 0.9 ns flat top
target  = solid Al, 2.7 g/cm^3, x in [0, 50] um, fully ionised Z = 13, T = 290 K
chamber = Al vapour, 1e-10 g/cm^3
domain  = 800 um, 8 blocks x 16 cells, AMR level 4
```

## Geometry

```
1D  |  propagation axis x  |  lengths in MICRONS (real masses -- no reduction here)

                                                              <== laser
      ##########....................................................
      ^         ^                                                  ^
      outflow   |                                               outflow
      x = 0     x = 50 um                                     x = 800 um

  #  solid Al target : 2.7 g/cm^3, fully ionised Z = 13, Te = Ti = 290 K
  .  chamber gas     : Al vapour at 1e-10 g/cm^3  (PIC has NONE -- see below)
  grid               : 8 blocks x 16 cells = 128 base cells, AMR lrefine_max = 4
                       -> 1024 effective cells, 0.78 um at the finest level
  duration           : 1.0 ns  (0.1 ns linear rise + 0.9 ns flat top)
```

Two differences from the WarpX legs are structural, not oversights:

- **The chamber gas exists here and does not exist in PIC.** FLASH needs a floor density to
  run; PIC cannot resolve 10⁻¹⁰ g/cm³ and the paper says so outright. This is one reason the
  acceptance criteria (§12.6) are confined to the ablated underdense plasma.
- **The target is *solid* — ~700 `n_cr` — where PIC caps it at 10 `n_cr`.** So inside the
  target the two codes are modelling different objects, deliberately. Nothing in this phase
  claims agreement there.

**This run is in real physical units.** The WarpX legs use a reduced mass ratio
(`m_p/m_e` = 100), which shrinks their lengths by `√(1836/100)` = 4.29 and their times by
1836/100 = 18.36. Their 1000 `d_e` box is 169.3 µm against this 800 µm, and their 54.66 ps
is this 1 ns. **Never overlay the codes on a µm or ps axis** — comparison is in normalised
units, each code with its own `d_i0` (`TEST_PLAN.md` §12.2).

Radiation transport **off** and ionisation **fixed at Z = 13** — the paper's own choice for
the PIC comparison, justified by its Fig. 1, which shows both make a negligible difference
to the profiles.

---

## Handoff note

### What we need back

Per dump time — **0.1, 0.2, 0.4, 0.6, 0.8, 1.0 ns** — 1D profiles of

```
x [cm or um]   nele [cm^-3]   tele [eV or K]   tion   velx   depo   dens
```

**The 0.1 ns dump is the important one beyond the comparison itself.** Under decision D1 it
is what our PIC runs may be initialised from — the paper does exactly this, because a cold
sharp solid edge makes the ray tracer reflect everything and nothing ablates. Please do not
drop it.

Format: plain text with a header row is ideal. Raw HDF5 plotfiles are fine too (`yt` reads
them), but then the column extraction is on us, and this repo has already been bitten once
by inferring column layout from column *count* (`tests/test_profile_columns.py` exists
because of it). A header row removes that whole failure mode.

Destination: see D8 in `runs/P4/README.md` — still open. Repo convention is that finished
diagnostics live under `/mnt/cellar/hhelal` with symlinks left at the original paths.

### Two runs, not one, if you can spare it (decision D1c)

| | Initial condition | Purpose |
|---|---|---|
| **1. cold-solid** | as `flash.par` ships — cold solid + FLASH's slow start | paper-faithful; also *validates* our analytic stand-in by comparison at 0.1 ns |
| **2. analytic-IC** | started from the same analytic rarefaction our WarpX runs use | the true apples-to-apples partner — removes "did they start from the same thing?" from the comparison entirely |

Run 1 alone is enough to proceed. Run 2 is what makes the three-way comparison airtight,
and in 1D it costs minutes.

### Things in `flash.par` that need your eyes

Every physical number is from the paper and we are confident in it. The FLASH **keywords**
are written from FLASH4 conventions and have never been through a build. Marked `# CHECK`
in the file:

1. **`sim_teleTarg = 290.0`** — we assume kelvin, not eV.
2. **`ms_targZMin = 13.0`** — intent is to *pin* ionisation at 13 so it matches the PIC
   legs. If that is not the right way to disable dynamic ionisation in your tree, please
   substitute the correct mechanism; the physics requirement is `Z` = 13, fixed.
3. **`eos_targTableFile = "al-imx-003.cn4"`** — the IONMIX Al table name in FLASH 4.6.2.
4. **`ed_gridType_1 = "regular1D"`** and the 1D laser package generally. FLASH's
   `EnergyDeposition` unit is mainly exercised in 2D/3D; the paper used 1D, so it works,
   but the exact keyword may differ.
5. **Beam power vs intensity.** `ed_power_1_* = 1.0e20` erg/s is `I` = 10¹³ W/cm² times a
   **unit** (1 cm²) cross-section, set by `ed_lensSemiAxisMajor_1 = 1.0`. If your setup
   defines the cross-section differently, keep `power/area` = 1.0e20 erg/s/cm² and change
   whichever of the two is convenient.

A suggested setup line, also unverified:

```
./setup LaserSlab -auto -1d +hdf5typeio species=cham,targ +mtmmmt +laser +uhd3t \
        -nxb=16 -objdir=lezhnin1d ed_maxPulseSections=4 ed_maxBeams=1
```

### What we are checking against you

Our acceptance table (`TEST_PLAN.md` §12.6) uses **the paper's own tolerances**, so our
agreement is directly comparable to theirs: `n_e`, `T_e`, `T_i` to 20 %, `V_z` to 10 %,
over the **underdense** region only.

The overdense interior is deliberately excluded. PIC caps the target at 10 `n_cr` against a
true ~700 `n_cr`, so inside the solid the two codes are modelling different objects — the
paper says as much, and no claim in this phase depends on that region.

One analytic anchor all three legs must hit, from Manheimer's steady-state ablation model
(the paper's Eq. 15, **with `Z^(−1/3)`**):

```
T_e,SS = 823 eV
```

which is the plateau in the paper's Fig. 3(b). If FLASH does not land near it, something is
wrong with the deck rather than with the physics.

## Result

**Not run by us — we have no FLASH build.** This directory is a handoff package. Results
arrive from the collaborator; see D8 for where they land.

## Retracted

Nothing yet. Note that `flash.par` has never been through a FLASH build: the physical values
are from the paper and are believed right, but the keywords are unverified and the `# CHECK`
items in the file are exactly where we expect to be wrong.
