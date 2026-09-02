#!/bin/bash
#SBATCH --job-name=harp8b_worker
#SBATCH --output=logs/%x-%j.out
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:l40s:1
#SBATCH --partition=long

set -euo pipefail

cd "$HOME/CODE/harp_micro_pb"
export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="$SCRATCH/huggingface"
mkdir -p "$HF_HOME" outputs logs

echo "Host: $(hostname)"
echo "Matrix indices: $INDEX_LIST"
echo "Matrix file: ${MATRIX_FILE:-experiments/matrix_qwen8b.json}"
nvidia-smi

IFS=':' read -r -a indices <<< "$INDEX_LIST"
for index in "${indices[@]}"; do
  echo "Starting matrix index: $index"
  srun uv run python experiments/run_matrix_entry.py \
    --matrix "${MATRIX_FILE:-experiments/matrix_qwen8b.json}" \
    --index "$index"
done
