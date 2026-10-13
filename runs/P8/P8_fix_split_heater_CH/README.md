# P8_fix_split_heater_CH — P8 fix test: split the heavy target macroparticles

**Phase.** 8 (hybrid OMEGA 2019), fix test.
**Question.** The user traced the aborts to the target population's weight (~1e5x an ambient macroparticle at ppc 200). Does density-triggered splitting of the target species (min_ppc 50, every 5 steps = 2 ps, offset 0.25), so plume macroparticles stay light as the plume thins carry P8_hyb_heater_CH_hv past its abort to 4.5 ns?
**Falsified by.** An abort (non-finite E) before 4.5 ns.

## Geometry
As `P8_hyb_heater_CH_hv`.

## Launch
`perlmutter/submit.sh p8split` (binary: warpx-cda particle-splitter build, which also carries the hybrid solver, the hybrid laser, the electron-fluid heater and Holmstrom).

## Result
**ABORTED** at step 4258 (t = 1.70 ns; debug array 59726909), same non-finite E. The unsplit Holmström twin aborted at step 2785. Splitting did run (heater: target macroparticles 15,600 → 61,087 at step 1900 → 331,896 at 3900; the unsplit twin stays at 15,600). Movie: `media/P8/P8_fix_split_heater_CH_p8diag.mp4`.

## Retracted
Nothing yet.
