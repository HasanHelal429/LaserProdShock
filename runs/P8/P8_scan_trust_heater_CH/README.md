# P8_scan_trust_heater_CH — P8 stabilizer scan

**Phase.** 8 (hybrid OMEGA 2019), stabilizer scan.
**Question.** Does n_trust = n_amb: below the ambient density the electron velocity derived from the noisy current is not trusted (fork's bounded alternative to the T_e advection abort) carry `P8_hyb_heater_CH_hv` past its abort (non-finite E at the plume/ambient interface)?
**Falsified by.** An abort before 4.5 ns.

## Geometry
As `P8_hyb_heater_CH_hv`.

## Result
**ABORTED** at step 2633 (t = 1.05 ns; shared array 59728350), same non-finite E. The Holmström twin aborted at step 2785 (1.11 ns). Movie: `media/P8/P8_scan_trust_heater_CH_p8diag.mp4`.

## Retracted
Nothing yet.
