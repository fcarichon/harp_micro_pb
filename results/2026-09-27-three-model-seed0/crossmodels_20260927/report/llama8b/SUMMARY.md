# HARP full-configuration experiment results

Status: **COMPLETE** — 60/60 expected results are structurally complete and configuration-matched; 60/60 are included in this analysis.

Generated (UTC): 2026-09-27T17:28:44.755189+00:00

## Coverage

| Category | Matrix entries |
|---|---:|
| Expected | 60 |
| completed | 60 |
| missing | 0 |
| malformed | 0 |
| config_mismatch | 0 |
| Analysis errors among completed records | 0 |

Only completed records whose recorded settings match the requested matrix are analyzed. Model vote failures and non-agreement remain results and are included in the denominators. Missing, malformed, or mismatched files are excluded.

## Experimental scope and interpretation

Requested seed values: 0. Each matrix entry represents one run of a particular profile/project configuration.

This is one seed-0 run per configuration. Scenario groups pool different profile/project configurations. They are not independent seed repetitions of the same experiment; these descriptive averages do not establish sampling uncertainty or statistical significance.

Exact agreement means all three agents chose the same project pair. A feasible aggregate can also result from disagreement under the deterministic majority rule. The labels `optimal`, `impossible`, and similar names identify the configured scenarios, not a correctness judgment about an observed response.

Normalized welfare and minimum utility are averaged only over runs with a feasible final aggregate and an available numeric metric. Every mean displays its own denominator n. Paired welfare change is final minus initial normalized welfare, averaged only over runs with feasible aggregates and numeric welfare at both stages. Infeasible runs are not assigned zero welfare. `NA` means the required observations are absent.

## Overall results

| Measure | Count / denominator or conditional mean |
|---|---:|
| Valid initial votes | 178/180 (98.9%) |
| Valid final votes | 179/180 (99.4%) |
| Initial exact agreement | 1/60 (1.7%) |
| Final exact agreement | 4/60 (6.7%) |
| Feasible initial aggregates | 46/60 (76.7%) |
| Feasible final aggregates | 48/60 (80.0%) |
| Final normalized welfare, conditional | 0.927 (n=48) |
| Final minimum utility, conditional | 4.271 (n=48) |
| Paired normalized-welfare change | -0.040 (n=38) |
| Out-of-catalog project mentions | 0 occurrences |

Final agreement categories among included runs: agreement: 4/60, invalid_vote: 1/60, non_agreement: 28/60, partial_agreement: 27/60.

## Results by scenario type

`n / expected` is the number of analyzed configurations versus the requested matrix entries in that group. Vote denominators are 3 × n; agreement and feasibility denominators are n.

| Model | Scenario type | n / expected | Valid initial votes | Valid final votes | Initial exact agreement | Final exact agreement | Feasible final aggregates | Final norm. welfare (conditional) | Min utility (conditional) | Paired welfare change |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Llama-3.1-8B-Instruct | coalition | 10/10 | 30/30 (100.0%) | 30/30 (100.0%) | 0/10 (0.0%) | 1/10 (10.0%) | 9/10 (90.0%) | 0.960 (n=9) | 5.111 (n=9) | -0.020 (n=9) |
| Llama-3.1-8B-Instruct | conflictual | 10/10 | 29/30 (96.7%) | 30/30 (100.0%) | 0/10 (0.0%) | 0/10 (0.0%) | 8/10 (80.0%) | 0.980 (n=8) | 2.500 (n=8) | 0.000 (n=4) |
| Llama-3.1-8B-Instruct | impossible | 10/10 | 29/30 (96.7%) | 29/30 (96.7%) | 0/10 (0.0%) | 0/10 (0.0%) | 5/10 (50.0%) | 0.933 (n=5) | 2.000 (n=5) | 0.143 (n=4) |
| Llama-3.1-8B-Instruct | optimal | 10/10 | 30/30 (100.0%) | 30/30 (100.0%) | 0/10 (0.0%) | 2/10 (20.0%) | 10/10 (100.0%) | 0.918 (n=10) | 5.000 (n=10) | -0.082 (n=10) |
| Llama-3.1-8B-Instruct | sub-optimal | 10/10 | 30/30 (100.0%) | 30/30 (100.0%) | 0/10 (0.0%) | 1/10 (10.0%) | 9/10 (90.0%) | 0.838 (n=9) | 5.556 (n=9) | -0.156 (n=7) |
| Llama-3.1-8B-Instruct | unequal_bargaining | 10/10 | 30/30 (100.0%) | 30/30 (100.0%) | 1/10 (10.0%) | 0/10 (0.0%) | 7/10 (70.0%) | 0.944 (n=7) | 4.143 (n=7) | 0.000 (n=4) |

