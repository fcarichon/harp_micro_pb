"""Check matrix coverage without treating a model's unsuccessful vote as a failed job.

Uses only the standard library; it does not load model weights or modify results.
Configuration defaults mirror run_matrix_entry.py and run_pilot.py. This checks
recorded metadata and structure, not the provenance of weights/prompts/project data.
"""

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

if __package__:
    from .run_matrix_entry import ROOT, build_command, load_entry
else:
    from run_matrix_entry import ROOT, build_command, load_entry


AGENTS = ("A1", "A2", "A3")
METRIC_FIELDS = {
    "selected_projects", "total_cost", "budget", "feasible", "budget_violation",
    "agent_utilities", "welfare", "min_utility", "optimal_welfare",
    "normalized_welfare", "regret",
}


def effective_config(entry):
    """Settings actually passed by the launcher, plus fixed pilot defaults."""
    return {
        "run_label": entry["scenario"],
        "model": entry["model"],
        "profiles": entry["profiles"],
        "project_ids": entry["project_ids"],
        "seed": entry["seed"],
        "temperature": entry.get("temperature", 0.7),
        "top_p": entry.get("top_p", 0.9),
        "max_new_tokens": entry.get("max_new_tokens", 512),
        "intention": bool(entry.get("intention", False)),
        "thinking": False,
        "discussion_prompt_file": entry.get("discussion_prompt_file") or "discussion_v3.txt",
        "project_evaluations_skipped": bool(entry.get("skip_project_evaluations", True)),
    }


def valid_pair(value, project_ids):
    return (
        isinstance(value, list) and len(value) == 2
        and all(isinstance(pid, str) and pid in project_ids for pid in value)
        and value[0] != value[1]
    )


def structural_errors(result, intention):
    errors = []
    for section in ("initial_votes", "final_votes"):
        votes = result.get(section)
        if not isinstance(votes, dict) or set(votes) != set(AGENTS):
            errors.append(f"{section}: expected exactly A1, A2, A3")
            continue
        for agent, vote in votes.items():
            if not isinstance(vote, dict) or not isinstance(vote.get("vote"), str):
                errors.append(f"{section}.{agent}: missing raw vote string")
                continue
            parsed = vote.get("parsed_vote")
            if (not isinstance(parsed, dict) or type(parsed.get("valid")) is not bool
                    or "selected_projects" not in parsed):
                errors.append(f"{section}.{agent}: missing parsed vote record")

    discussions = result.get("pairwise_discussions")
    expected_pairs = set(combinations(AGENTS, 2))
    actual_pairs = []
    if not isinstance(discussions, list) or len(discussions) != 3:
        errors.append("pairwise_discussions: expected three discussions")
    else:
        for index, discussion in enumerate(discussions):
            pair = discussion.get("pair") if isinstance(discussion, dict) else None
            if not valid_pair(pair, AGENTS):
                errors.append(f"pairwise_discussions[{index}]: invalid agent pair")
                continue
            actual_pairs.append(tuple(sorted(pair)))
            messages = discussion.get("messages")
            kinds = ("critique", "intention") if intention else ("critique",)
            expected_messages = Counter((kind, a, b) for kind in kinds
                                        for a, b in (pair, pair[::-1]))
            if not isinstance(messages, list):
                errors.append(f"pairwise_discussions[{index}]: missing messages")
                continue
            actual_messages = []
            for message in messages:
                if (not isinstance(message, dict)
                        or not isinstance(message.get("content"), str)
                        or any(not isinstance(message.get(key), str)
                               for key in ("type", "speaker", "receiver"))):
                    errors.append(f"pairwise_discussions[{index}]: malformed message")
                    continue
                actual_messages.append((message["type"], message["speaker"], message["receiver"]))
            if Counter(actual_messages) != expected_messages:
                errors.append(f"pairwise_discussions[{index}]: missing or duplicate directed messages")
        if set(actual_pairs) != expected_pairs or len(actual_pairs) != 3:
            errors.append("pairwise_discussions: missing or duplicate agent pairs")

    orchestrator = result.get("orchestrator")
    decision = orchestrator.get("decision") if isinstance(orchestrator, dict) else None
    if (not isinstance(orchestrator, dict) or not isinstance(orchestrator.get("method"), str)
            or not isinstance(decision, dict)
            or not {"match", "final_vote", "project_vote_counts"} <= decision.keys()):
        errors.append("orchestrator: missing decision record")
    elif isinstance(decision["final_vote"], list):
        metrics = result.get("metrics")
        if not isinstance(metrics, dict) or not METRIC_FIELDS <= metrics.keys():
            errors.append("metrics: missing computed metrics for aggregate allocation")
    elif decision["final_vote"] == "infeasible_vote":
        if "metrics" not in result or result["metrics"] is not None:
            errors.append("metrics: expected explicit null for infeasible aggregation")
    else:
        errors.append("orchestrator: unknown final_vote representation")
    return errors


