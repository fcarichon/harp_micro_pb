#!/bin/bash
#SBATCH --job-name=harp30b_v2
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=64G
#SBATCH --gres=gpu:a100l:1
#SBATCH --partition=long
#SBATCH --array=0-3%1

set -euo pipefail

cd "$HOME/CODE/harp_micro_pb"
export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="$SCRATCH/huggingface"
mkdir -p "$HF_HOME" outputs logs

echo "Host: $(hostname)"
echo "Array task: $SLURM_ARRAY_TASK_ID"
nvidia-smi

srun uv run python experiments/run_matrix_entry.py \
  --matrix experiments/matrix_qwen30b.json \
  --index "$SLURM_ARRAY_TASK_ID"
