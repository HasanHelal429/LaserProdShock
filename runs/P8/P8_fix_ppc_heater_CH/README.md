# P8_fix_ppc_heater_CH — P8 fix test for the empty-cell abort

**Phase.** 8 (hybrid OMEGA 2019), fix test.
**Question.** Does target ppc 200 -> 50000: one target macroparticle per cell = 1.8e24 m^-3 (2 n_amb) instead of 4.5e26 (500 n_amb) keep every cell populated, and so carry P8_hyb_heater_CH_hv past its abort and on to 4.5 ns? The user traced every P8 abort to a cell where both ion species run out of macroparticles.
**Falsified by.** An abort (non-finite E), or any cell with zero particles of every species before 4.5 ns.

## Geometry
As `P8_hyb_heater_CH_hv`.

## Result
**ABORTED** at step 4598 (t = 1.84 ns; debug array 59726201), same non-finite E. The Holmström-only twin aborted at step 2785. Movie: `media/P8/P8_fix_ppc_heater_CH_p8diag.mp4`. Neither fix stops the blow-up; the user's next diagnosis is the target population's weighting (see `P8_fix_split_*`).

## Retracted
Nothing yet.
