# Three-model full-configuration comparison

Completed and audited on 27 September 2026. All three models have **60/60 structurally complete, configuration-matched seed-0 results**, with zero analysis errors. Gemma and Llama additionally pass the full 720-call diagnostic checks for each model. This is a descriptive pilot, not a statistically significant model ranking.

## Main results

Each model has 180 ballots at each stage and 60 configuration-level outcomes. Arrows below mean initial → final. Vote validity is measured with the original tolerant parser, not a strict JSON-only requirement.

| Measure | Qwen3-30B-A3B-Instruct-2507 | Gemma-4-31B-it | Llama-3.1-8B-Instruct |
| --- | ---: | ---: | ---: |
| Complete configurations | 60/60 | 60/60 | 60/60 |
| Valid initial → final ballots | 180/180 → 180/180 | 180/180 → 179/180 | 178/180 → 179/180 |
| Valid initial → final ballot rate | 100% → 100% | 100% → 99.4% | 98.9% → 99.4% |
| Exact unanimous agreement | 0/60 → 8/60 | 0/60 → 15/60 | 1/60 → 4/60 |
| Final exact-agreement rate | 13.3% | 25.0% | 6.7% |
| Feasible majority aggregate | 37/60 → 52/60 | 31/60 → 58/60 | 46/60 → 48/60 |
| Final feasible-aggregate rate | 86.7% | 96.7% | 80.0% |
| Final normalized welfare, conditional | 0.945983 (n=52) | 0.967815 (n=58) | 0.926704 (n=48) |
| Final minimum utility, conditional | 4.365385 (n=52) | 4.534483 (n=58) | 4.270833 (n=48) |
| Paired normalized-welfare change | −0.026147 (n=35) | +0.010480 (n=30) | −0.039986 (n=38) |
| Out-of-catalog project mentions | 0 | 0 | 0 |

“Exact agreement” means all three agents choose the same unordered pair. A “feasible aggregate” means the unchanged majority procedure produces a valid two-project allocation; it does not require unanimous agreement. In particular, Gemma's 58 feasible outcomes are **not** 58 consensus outcomes.

Welfare and minimum utility are averaged only over feasible final outcomes with available numeric metrics. The models' eligible subsets differ, so these conditional means are not a comparison on an identical set of successful configurations. Infeasible outcomes are not assigned zero welfare. Paired change is final minus initial welfare, restricted to runs feasible at both stages; it excludes newly feasible and newly infeasible runs.

## What changed after discussion?

| Feasibility transition | Qwen | Gemma | Llama |
| --- | ---: | ---: | ---: |
| Feasible → feasible | 35 | 30 | 38 |
| Infeasible → feasible | 17 | 28 | 10 |
| Feasible → infeasible | 2 | 1 | 8 |
| Infeasible → infeasible | 6 | 1 | 4 |
| Net increase in feasible outcomes | +15 | +27 | +2 |

Under these particular conditions, Gemma shows the largest observed increase in feasible aggregation and the most final exact agreements. Qwen also shows a substantial feasibility increase. Llama starts with more feasible aggregates, but its 10 newly feasible cases are largely offset by eight losses. For Llama's 38 both-feasible runs, normalized welfare improves in two, declines in 11 and is unchanged in 25.

These are before/after descriptions, not proof that discussion causally improves or harms performance. There is no separate no-discussion resampling control. More agreement also does not imply more welfare: the paired conditional welfare changes for Qwen and Llama are negative, despite increased agreement/feasibility counts.

Final agreement labels provide a separate view:

| Final label | Qwen | Gemma | Llama |
| --- | ---: | ---: | ---: |
| Agreement | 8 | 15 | 4 |
| Partial agreement | 31 | 29 | 27 |
| Non-agreement | 21 | 15 | 28 |
| Invalid vote | 0 | 1 | 1 |

Scenario names such as `optimal` and `impossible` are configuration labels, not correctness certificates for individual outputs. A feasible or unanimous result in an `impossible` scenario should not be called a contradiction without checking the intended definition of that scenario.

## Formatting and generation diagnostics

| Check | Qwen | Gemma | Llama |
| --- | --- | --- | --- |
| Measured EOS completions | Not instrumented | 720/720 | 720/720 |
| Measured max-token hits | Unavailable | 0/720 | 0/720 |
| Native response-processing errors | Not instrumented | 0 | 0 |
| Empty returned responses | Not instrumented | 0 | 0 |
| Strict JSON-only ballots | Not re-audited here | 0/360 | 359/360 |
| Valid ballots across both stages | 360/360 | 359/360 | 357/360 |

Gemma wraps all 360 ballots in Markdown fences. The frozen tolerant parser accepts the wrapper; this must not be described as strict JSON-only adherence. Llama is closer to the requested output format, but syntactically valid JSON can still contain an invalid selection, such as a repeated project ID.

