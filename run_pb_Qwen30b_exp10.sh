#!/bin/bash
#SBATCH --job-name=harp_pb_Qwen30b_exp10
#SBATCH --output=logs/%x-%j.out
#SBATCH --time=10:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-gpu=64G
#SBATCH --gres=gpu:rtx8000:2
#SBATCH --partition=long


module load cuda/12.2

export HF_HOME=/home/mila/f/florian.carichon/scratch/huggingface

cd /home/mila/f/florian.carichon/harp_micro_pb

uv run python src/run_pilot.py \
    --profiles eco-growth family egalitarian \
    --project_ids P14 P17 P18 \
    --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
    --output "exp10_c_runCompetition.json"