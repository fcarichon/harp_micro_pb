#!/bin/bash

#SBATCH --job-name=pb
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00

#SBATCH --output=logs/%x-%j.out

module load cuda/12.2

export HF_HOME=/home/mila/f/florian.carichon/scratch/huggingface

cd /home/mila/f/florian.carichon/harp_micro_pb

uv run python src/run_pilot.py