Preserved cases worth reviewing with Florian:

- **Gemma, index 48, `RFQ_optimal`, final A1:** two JSON proposals separated by self-correction. The original parser rejects them with `Extra data`. The response ends with EOS at 491/512 tokens: it is not truncation or an infrastructure failure. The other infeasible Gemma final outcome is index 15, `ERQ_conflictual`.
- **Llama, index 2, `ERG_impossible`:** initial A3 selects `P14` twice; final A2 includes unescaped literal newlines inside its JSON justification.
- **Llama, index 21, `EGF_conflictual`:** initial A2 selects `P14` twice.
- **Llama, index 24, `EGQ_optimal`, A3→A1 discussion:** proposes three projects (`P32`, `P17`, `P23`), despite the two-project constraint. Its final ballots are valid. Ballot validity therefore does not establish that all discussion messages follow the scenario constraints.

All these responses remain unchanged. No invalid vote, non-agreement or other scientific outcome was repaired or rerun. Zero truncations in the two instrumented models does not establish a measured zero-truncation rate for Qwen: its earlier raw outputs contain no equivalent per-call records.

## Fixed design and remaining comparability limits

The run covers the same 60 ordered profile/project configurations: ten profile combinations × six scenario types, one seed (0) each. Each configuration has three agents, five candidate projects and two selected projects per ballot; three initial votes, six directed critiques and three final votes give 12 generations per run. Prompt text, data, protocol, vote parser and majority rule are unchanged. Temperature is 0.7, top-p 0.9 and max-new-tokens 512; thinking and intention are disabled and standalone ratings are skipped.

The models have different sizes/architectures and native chat templates, tokenizers and response handling. The shared explicit sampling settings do not eliminate inherited defaults: an offline reconstruction using the installed Transformers 5.14.1 preparation code gives **top_k 20 for Qwen, 64 for Gemma and 50 for Llama**. Llama's saved null value is filled from a library default; it does not mean disabled top-k. This reconstruction is not a new inference trace. See [backend comparability](BACKEND_COMPARABILITY.md).

This experiment supports descriptions of these particular systems under these settings. It does not isolate model size, backend, decoding choice or deliberation as a cause. Sixty different configurations are not 60 repeated seeds of one condition, and no significance or controlled scaling claim is made.

## Completion and provenance

| Model | Recorded checkpoint revision | GPU arrays | Last GPU task finished, UTC |
| --- | --- | --- | --- |
| Qwen | `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` | 10951257, 10951287 | 2026-09-27 13:12:19 |
| Gemma | `842da3794eaa0b77d5f08bae87a17459d91ff475` | 10952157, 10952420 | 2026-09-27 17:17:59 |
| Llama | `0e9e39f249a16976918f6564b8830bc894c89659` | 10953100, 10953331 | 2026-09-27 17:23:52 |

Qwen's revision is the cached checkpoint revision recorded in its execution manifest, not a newly instrumented runtime pin. The new Gemma/Llama loaders explicitly pin revisions and record requested/resolved runtime revisions; the original Qwen loader and outputs are preserved as executed.

Both new models' 60 tasks completed with exit 0:0; the final user queue was empty. All 120 raw results and completed GPU logs were retrieved using nondeleting transfers that protect existing raw files. Source/input hashes and immutable manifests match locally and remotely. Independent audits recomputed every ballot parse, aggregation, recorded metric and report denominator, and matched all 1,440 new generation records to the protocol. Native-tokenizer reconstruction was performed on both smoke cases per new model, not repeated for all 60.

Llama logs for indices 5 and 59 contain post-save Slurm task-epilog ambiguous-redirect messages. Both outputs are complete, pass the checks and have successful job exit codes. The logs are retained; no retry was warranted. Gemma logs have no detected error/warning markers. No retry jobs, environment changes, extra seeds, GitHub pushes or Slack messages were made. The original Qwen baseline remains unchanged.

## Reports and next discussion

- [Qwen per-configuration report](../../qwen_fullconfigs_20260927/report/SUMMARY.md)
- [Gemma per-configuration report](gemma4/SUMMARY.md)
- [Llama per-configuration report](llama8b/SUMMARY.md)
- [Backend and decoding caveats](BACKEND_COMPARABILITY.md)

The batch is shared for asynchronous review. Useful questions are whether the intended benchmark target is consensus or feasible aggregation; what explains the cases that lose feasibility or welfare after discussion; and whether subsequent experiments should prioritize repeated seeds, a no-discussion control or more tightly matched generation settings. These are proposals for discussion, not experiments already authorized or launched. See the bundle README for this publication's scope; no Slack message is included in the upload.