## Per-run results

Full analysis fields are in `results.csv`; raw outputs remain in the results directory. `Switches` counts changed parsed selections, including transitions to or from an invalid vote.

| Index | Scenario | Seed | Valid votes initial / final | Initial agreement | Final agreement | Final allocation | Norm. welfare initial / final | Paired change | Final min utility | Switches | Out-of-catalog mentions | Raw file |
|---:|---|---:|---|---|---|---|---|---:|---:|---:|---:|---|
| 0 | ERG_optimal | 0 | 3/3 / 3/3 | partial_agreement | partial_agreement | P20+P25 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_ERG_optimal_seed0.json |
| 1 | ERG_sub-optimal | 0 | 3/3 / 3/3 | partial_agreement | partial_agreement | P21+P20 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_ERG_sub-optimal_seed0.json |
| 2 | ERG_impossible | 0 | 2/3 / 2/3 | invalid_vote | invalid_vote | infeasible_vote | NA / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERG_impossible_seed0.json |
| 3 | ERG_conflictual | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P21 | NA / 0.947 | NA | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERG_conflictual_seed0.json |
| 4 | ERG_coalition | 0 | 3/3 / 3/3 | partial_agreement | partial_agreement | P20+P25 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERG_coalition_seed0.json |
| 5 | ERG_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P20 | NA / 0.818 | NA | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERG_unequal_bargaining_seed0.json |
| 6 | ERF_optimal | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P20+P22 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERF_optimal_seed0.json |
| 7 | ERF_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P20+P17 | 1.000 / 0.818 | -0.182 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERF_sub-optimal_seed0.json |
| 8 | ERF_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P17+P18 | 0.667 / 0.667 | 0.000 | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_ERF_impossible_seed0.json |
| 9 | ERF_conflictual | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P22+P17 | NA / 0.947 | NA | 2.000 | 1 | 0 | Llama-3.1-8B-Instruct_v2_ERF_conflictual_seed0.json |
| 10 | ERF_coalition | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P20+P22 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERF_coalition_seed0.json |
| 11 | ERF_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P22+P1 | NA / 0.920 | NA | 5.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERF_unequal_bargaining_seed0.json |
| 12 | ERQ_optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P20+P23 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_optimal_seed0.json |
| 13 | ERQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P20+P18 | 1.000 / 0.818 | -0.182 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_sub-optimal_seed0.json |
| 14 | ERQ_impossible | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P18+P8 | 0.714 / 1.000 | 0.286 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_impossible_seed0.json |
| 15 | ERQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P23+P18 | NA / 1.000 | NA | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_conflictual_seed0.json |
| 16 | ERQ_coalition | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P20 | 1.000 / 0.818 | -0.182 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_coalition_seed0.json |
| 17 | ERQ_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | NA / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_ERQ_unequal_bargaining_seed0.json |
| 18 | EGF_optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P21+P18 | 1.000 / 0.636 | -0.364 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGF_optimal_seed0.json |
| 19 | EGF_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 1.000 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGF_sub-optimal_seed0.json |
| 20 | EGF_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P17 | NA / 1.000 | NA | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_EGF_impossible_seed0.json |
| 21 | EGF_conflictual | 0 | 2/3 / 3/3 | invalid_vote | non_agreement | P17+P22 | NA / 1.000 | NA | 2.000 | 1 | 0 | Llama-3.1-8B-Instruct_v2_EGF_conflictual_seed0.json |
| 22 | EGF_coalition | 0 | 3/3 / 3/3 | non_agreement | agreement | P21+P22 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGF_coalition_seed0.json |
| 23 | EGF_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P21+P22 | NA / 1.000 | NA | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGF_unequal_bargaining_seed0.json |
| 24 | EGQ_optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P21+P32 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_optimal_seed0.json |
| 25 | EGQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P21+P18 | 1.000 / 0.818 | -0.182 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_sub-optimal_seed0.json |
| 26 | EGQ_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P18 | 0.714 / 1.000 | 0.286 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_impossible_seed0.json |
| 27 | EGQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P23 | 1.000 / 1.000 | 0.000 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_conflictual_seed0.json |
| 28 | EGQ_coalition | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P32+P21 | 1.000 / 1.000 | 0.000 | 6.000 | 1 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_coalition_seed0.json |
| 29 | EGQ_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | NA / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_EGQ_unequal_bargaining_seed0.json |
| 30 | EFQ_optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P22+P3 | 1.000 / 0.955 | -0.045 | 5.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_optimal_seed0.json |
| 31 | EFQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P22+P18 | NA / 0.818 | NA | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_sub-optimal_seed0.json |
| 32 | EFQ_impossible | 0 | 3/3 / 3/3 | partial_agreement | non_agreement | P16+P17 | 1.000 / 1.000 | 0.000 | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_impossible_seed0.json |
| 33 | EFQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P23+P17 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_conflictual_seed0.json |
| 34 | EFQ_coalition | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P16+P23 | 0.818 / 0.818 | 0.000 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_coalition_seed0.json |
| 35 | EFQ_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P24+P23 | 0.917 / 0.917 | 0.000 | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_EFQ_unequal_bargaining_seed0.json |
| 36 | RGF_optimal | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P18+P25 | 1.000 / 0.636 | -0.364 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGF_optimal_seed0.json |
| 37 | RGF_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P17+P25 | 1.000 / 0.818 | -0.182 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RGF_sub-optimal_seed0.json |
| 38 | RGF_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 0.625 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGF_impossible_seed0.json |
| 39 | RGF_conflictual | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 0.900 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGF_conflictual_seed0.json |
| 40 | RGF_coalition | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P25+P30 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RGF_coalition_seed0.json |
| 41 | RGF_unequal_bargaining | 0 | 3/3 / 3/3 | partial_agreement | partial_agreement | P2+P26 | 0.955 / 0.955 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGF_unequal_bargaining_seed0.json |
| 42 | RGQ_optimal | 0 | 3/3 / 3/3 | non_agreement | agreement | P25+P32 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_optimal_seed0.json |
| 43 | RGQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P25+P18 | 1.000 / 0.818 | -0.182 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_sub-optimal_seed0.json |
| 44 | RGQ_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | NA / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_impossible_seed0.json |
| 45 | RGQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 0.737 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_conflictual_seed0.json |
| 46 | RGQ_coalition | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P25+P28 | 1.000 / 1.000 | 0.000 | 6.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_coalition_seed0.json |
| 47 | RGQ_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P25+P28 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RGQ_unequal_bargaining_seed0.json |
| 48 | RFQ_optimal | 0 | 3/3 / 3/3 | non_agreement | agreement | P26+P3 | 1.000 / 0.955 | -0.045 | 5.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_optimal_seed0.json |
| 49 | RFQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | agreement | P18+P26 | 1.000 / 0.818 | -0.182 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_sub-optimal_seed0.json |
| 50 | RFQ_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 0.667 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_impossible_seed0.json |
| 51 | RFQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P28+P18 | 0.947 / 0.947 | 0.000 | 2.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_conflictual_seed0.json |
| 52 | RFQ_coalition | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P26+P28 | 1.000 / 1.000 | 0.000 | 6.000 | 3 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_coalition_seed0.json |
| 53 | RFQ_unequal_bargaining | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P29+P28 | 1.000 / 1.000 | 0.000 | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_RFQ_unequal_bargaining_seed0.json |
| 54 | GFQ_optimal | 0 | 3/3 / 3/3 | partial_agreement | partial_agreement | P32+P3 | 1.000 / 1.000 | 0.000 | 6.000 | 1 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_optimal_seed0.json |
| 55 | GFQ_sub-optimal | 0 | 3/3 / 3/3 | non_agreement | non_agreement | P18+P32 | NA / 0.818 | NA | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_sub-optimal_seed0.json |
| 56 | GFQ_impossible | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 0.714 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_impossible_seed0.json |
| 57 | GFQ_conflictual | 0 | 3/3 / 3/3 | non_agreement | partial_agreement | P32+P18 | 1.000 / 1.000 | 0.000 | 2.000 | 2 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_conflictual_seed0.json |
| 58 | GFQ_coalition | 0 | 3/3 / 3/3 | non_agreement | non_agreement | infeasible_vote | 1.000 / NA | NA | NA | 3 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_coalition_seed0.json |
| 59 | GFQ_unequal_bargaining | 0 | 3/3 / 3/3 | agreement | non_agreement | infeasible_vote | 1.000 / NA | NA | NA | 2 | 0 | Llama-3.1-8B-Instruct_v2_GFQ_unequal_bargaining_seed0.json |

## Results requiring attention

None. All expected result records are included.

## Data and provenance

- Matrix: `reproduction/crossmodels/experiments/matrix_fullconfigs_llama8b.json`
- Raw results directory: `crossmodels_20260927/results/llama8b_seed0`
- Initial-aggregation utilities are calculated with this checkout's `data/agents.json` and `data/projects.json`; final welfare/minimum utility are the recorded pilot metrics.
- Coverage checks recorded run settings and output structure. It does not independently verify the model weights or the prompts/project data used at execution time.
- SHA-256 hashes for the matrix and analysis data are stored in `coverage.json`.
