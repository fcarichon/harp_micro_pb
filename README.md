# HARP-MicroPB Pilot

This folder contains a minimal executable pilot instance for the HARP project:
**Holistic Alignment in Multi-Agent Participatory Budgeting under Partial Preference Information**.

The goal is not to run the full benchmark yet. The goal is to verify that one fixed 3-agent / 6-project participatory-budgeting game can run end-to-end:

```text
game config -> agent prompts -> deliberation transcript -> final allocation -> allocation parser -> basic metrics
```

## Folder structure

```text
harp_micro_pb/
├── data/
│   ├── projects.json
│   └── pilot_001.json
├── prompts/
│   ├── base_agent_prompt.txt
│   ├── eco_profile.txt
│   ├── growth_profile.txt
│   ├── family_profile.txt
│   └── moderator_prompt.txt
├── outputs/
│   └── pilot_001_output.json  # created after running the pilot
├── src/
│   ├── run_pilot.py
│   ├── build_prompts.py
│   ├── parse_allocation.py
│   └── compute_metrics.py
└── README.md
```

## Pilot setup

- Agents: Eco, Growth, Family
- Projects: P1, P2, P3, P5, P6, P9
- Budget: $100M
- Cost: each project costs $50M
- Final allocation: at most two projects
- Protocol: fixed multi-round deliberation

## How to run

From the project root:

```bash
python src/run_pilot.py
```

This uses mock LLM outputs so that the pipeline can run without an API key. It will save the output to:

```text
outputs/pilot_001_output.json
```

## Next implementation step

Replace `mock_call_llm` in `src/run_pilot.py` with a real LLM API call. Keep the same output structure so that the parser and metrics code continue to work.

## First success criterion

The pilot is successful if it produces:

1. A full transcript.
2. A final allocation in JSON.
3. A binary allocation vector.
4. Basic metrics: feasibility, budget violation, welfare, minimum utility, normalized welfare, and regret.
5. A manual process-label template for truthfulness, transparency, argumentative fairness, anti-collusion, procedural compliance, and rationale-outcome mismatch.
