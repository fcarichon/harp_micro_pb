#!/bin/bash
#SBATCH --job-name=harp30b_full
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=64G
#SBATCH --gres=gpu:a100l:1
#SBATCH --partition=long
#SBATCH --array=0-59%2

# Submit from the isolated repository root. Slurm opens logs before this script
# starts, so first run: mkdir -p logs
# Use a new absolute batch directory, for example:
# sbatch experiments/run_qwen30b_full_matrix.sbatch /absolute/path/to/new-batch
# RUN_OUTPUT_DIR can instead be exported before submission.
# For a smoke test, override the array at submission with --array=0%1.

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?Submit this job from the isolated repository root}"
RUN_OUTPUT_DIR="${RUN_OUTPUT_DIR:-${1:-}}"
case "$RUN_OUTPUT_DIR" in
  /*) ;;
  *) echo "Supply an absolute RUN_OUTPUT_DIR or first positional argument." >&2; exit 2 ;;
esac
if [[ ! -f experiments/matrix_fullconfigs_qwen30b.json ]]; then
  echo "The submission directory does not contain the full Qwen matrix." >&2
  exit 2
fi

export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="${SCRATCH:?SCRATCH is required}/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1
mkdir -p "$HF_HOME"

echo "Host: $(hostname)"
echo "Array task: $SLURM_ARRAY_TASK_ID"
echo "Batch output: $RUN_OUTPUT_DIR"
nvidia-smi

srun uv run --frozen --no-sync python experiments/run_matrix_entry.py \
  --matrix experiments/matrix_fullconfigs_qwen30b.json \
  --index "$SLURM_ARRAY_TASK_ID" \
  --output-dir "$RUN_OUTPUT_DIR"