def scientific_outcome(result, project_ids):
    summary = {}
    for section in ("initial_votes", "final_votes"):
        pairs = []
        for agent in AGENTS:
            parsed = result[section][agent]["parsed_vote"]
            selected = parsed["selected_projects"]
            pairs.append(tuple(sorted(selected)) if parsed["valid"] and
                         valid_pair(selected, project_ids) else None)
        summary[f"valid_{section}"] = sum(pair is not None for pair in pairs)
        counts = Counter(pairs)
        summary[f"{section.removesuffix('_votes')}_agreement"] = (
            "invalid_vote" if None in pairs else "agreement" if len(counts) == 1
            else "partial_agreement" if 2 in counts.values() else "non_agreement"
        )
    decision = result["orchestrator"]["decision"]
    summary["feasible_aggregate_pair"] = valid_pair(decision["final_vote"], project_ids)
    summary["orchestrator_match"] = decision["match"]
    return summary


def reject_nonfinite(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def check_results(matrix_path, results_dir):
    matrix_path = Path(matrix_path).expanduser()
    if not matrix_path.is_absolute():
        matrix_path = ROOT / matrix_path
    results_dir = Path(results_dir).expanduser().resolve()
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)
    if not isinstance(matrix, list) or not matrix:
        raise ValueError("The matrix must be a non-empty JSON list.")
    entries = [load_entry(matrix_path, index) for index in range(len(matrix))]
    paths = [build_command(entry, results_dir)[1] for entry in entries]
    if len(set(paths)) != len(paths):
        raise ValueError("Multiple matrix entries map to the same output filename.")

    rows = []
    for index, (entry, path) in enumerate(zip(entries, paths)):
        row = {"index": index, "scenario": entry["scenario"], "file": path.name}
        rows.append(row)
        if not path.exists():
            row["status"] = "missing"
            continue
        try:
            result = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)
        except (OSError, ValueError) as exc:
            row.update(status="malformed", errors=[str(exc)])
            continue
        if not isinstance(result, dict) or not isinstance(result.get("run_config"), dict):
            row.update(status="malformed", errors=["Missing run_config object"])
            continue
        expected = effective_config(entry)
        actual = result["run_config"]
        mismatch = {key: {"expected": value, "actual": actual.get(key)}
                    for key, value in expected.items()
                    if key not in actual or actual[key] != value
                    or (type(value) is bool and type(actual[key]) is not bool)}
        errors = structural_errors(result, expected["intention"])
        if errors:
            row.update(status="malformed", errors=errors)
        elif mismatch:
            row["status"] = "config_mismatch"
        else:
            row.update(status="completed", scientific=scientific_outcome(result, expected["project_ids"]))
        if mismatch:
            row["config_mismatch"] = mismatch

    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("completed", "missing", "malformed", "config_mismatch")}
    science = [row["scientific"] for row in rows if row["status"] == "completed"]
    return {
        "matrix": str(matrix_path.resolve()), "results_dir": str(results_dir),
        "expected": len(entries), "counts": counts,
        "coverage_complete": counts["completed"] == len(entries),
        "scientific_summary": {
            "runs": len(science),
            "valid_initial_votes": sum(row["valid_initial_votes"] for row in science),
            "valid_final_votes": sum(row["valid_final_votes"] for row in science),
            "total_votes_per_stage": 3 * len(science),
            "final_agreement": dict(Counter(row["final_agreement"] for row in science)),
            "feasible_aggregate_pairs": sum(row["feasible_aggregate_pair"] for row in science),
        },
        "entries": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = check_results(args.matrix, args.results_dir)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, separators=(",", ":")))
        return 2
    print(json.dumps(report, separators=(",", ":")))
    return 0 if report["coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
