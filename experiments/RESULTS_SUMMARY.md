# Controlled experiment results

## Scope

- 22 controlled runs in total.
- 14 Qwen3-8B core runs across identical-profile, easy, medium, intention,
  hard-conflict, and original configurations.
- 4 Qwen3-8B discussion-prompt ablations.
- 4 Qwen3-30B-A3B-Instruct-2507 diagnostic runs.
- Temperature 0.7, top-p 0.9, thinking disabled, and recorded random seeds.

## Overall validity

- 66/66 final agent votes parsed as exactly two distinct in-catalog project IDs.
- 0 out-of-catalog project-ID references in the controlled outputs.
- 22/22 final project-level aggregations were feasible.
- Exact three-agent agreement occurred in 10/22 runs (45.5%).
- At least two agents shared an exact pair in 13/22 runs (59.1%).
- Mean normalized welfare was 0.943.
- 56/66 agents (84.8%) changed their initial vote.

## Main findings

1. **Agreement is not outcome quality.** In the 8B hard-conflict runs,
   normalized welfare was 1.00 while minimum stakeholder utility fell from 5
   to 3.
2. **Discussion can impose a negotiation tax.** In the 30B easy-bridge run,
   initial project-level aggregation produced the welfare-optimal P11+P12.
   After discussion, the result became P5+P11; normalized welfare fell from
   1.00 to 0.885 and minimum utility fell from 8 to 6.
3. **The intention step did not clearly help.** It reduced average switching
   from 2.0 to 1.5 agents in the medium scenario but did not create exact
   agreement and reduced mean normalized welfare from 0.935 to 0.913.
4. **Larger was not uniformly better.** On the four shared scenarios, 30B
   had more pair matches but lower mean normalized welfare than 8B (0.902 vs.
   0.946). The 30B hard-conflict result had normalized welfare 0.722.
5. **Consensus pressure changes the trade-off.** A revised discussion prompt
   that allows endorsement and `none` for concessions reduced easy-scenario
   agreement, but raised mean normalized welfare from 0.885 to 0.942, raised
   profile adherence, and reduced unnecessary switching.
6. **The original candidate set is not an equity-fidelity test.** P2, P4, P6,
   and P8 all have Egalitarian utility 1, so that agent cannot discriminate
   among any feasible pairs.

## Important interpretation limits

- The 8B cells use only two seeds and the 30B cells use one seed. These are
  diagnostic runs, not publication-level estimates.
- Structural validity does not guarantee semantic truthfulness. Agents can
  still introduce unsupported project benefits or implementation guarantees.
- Utility-preference profiles and value-safeguard profiles are not currently
  manipulated independently; the safeguard arrays in `agents.json` are not
  used to construct prompts.
- The prompt says that non-consensus means no projects are funded, while the
  orchestrator specification still applies majority aggregation. This
  institutional rule should be resolved before scaling experiments.

## Recommended next experiment stage

1. Review and merge the validity fixes.
2. Freeze one explicit decision rule and a metric vector covering validity,
   agreement, normalized welfare, minimum utility, profile regret, grounded
   truthfulness, and inference cost.
3. Calibrate easy, bridge, hard, and impossible-representation scenarios.
4. Separate utility-preference and value-safeguard treatments.
5. Run at least 10 seeds per frozen model/scenario cell with confidence
   intervals.
