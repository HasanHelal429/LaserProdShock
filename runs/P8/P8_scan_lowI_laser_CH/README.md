# P8_scan_lowI_laser_CH — P8 stabilizer scan

**Phase.** 8 (hybrid OMEGA 2019), stabilizer scan.
**Question.** Does laser intensity 5e13 -> 1e13 W/cm^2 (does the failure track the laser's ambient heating?) carry `P8_hyb_laser_CH_hv` past its abort (non-finite E at the plume/ambient interface)?
**Falsified by.** An abort before 4.5 ns.

## Geometry
As `P8_hyb_laser_CH_hv`.

## Result
**ABORTED** at step 727 (t = 0.29 ns; shared array 59728350), same non-finite E. The Holmström twin aborted at step 836 (0.33 ns). Movie: `media/P8/P8_scan_lowI_laser_CH_p8diag.mp4`.

## Retracted
Nothing yet.
