#!/bin/bash
#SBATCH --job-name=harp_model_cache
#SBATCH --output=logs/%x-%j.out
#SBATCH --partition=long-cpu
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00

# Download weights on a CPU node; no GPU is reserved during transfer.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the isolated experiment checkout}"
MODEL_ID="${1:?Supply an official model ID}"
MODEL_REVISION="${2:?Supply the exact model commit}"
case "$MODEL_ID" in
  google/gemma-4-31B-it|meta-llama/Llama-3.1-8B-Instruct) ;;
  *) echo "Unsupported model ID" >&2; exit 2 ;;
esac
if [[ ! "$MODEL_REVISION" =~ ^[0-9a-f]{40}$ ]]; then
  echo "An exact 40-character revision is required" >&2
  exit 2
fi
export HF_HOME="${SCRATCH:?SCRATCH is required}/huggingface"
export PYTHONUNBUFFERED=1
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
HARP_HF_CLI="${UV_PROJECT_ENVIRONMENT:?Specify the existing Python environment}/bin/hf"
test -x "$HARP_HF_CLI"
"$HARP_HF_CLI" download "$MODEL_ID" --revision "$MODEL_REVISION" --cache-dir "$HF_HOME"
