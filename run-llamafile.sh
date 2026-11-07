#!/usr/bin/env bash
# Apex — profile-driven llamafile launcher.
# Reads runtime settings from config/navi.config.json (written by
# the install-time hardware profiler; editable / re-detectable in
# Settings) and execs navi.llamafile with those flags. No profile
# in the config -> the fluid floor: 4096 / 4 threads / batch 512.
set -euo pipefail
cd "$(dirname "$0")"
FLAGS="$(python3 - <<'PY' 2>/dev/null || echo "--ctx-size 4096 --threads 4 --batch-size 512"
import json
try:
    with open("config/navi.config.json") as f:
        cfg = json.load(f)
    rt = cfg.get("runtime") or {}
    hp = (cfg.get("hardware_profile") or {}).get("settings") or {}
    ctx = int(rt.get("ctx_size") or hp.get("ctxSize") or 4096)
    thr = int(rt.get("threads") or hp.get("threads") or 4)
    bat = int(rt.get("batch_size") or hp.get("batchSize") or 512)
    gpu = int(rt.get("gpu_layers") if rt.get("gpu_layers") is not None else (hp.get("gpuLayers") or 0))
    out = f"--ctx-size {ctx} --threads {thr} --batch-size {bat}"
    if gpu > 0:
        out += f" --n-gpu-layers {gpu}"
    print(out)
except Exception:
    print("--ctx-size 4096 --threads 4 --batch-size 512")
PY
)"
# shellcheck disable=SC2086
exec ./navi.llamafile --server --v2 $FLAGS
