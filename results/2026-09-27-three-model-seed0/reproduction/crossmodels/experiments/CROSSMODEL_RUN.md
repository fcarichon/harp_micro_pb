# Gemma and Llama full configuration runs

Run the same 60 configurations as the completed Qwen sweep on
`google/gemma-4-31B-it` and `meta-llama/Llama-3.1-8B-Instruct`.
The Llama matrix is copied from `matrix_fullconfigs_qwen30b.json` with only the
model ID changed. The existing Gemma matrix has the same scenario, profile,
project-order, and seed entries. The launcher checks this equivalence before
starting each run.

## Fixed experiment protocol

- Florian's corrected projects and 60 scenarios from upstream `46c57cf`.
- Three agents; original profile order and candidate-project order.
- Initial votes, the three pairwise discussions, then final votes and the
  existing deterministic aggregation rule.
- Existing prompt files, including `discussion_v3.txt`.
- Seed `0`, sampling temperature `0.7`, top-p `0.9`, and at most `512` new tokens.
- Thinking disabled; no intention step; independent project evaluations skipped.
- Preserve unsuccessful/invalid model votes as experiment outcomes.

Backend compatibility changes concern model loading and chat-template support.
They must leave the protocol above unchanged. Pin each model/tokenizer to the
same full checkpoint revision with `HARP_MODEL_REVISION`, and record the installed
libraries and input hashes in the run manifest. Use model-native chat templates;
document any required role adaptation as a compatibility difference when comparing
against Qwen. This is one exploratory run per configuration, not a multi-seed study.

## Prepare and launch

Use the isolated cross-model checkout and its prepared Python environment. Cache
the complete pinned model snapshots before requesting GPUs. Compute jobs run in
Hugging Face offline mode, and `uv --frozen --no-sync` uses the existing environment
without installing dependencies. `HF_HOME` points at the cache directory containing
`models--google--gemma-4-31B-it` or
`models--meta-llama--Llama-3.1-8B-Instruct` directly; if unset, it defaults to
`$SCRATCH/huggingface`.

Before submitting, create `logs` in the checkout root. Export the prepared
`UV_PROJECT_ENVIRONMENT`, the full 40-character `HARP_MODEL_REVISION`, and any
explicit `HF_HOME`. Supply a fresh absolute output directory separately for each
model. Do not reuse the Qwen result directory.

```bash
mkdir -p logs
sbatch --job-name=harp_gemma4 --array=0,5%1 \
  experiments/run_crossmodel_matrix.sbatch \
  experiments/matrix_fullconfigs_gemma4.json /absolute/path/to/gemma-batch
```

Inspect smoke results at indices `0` and `5`, including the corrected unequal
bargaining case. Once these finish and pass the existing structural/configuration
checks, submit the remaining indices with `--array=1-4,6-59%1` using the same matrix,
revision and batch directory. Llama uses the same commands with its matrix and a
separate directory; add `--mem=32G` to its `sbatch` command.

The default allocation is one A100 80GB (`a100l`), eight CPUs, 128GB host RAM and two
hours per configuration in the `long` partition. Keep at most one active array per
model and the `%1` limit, giving at most two concurrent GPUs across the two models.
The default array covers `0-59%1`; use it only if no smoke entries have already run.

The launcher verifies cached checkpoint files and rejects model, matrix, revision,
or output-directory mismatches. It records `batch_identity.json` on the first
actual launch. A pre-created directory may contain a matching `run_manifest.json`;
other old files are refused without a matching batch identity. Existing selected
result files are never overwritten. A missing-output configuration may be retried
once only after its previous job has terminated with a diagnosed infrastructure
failure. Preserve the failed-attempt logs and frozen settings, and record the
retry job ID. Invalid votes, truncation and nonagreement are not retry reasons.

For a read-only command/cache preflight, set `SLURM_SUBMIT_DIR` to the checkout root
and `SLURM_ARRAY_TASK_ID` to the chosen index, then call the script with `bash` and
append `--dry-run`. This checks the pinned cache and prints the pilot command without
loading model weights or creating result files.

## Review and handoff

Check each model against its own matrix with `check_full_results.py`, then produce
its summary with `summarize_full_run.py`. Review all three models together before
publishing anything to GitHub or sending Florian a Slack update. Record any model
loading or formatting failures separately from valid runs whose agents disagree.
