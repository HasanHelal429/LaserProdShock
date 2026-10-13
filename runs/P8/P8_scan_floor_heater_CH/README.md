# P8_scan_floor_heater_CH — P8 stabilizer scan

**Phase.** 8 (hybrid OMEGA 2019), stabilizer scan.
**Question.** Does density floor 0.1 -> 1.0 n_amb (bounds B/n in the Hall term 10x tighter) carry `P8_hyb_heater_CH_hv` past its abort (non-finite E at the plume/ambient interface)?
**Falsified by.** An abort before 4.5 ns.

## Geometry
As `P8_hyb_heater_CH_hv`.

## Result
**ABORTED** at step 11080 (t = 4.43 ns; shared array 59728350), same non-finite E. The Holmström twin aborted at step 2785 (1.11 ns). Movie: `media/P8/P8_scan_floor_heater_CH_p8diag.mp4`.

## Retracted
Nothing yet.
