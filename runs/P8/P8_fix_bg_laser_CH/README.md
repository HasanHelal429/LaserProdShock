# P8_fix_bg_laser_CH — P8 fix test for the empty-cell abort

**Phase.** 8 (hybrid OMEGA 2019), fix test.
**Question.** Does an IMMOBILE background ion population at 1% of n_amb everywhere (bg_ions_CH, do_not_push = 1, ppc 50) keep every cell populated, and so carry P8_hyb_laser_CH_hv past its abort and on to 4.5 ns? The user traced every P8 abort to a cell where both ion species run out of macroparticles.
**Falsified by.** An abort (non-finite E), or any cell with zero particles of every species before 4.5 ns.

## Geometry
As `P8_hyb_laser_CH_hv`.

## Result
**ABORTED** at step 572 (t = 0.23 ns; debug array 59726201), same non-finite E. The Holmström-only twin aborted at step 836. Movie: `media/P8/P8_fix_bg_laser_CH_p8diag.mp4`. Neither fix stops the blow-up; the user's next diagnosis is the target population's weighting (see `P8_fix_split_*`).

## Retracted
Nothing yet.
