#!/bin/bash
# Measure the PIC noise floor on f_abs(0) by re-running one config at several RNG seeds.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
SEEDS=("${@:-}"); [[ -z "${SEEDS[0]:-}" ]] && SEEDS=(1 2 3 4 5 6)
for s in "${SEEDS[@]}"; do
  name="seed_${s}"; d="$HERE/scratch/$name"; mkdir -p "$d"
  python - "$HERE" "$d" "$s" "$name" <<'PY'
import sys, yaml
here,d,s,name = sys.argv[1:5]
cfg = yaml.safe_load(open(f"{here}/config.base.yaml"))
cfg["meta"]["run_id"]=name; cfg["meta"]["deck"]=f"inputs_{name}"
cfg["numerics"]["random_seed"]=int(s)
yaml.safe_dump(cfg, open(f"{d}/config.yaml","w"), sort_keys=False)
open(f"{d}/README.md","w").write(f"""# {name} — f_abs(0) noise-floor variant, random_seed = {s}

**Phase.** 0
**Question.** How much does f_abs(0) move between statistically identical runs?
**Expected.** A spread set by per-cell density noise at the critical surface.
**Falsified by.** Zero spread (then f_abs(0) is deterministic and small differences
between geometries are meaningful).

## Geometry
See `studies/fabs_noise/config.base.yaml`; identical to `runs/P0_bc_open_B` except
`max_step = 2` and the seed.

## Result
See `studies/fabs_noise/analyze.py`.

## Retracted
Nothing.
""")
PY
  python "$ROOT/scripts/make_inputs.py" "$d" -q >/dev/null
  echo "=== $name"; "$ROOT/scripts/launch.sh" -j 2 "$d" >/dev/null 2>&1 || echo "FAILED $name"
done
echo "seed ladder complete"
