# P5_ckpt — checkpoint/restart acceptance test

**Phase.** 5, `TEST_PLAN.md` §13.
**Question.** Does a chained submission actually resume — right checkpoint, continued step
counter, `run.log` appended rather than truncated?
**Expected.** Segment 2 restarts from `diags/chk002000` and runs on to the raised
`max_step`, with the first segment's `LASERDEP` history still present in `run.log`.
**Falsified by.** A restart from step 0, a truncated `run.log`, or `run_warpx` refusing
because it saw an existing `diags/`.

---

## Why this exists

A G8-passing spine costs ~145 h against a 48 h queue limit, so the phase's headline result
depends on chaining. `P5_flashic_off` already lost 65 % of a 24 h run to the wall with
nothing to resume from. A machinery bug found here costs two minutes; found on the spine it
costs two days.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 2000 steps = 0.1977 ps
```

## Result

**PASSED, 2026-09-02.** Segment 1 (job 57869919 → 57871106) ran 2000 steps and wrote
`chk000000/001000/002000`. `max_step` was then raised to 4000 and the leg resubmitted
(57871958). Segment 2:

| check | result |
|---|---|
| found and used the checkpoint | `run_warpx: RESTARTING from chk002000` |
| `run.log` appended, not truncated | 402 `LASERDEP` lines = 201 + 201 |
| continued, not restarted | steps 1–4000, **4000 distinct**, no duplicates |
| new checkpoints written | `chk003000`, `chk004000` |
| exit | 0 |

**It failed on the first attempt, which is why it exists.** The renderer emitted
`chk.diag_type = checkpoint`, but `checkpoint` is a **format**: WarpX aborted at
initialisation with *"diag_type must be Full, TimeAveraged, BackTransformed or
BoundaryScraping"*. The correct form is `chk.diag_type = Full` + `chk.format = checkpoint`
(see `Examples/Tests/pml/inputs_base_2d`). Two minutes to find here; it would have been two
days on the spine.

## Retracted

Nothing.
