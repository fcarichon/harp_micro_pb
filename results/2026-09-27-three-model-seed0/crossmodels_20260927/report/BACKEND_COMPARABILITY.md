# Cross-model backend comparability

This is a descriptive comparison of one seed per configuration, not a controlled model-scaling or statistical-significance study. The three model IDs, sizes, native templates and some inherited generation defaults differ. Do not attribute every observed difference solely to model quality.

## Fixed conditions

The same 60 ordered profile/project configurations, seed 0, original prompt contents, data, discussion protocol, vote parser and deterministic aggregation are used. Each run has three initial votes, six directed critiques and three final votes. All use sampling, temperature 0.7, top-p 0.9 and max-new-tokens 512; thinking and intention steps are disabled, and standalone ratings are skipped. The shared environment is reused without changes.

## Native defaults: verified, not assumed identical

At 16:48 UTC on 2026-09-27, a CPU-only check read the installed Transformers 5.14.1 source and invoked its `GenerationMixin._prepare_generation_config` using pinned local checkpoint generation configurations and the experiment's explicit overrides. No model weights were loaded, no responses generated, and no source or run settings changed. Gemma/Llama overrides came from saved runtime metadata; Qwen overrides were reconstructed from the frozen legacy loader and its pinned cached tokenizer.

| Model | Checkpoint top_k | Prepared top_k | PAD ID used | EOS IDs |
| --- | ---: | ---: | ---: | --- |
| Qwen/Qwen3-30B-A3B-Instruct-2507 | 20 | 20 | 151645 | 151645, 151643 |
| google/gemma-4-31B-it | 64 | 64 | 0 | 1, 106, 50 |
| meta-llama/Llama-3.1-8B-Instruct | null | 50 | 128009 | 128001, 128008, 128009 |

The installed `generation/utils.py` method fills unset checkpoint values from global defaults before applying explicit call overrides. `GenerationConfig._get_default_generation_params()` sets top_k to 50. Thus Llama's serialized `top_k=null` does **not** mean top-k filtering is disabled: the reconstructed prepared value is 50. In all three reconstructed configurations, typical_p and repetition_penalty are 1.0, num_beams is 1, and min_p is unset. This is an offline reconstruction of library configuration preparation, not a newly instrumented inference trace. Raw runtime metadata is preserved unchanged.

Reconstruction sources in the existing environment:

- `transformers/generation/utils.py`, `_prepare_generation_config` (lines 1733–1805).
- `transformers/generation/configuration_utils.py`, `_get_default_generation_params` (lines 590 onward; top_k at line 606).
- `transformers/generation/utils.py`, top-k logits-warper condition (lines 1279–1281).

Pinned checkpoint generation-config hashes:

| Model | Revision | generation_config.json SHA-256 |
| --- | --- | --- |
| Qwen | 0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe | 19d306dd769db12a9d710b44cf7f83b635efbe5166b84fb4358a08fb7d88bb53 |
| Gemma | 842da3794eaa0b77d5f08bae87a17459d91ff475 | d4226bbe3117d2d253ba4609720ba82c6c4ce4627a9a6ae05387c78983ac03de |
| Llama | 0e9e39f249a16976918f6564b8830bc894c89659 | 189fb0c0d7fd8a527db217c0a60a0e013f0394cd8800f9697a666a9e75e5f7fd |

## Templates and response handling

- Qwen retains the original renderer-then-tokenizer path and legacy reasoning-tag normalization. Its completed baseline is not rewritten or rerun.
- Gemma uses its native processor/template, tokenizes once, and returns the processor's parsed content while separately recording raw completions. The native multimodal class is used for text-only inputs.
- Llama uses its native system/user/assistant template, tokenizes once, and decodes with special tokens skipped, without Qwen reasoning-tag stripping.
- The two new backends' smoke prompts were independently reconstructed with real pinned tokenizers/processors. All 24 input-token counts per model matched. Equal text prompts do not imply equal tokens or equal effective context lengths across tokenizers.

## Reporting safeguards

- Report strict JSON formatting separately from valid parsed votes. The unchanged tolerant parser accepts some wrapped responses; structurally complete result files can still contain invalid model votes.
- Invalid votes, output truncation and nonagreement remain scientific outcomes and must not be silently repaired or rerun.
- Report exact unanimous agreement separately from feasible majority aggregation.
- Welfare is conditional on feasible final allocations, with denominators shown; paired changes require feasibility at both stages. Do not give infeasible outcomes an invented welfare of zero.
- Gemma/Llama include per-call token/EOS diagnostics. Qwen was completed before this instrumentation was added; do not infer an equally measured Qwen truncation rate from valid ballots alone.
- All three runs use seed 0 only. Different configurations are not independent repetitions of the same experimental condition, and different model sizes/architectures and top-k values prevent a controlled scaling claim.

## Preserved Qwen baseline check

A read-only check at 17:09 UTC confirmed all 35 original Qwen source/input hashes still match locally and on Mila, and all 60 raw results plus the immutable manifest match their remote copies by itemized checksum comparison. The original report remains 60/60 complete with no analysis errors. All 19 prompt/data files shared with the cross-model checkout are byte-identical. The environment package versions in Qwen's manifest match the cross-model manifest versions.

None of the 60 Qwen raw results contains `generation_records` or `model_runtime`; Qwen's truncation/EOS rate is therefore unavailable under the new per-call diagnostic method. Its 180/180 valid initial and final ballots do not replace that missing measurement. This check did not rewrite the baseline reports, outputs, code or manifest.
