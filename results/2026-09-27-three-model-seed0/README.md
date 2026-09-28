# Qwen, Gemma and Llama: 60 configurations each, seed 0

Experiments completed on 27 September 2026; results prepared for sharing on 28 September 2026. This is a results archive based on upstream commit `46c57cfbbc1a4e8a2a1adaca93c48667bda4ab92`. It does not change the repository's active runner, prompts or data.

Start with the **[three-model comparison](crossmodels_20260927/report/THREE_MODEL_COMPARISON.md)**. The [Chinese readout](crossmodels_20260927/report/READOUT_ZH.md) and [backend comparability notes](crossmodels_20260927/report/BACKEND_COMPARABILITY.md) provide further context.

## Results at a glance

Arrows denote initial → final. Each model has 60 configurations and 180 ballots at each stage.

| Model | Valid ballots / 180 | Exact agreement / 60 | Feasible aggregation / 60 | Conditional final normalized welfare |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-30B-A3B-Instruct-2507 | 180 → 180 | 0 → 8 | 37 → 52 | 0.945983 (n=52) |
| Gemma-4-31B-it | 180 → 179 | 0 → 15 | 31 → 58 | 0.967815 (n=58) |
| Llama-3.1-8B-Instruct | 178 → 179 | 1 → 4 | 46 → 48 | 0.926704 (n=48) |

All 180 expected results are structurally complete and configuration-matched, with no analysis errors. Invalid model votes remain in the denominators. Both new models pass 720-call diagnostics with zero max-token hits; Qwen predates this instrumentation, so an equivalent truncation measurement is unavailable.

**These are descriptive single-seed results, not a statistically significant model ranking.** Exact agreement differs from feasible majority aggregation. Welfare is conditional on each model's feasible outcomes, so the successful subsets differ. Model size/architecture, native chat templates and inherited decoding defaults also differ, including reconstructed top-k values of 20 / 64 / 50 for Qwen / Gemma / Llama. No invalid vote or nonagreement was rerun to improve the outcome.

## Contents

| Item | Location |
| --- | --- |
| Qwen: 60 unchanged raw JSONs | [results](qwen_fullconfigs_20260927/results/seed0/) |
| Gemma: 60 unchanged raw JSONs | [results](crossmodels_20260927/results/gemma4_seed0/) |
| Llama: 60 unchanged raw JSONs | [results](crossmodels_20260927/results/llama8b_seed0/) |
| Qwen coverage, per-run CSV and report | [report](qwen_fullconfigs_20260927/report/SUMMARY.md) |
| Gemma coverage, CSV, report and generation diagnostics | [report](crossmodels_20260927/report/gemma4/SUMMARY.md) |
| Llama coverage, CSV, report and generation diagnostics | [report](crossmodels_20260927/report/llama8b/SUMMARY.md) |
| Model revisions, dependencies and input hashes | [Qwen metadata](qwen_fullconfigs_20260927/provenance/manifest.public.json), [Gemma metadata](crossmodels_20260927/provenance/manifest_gemma4.public.json), [Llama metadata](crossmodels_20260927/provenance/manifest_llama8b.public.json) |
| Frozen execution/analysis inputs, not changes to active code | [Qwen snapshot](reproduction/qwen/), [Gemma/Llama snapshot](reproduction/crossmodels/) |
| Publication transformations and SHA-256 inventory | [publication manifest](publication_manifest.json) |

The raw JSONs include the original model replies, parsed ballots, discussion and metrics; Gemma/Llama also contain runtime and per-call generation diagnostics. The two `batch_identity.json` files are metadata and are not counted among the 180 result JSONs.

Frozen snapshots contain all files listed by their execution manifests and the analysis helpers needed below. They intentionally remain separate: the original Qwen path is not replaced by the newer native Gemma/Llama backends. These are archival inputs, not proposed changes to the main implementation.

## Verify and reproduce the analysis (CPU only)

From the repository root, with Python 3.10 or later:

```bash
python3 results/2026-09-27-three-model-seed0/verify_bundle.py
```

This uses only the Python standard library. It verifies the publication checksums and frozen input hashes, checks that all three matrices cover the same ordered configurations, regenerates the three reports in a temporary directory, compares every CSV row and overall metric with the published reports, and rechecks Gemma/Llama generation diagnostics. It does not load models, download weights, authenticate to services or run new experiments. Exit 0 means all checks pass; the bundled results are never rewritten.

For manual report regeneration, use the relevant frozen snapshot's `experiments/summarize_full_run.py`, passing its matrix, the matching raw directory, and a **new** output directory. For example:

```bash
python3 results/2026-09-27-three-model-seed0/reproduction/crossmodels/experiments/summarize_full_run.py \
  --matrix results/2026-09-27-three-model-seed0/reproduction/crossmodels/experiments/matrix_fullconfigs_gemma4.json \
  --results-dir results/2026-09-27-three-model-seed0/crossmodels_20260927/results/gemma4_seed0 \
  --report-dir /tmp/harp-gemma-recomputed
```

The [cross-model run notes](reproduction/crossmodels/experiments/CROSSMODEL_RUN.md) document the original GPU launch procedure. Running generation again requires appropriate compute, legitimate access to the gated models, the exact pinned checkpoints, and compatible installed packages. Environment/package versions are recorded in the public manifests. A local `uv sync` need not reproduce the shared historical cluster environment exactly; inspect the manifest versions rather than assuming it does. Do not use the older scenario examples in the snapshot's upstream README as the 60-entry matrix for this batch.

## Publication and privacy notes

- All 180 raw results, the two batch identities, CSV data, frozen source files and experiment matrices are copied byte-for-byte from the audited local archive.
- Public manifest exports omit hostnames and machine-specific checkout/environment/cache paths, and record each original manifest's SHA-256. Model/dependency pins and source/checkpoint hashes are unchanged.
- Published report copies replace author-local absolute paths with paths relative to this bundle root and remove a compute-node name. Numeric results and response text are unchanged. The original reports and immutable manifests remain retained locally.
- Cluster logs, operational status/history, automation details, credentials, model weights and caches are not included. Original logs remain retained, including two post-save Llama Slurm epilog warnings; both affected outputs passed checks and had successful job exits.
- The dated analysis reports describe the state when the experiments completed, before this publication. Statements there that no GitHub upload had yet occurred are historical; this README documents the later sharing step. No Slack message is part of this publication.

## Cases worth reviewing

Gemma's `RFQ_optimal` final A1 gives two JSON proposals; Llama's `ERG_impossible` includes a duplicate project selection and an invalid JSON string; `EGF_conflictual` includes another duplicate selection; and one `EGQ_optimal` discussion proposes three projects. These are preserved scientific outcomes, not missing or broken result files. The comparison report distinguishes them from infrastructure issues.
