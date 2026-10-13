# P8_scan_dt2_laser_CH — P8 stabilizer scan

**Phase.** 8 (hybrid OMEGA 2019), stabilizer scan.
**Question.** Does dt 400 -> 200 fs (particle CFL at 3400 km/s 0.68 -> 0.34), steps doubled carry `P8_hyb_laser_CH_hv` past its abort (non-finite E at the plume/ambient interface)?
**Falsified by.** An abort before 4.5 ns.

## Geometry
As `P8_hyb_laser_CH_hv`.

## Result
**ABORTED** at step 949 (t = 0.19 ns; shared array 59728350), same non-finite E. The Holmström twin aborted at step 836 (0.33 ns). Movie: `media/P8/P8_scan_dt2_laser_CH_p8diag.mp4`.

## Retracted
Nothing yet.
