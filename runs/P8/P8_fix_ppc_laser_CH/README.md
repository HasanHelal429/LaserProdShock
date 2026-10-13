# P8_fix_ppc_laser_CH — P8 fix test for the empty-cell abort

**Phase.** 8 (hybrid OMEGA 2019), fix test.
**Question.** Does target ppc 200 -> 50000: one target macroparticle per cell = 1.8e24 m^-3 (2 n_amb) instead of 4.5e26 (500 n_amb) keep every cell populated, and so carry P8_hyb_laser_CH_hv past its abort and on to 4.5 ns? The user traced every P8 abort to a cell where both ion species run out of macroparticles.
**Falsified by.** An abort (non-finite E), or any cell with zero particles of every species before 4.5 ns.

## Geometry
As `P8_hyb_laser_CH_hv`.

## Result
Pending.

## Retracted
Nothing yet.
