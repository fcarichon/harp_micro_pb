# Controlled experiment matrix

The matrix separates implementation validity from substantive multi-agent behavior.
Every run uses three agents, four candidate projects, a two-project budget, structured
votes, deterministic aggregation, and a recorded random seed.

## Scenarios and hypotheses

| Scenario | Profiles | Projects | Diagnostic purpose | Expected behavior |
|---|---|---|---|---|
| `identical_ecology` | ecology x3 | P1, P6, P10, P13 | Same-preference control | Strong convergence toward P1+P10 |
| `identical_reputation` | reputation x3 | P2, P4, P8, P13 | Same-preference control with a top tie | Agreement should still be easy, although P4/P8 are tied |
| `easy_bridge` | ecology, family, egalitarian | P3, P5, P11, P12 | Different profiles with two high-welfare bridge projects | P11+P12 is the welfare-optimal compromise |
| `medium_bridge` | ecology, growth, reputation | P1, P2, P6, P13 | Shared support for P13 but disagreement on the second project | P13 should anchor a feasible compromise |
| `medium_bridge_intention` | same as `medium_bridge` | same | Ablation of the explicit intention step | Compare convergence with `medium_bridge` |
| `hard_conflict` | ecology, reputation, egalitarian | P1, P4, P5, P9 | Each profile has a different core interest | Agreement is possible but requires a visible concession |
| `original_low_equity` | ecology, reputation, egalitarian | P2, P4, P6, P8 | Reproduce Florian's original configuration | Egalitarian utility is 1 for every option, so this is not a valid profile-fidelity test for that agent |

The 8B matrix runs every scenario with seeds 0 and 1. The 30B matrix runs one seed
for the two most important controls plus the hard and original configurations.
Project-evaluation calls are skipped because they do not feed into deliberation; they
should be evaluated as a separate perception/calibration task.
