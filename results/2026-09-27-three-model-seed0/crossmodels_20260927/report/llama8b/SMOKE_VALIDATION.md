# Llama smoke validation — 2026-09-27

Both smoke tasks in array `10953100` passed the execution and analysis checks. They remain part of the requested 60 seed-0 runs and must not be rerun.

- Model: `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659`.
- Indices: 0 (`ERG_optimal`) and 5 (`ERG_unequal_bargaining`). Both completed on <compute-node> with job, derived and application-step exit codes 0:0; elapsed times 103 and 70 seconds.
- Four safetensors shards loaded through `LlamaForCausalLM`; logs show 291/291 weights loaded. Recorded runtime: BF16, `model_device=cuda:0`, native `TokenizersBackend`, thinking disabled. `hf_device_map` is null in this installed environment; this alone is not evidence of CPU execution. A100 80GB allocation and index-0 GPU accounting independently show GPU execution (peak 16,724 MiB).
- Both outputs are structurally complete and match the exact requested configurations. The full report is intentionally partial (2/60), with zero malformed files, configuration mismatches or analysis errors.
- All 24 calls correspond exactly to the expected three initial votes, six directed critiques and three final votes per run. All ended with EOS 128009; no truncations, empty answers or parser errors.
- Independent CPU-only audit used the real pinned tokenizer, without loading model weights. Original pilot functions reconstructed all 24 prompts: every recorded input-token count matched, with one BOS token and the native system/user/assistant headers. Tokenizing the rendered template with `add_special_tokens=False` matched native template tokenization.
- All 24 raw output token counts and cleaned decodes matched. Input lengths were 823–1,899 tokens and output lengths 71–325, below the fixed 512 limit.
- All 12 initial/final ballots are strict JSON (not Markdown-fenced). Independent parsing, majority aggregation and brute-force metric recomputation found no differences.
- All 39 source/input hashes match locally and remotely; all five cached checkpoint metadata hashes match the immutable manifest. Itemized checksum rsync found no differences in raw outputs, completed logs or the manifest (directory timestamps are not result-content differences).

## Observations, not full-matrix conclusions

Initial/final valid ballots are 6/6 at each stage. Neither run has exact agreement at either stage. Feasible majority aggregation changes from 1/2 to 2/2. Final labels are one partial agreement and one nonagreement. Conditional final normalized welfare is 0.9090909091 (n=2), minimum utility 4 (n=2), and paired normalized-welfare change 0 (n=1).

| Scenario | Final allocation | Final agreement | Normalized welfare |
| --- | --- | --- | ---: |
| ERG_optimal | P20, P25 | Partial | 1.0000000000 |
| ERG_unequal_bargaining | P16, P20 | None | 0.8181818182 |

## Preserved caveats

- Transformers warns that BPE cleanup ignores `clean_up_tokenization_spaces=True`; the native behavior is retained, with no tokenizer-setting change.
- Index 5 logs post-save `/etc/slurm/slurmtask_epilog` ambiguous-redirect errors. Both saved results and all 24 calls are complete, and job/derived/application-step exit codes are 0:0. This is recorded as a cluster epilog/logging issue, not a missing-output failure. No retry is justified or performed; peak-memory accounting for this task is unavailable in its log.
- Native generation defaults differ across backends. Llama's serialized effective configuration has `top_k=null`, whereas Gemma records `top_k=64`. A later CPU-only reconstruction using the installed library's actual configuration-preparation method confirmed Llama's null falls back to 50; Qwen prepares 20 and Gemma 64. See `../BACKEND_COMPARABILITY.md`. Raw metadata and all running settings remain unchanged. Temperature 0.7, top-p 0.9 and max-new-tokens 512 remain fixed; do not silently equate all other defaults.

After these checks, only remaining indices `1-4,6-59%1` were submitted as array `10953331` at 16:09:26 UTC, with one A100 task at a time and 32GB host RAM. Submission is not completion. No prompt, data, protocol, environment or scientific setting was changed.
