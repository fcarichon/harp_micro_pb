#!/bin/bash
#SBATCH --job-name=harp_crossmodel
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:a100l:1
#SBATCH --partition=long
#SBATCH --array=0-59%1

# Submit from this checkout's root and create logs BEFORE sbatch starts.
# Usage: sbatch [Slurm overrides] experiments/run_crossmodel_matrix.sbatch MATRIX OUTPUT_DIR
# Use a fresh absolute output directory per model and export HARP_MODEL_REVISION
# as the complete checkpoint commit SHA. Llama may use sbatch --mem=32G.
# One array per model with %1 gives at most one active GPU per model.
# For a local read-only preflight, set SLURM_SUBMIT_DIR/SLURM_ARRAY_TASK_ID and
# run: bash experiments/run_crossmodel_matrix.sbatch MATRIX OUTPUT_DIR --dry-run

set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 || ( $# -eq 3 && "$3" != "--dry-run" ) ]]; then
  echo "Usage: $0 MATRIX_PATH ABSOLUTE_OUTPUT_DIR [--dry-run]" >&2
  exit 2
fi
: "${HARP_MODEL_REVISION:?Export the complete cached checkpoint commit SHA}"
if [[ ! "$HARP_MODEL_REVISION" =~ ^[0-9a-f]{40}$ ]]; then
  echo "HARP_MODEL_REVISION must be a full 40-character lowercase commit SHA." >&2
  exit 2
fi
cd "${SLURM_SUBMIT_DIR:?Submit from the isolated repository root}"
MATRIX_PATH="$1"
RUN_OUTPUT_DIR="$2"
case "$RUN_OUTPUT_DIR" in
  /*) ;;
  *) echo "OUTPUT_DIR must be an absolute path to a new batch directory." >&2; exit 2 ;;
esac
HARP_LAUNCH_DRY_RUN=0
if [[ "${3:-}" == "--dry-run" ]]; then HARP_LAUNCH_DRY_RUN=1; fi

export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-${SCRATCH:?SCRATCH or HF_HOME is required}/huggingface}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export UV_OFFLINE=1

python3 - "$MATRIX_PATH" "$RUN_OUTPUT_DIR" "$HARP_MODEL_REVISION" \
  "${SLURM_ARRAY_TASK_ID:?An array index is required}" "$HARP_LAUNCH_DRY_RUN" <<'PY'
import fcntl
import hashlib
import json
import os
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "experiments"))
from run_matrix_entry import build_command, load_entry, main as preview_entry

matrix_path = Path(sys.argv[1]).resolve()
output_dir = Path(sys.argv[2]).resolve()
revision = sys.argv[3]
dry_run = sys.argv[5] == "1"

def fail(message):
    raise SystemExit(message)

try:
    index = int(sys.argv[4])
    matrix = json.loads(matrix_path.read_text())
    baseline = json.loads((root / "experiments/matrix_fullconfigs_qwen30b.json").read_text())
    if not isinstance(matrix, list) or len(matrix) != 60 or len(baseline) != 60:
        fail("Expected the complete 60-entry matrix.")
    model_ids = {entry.get("model") for entry in matrix if isinstance(entry, dict)}
    allowed = {"google/gemma-4-31B-it", "meta-llama/Llama-3.1-8B-Instruct"}
    if len(model_ids) != 1 or not model_ids <= allowed:
        fail("The matrix must specify one supported Gemma or Llama model consistently.")
    model = next(iter(model_ids))
    for position, (entry, reference) in enumerate(zip(matrix, baseline)):
        if (not isinstance(entry, dict)
                or {key: value for key, value in entry.items() if key != "model"}
                != {key: value for key, value in reference.items() if key != "model"}):
            fail(f"Matrix entry {position} differs from the Qwen baseline beyond model.")
    selected = load_entry(matrix_path, index)
    _, destination = build_command(selected, output_dir)
    if destination.exists() or destination.is_symlink():
        fail(f"Refusing to overwrite existing output: {destination}")

    cache = Path(os.environ["HF_HOME"]) / ("models--" + model.replace("/", "--"))
    snapshot = cache / "snapshots" / revision
    if not snapshot.is_dir():
        fail(f"Pinned model snapshot is not cached: {snapshot}")
    weight_index = snapshot / "model.safetensors.index.json"
    if not weight_index.is_file():
        fail(f"Cached checkpoint has no safetensors index: {weight_index}")
    weight_map = json.loads(weight_index.read_text()).get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        fail("The cached checkpoint has an empty or invalid weight map.")
    files = set(weight_map.values()) | {"config.json", "tokenizer_config.json", "generation_config.json"}
    if model == "google/gemma-4-31B-it":
        files.update({"processor_config.json", "chat_template.jinja"})
    missing = sorted(name for name in files if not (snapshot / name).is_file()
                     or (snapshot / name).stat().st_size == 0)
    if not any((snapshot / name).is_file() and (snapshot / name).stat().st_size
               for name in ("tokenizer.json", "tokenizer.model")):
        missing.append("tokenizer.json or tokenizer.model")
    if missing:
        fail(f"Incomplete cached checkpoint for {model}: {missing}")

    identity = {
        "model": model,
        "model_revision": revision,
        "matrix_sha256": hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        "matrix_entries": 60,
    }
    identity_path = output_dir / "batch_identity.json"

    def validate_batch():
        if identity_path.exists():
            if json.loads(identity_path.read_text()) != identity:
                fail(f"Output directory belongs to a different model, revision, or matrix: {output_dir}")
            return True
        if output_dir.exists():
            unexpected = {path.name for path in output_dir.iterdir()} - {".batch.lock", "run_manifest.json"}
            if unexpected:
                fail(f"Choose a fresh output directory; untracked files already exist: {sorted(unexpected)}")
            manifest_path = output_dir / "run_manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text())
                if (manifest.get("model") != model
                        or manifest.get("cached_model_revision") != revision):
                    fail("Existing run_manifest.json does not match the selected model/revision.")
        return False

    validate_batch()
    print(f"Model: {model}\nPinned revision: {revision}\nCache: {snapshot}", flush=True)
    preview_entry(["--matrix", str(matrix_path), "--index", str(index),
                   "--output-dir", str(output_dir), "--dry-run"])
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / ".batch.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not validate_batch():
                with identity_path.open("x") as handle:
                    json.dump(identity, handle, indent=2)
                    handle.write("\n")
except (OSError, ValueError, TypeError, KeyError) as exc:
    fail(f"Cross-model preflight failed: {exc}")
PY

if [[ "$HARP_LAUNCH_DRY_RUN" == "1" ]]; then exit 0; fi
echo "Host: $(hostname)"
echo "Array task: $SLURM_ARRAY_TASK_ID"
nvidia-smi
srun uv run --frozen --no-sync python experiments/run_matrix_entry.py \
  --matrix "$MATRIX_PATH" \
  --index "$SLURM_ARRAY_TASK_ID" \
  --output-dir "$RUN_OUTPUT_DIR"
