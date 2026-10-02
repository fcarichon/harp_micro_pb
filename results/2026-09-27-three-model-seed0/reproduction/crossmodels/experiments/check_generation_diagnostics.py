"""Read-only checks for twelve-call Gemma/Llama runs and their raw diagnostics.

This supplements check_full_results.py; a matching file count alone does not prove
matrix coverage. Truncation, empty replies, and response-parser errors are model
outcomes, not failed diagnostic checks. Non-result manifest files are ignored.
"""

import argparse
import json
from collections import Counter
from pathlib import Path


AGENTS = ("A1", "A2", "A3")
PAIRS = (("A1", "A2"), ("A1", "A3"), ("A2", "A3"))
IGNORE = {"batch_identity.json", "run_manifest.json"}


def expected_responses(result):
    """Return initial A1/A2/A3, six ordered critiques, and final A1/A2/A3."""
    responses = [(f"initial:{agent}", result["initial_votes"][agent]["vote"]) for agent in AGENTS]
    discussions = result["pairwise_discussions"]
    if not isinstance(discussions, list) or len(discussions) != 3:
        raise ValueError("Expected three ordered pairwise discussions")
    for pair, discussion in zip(PAIRS, discussions):
        if discussion["pair"] != list(pair):
            raise ValueError(f"Discussion order differs from expected pair {pair}")
        messages = discussion["messages"]
        if not isinstance(messages, list) or len(messages) != 2:
            raise ValueError(f"Expected two critiques for pair {pair}")
        for (speaker, receiver), message in zip((pair, pair[::-1]), messages):
            if (message["type"], message["speaker"], message["receiver"]) != ("critique", speaker, receiver):
                raise ValueError(f"Incorrect directed critique order for pair {pair}")
            responses.append((f"critique:{speaker}->{receiver}", message["content"]))
    responses.extend((f"final:{agent}", result["final_votes"][agent]["vote"]) for agent in AGENTS)
    if any(not isinstance(text, str) for _, text in responses):
        raise ValueError("Saved protocol responses must be strings")
    return responses


def inspect_run(result, model, revision):
    errors = []
    config = result["run_config"]
    runtime = result["model_runtime"]
    if not isinstance(config, dict) or not isinstance(runtime, dict):
        raise ValueError("run_config and model_runtime must be objects")
    for where, value in (("run_config.model", config.get("model")),
                         ("model_runtime.model_id", runtime.get("model_id"))):
        if value != model:
            errors.append(f"{where} differs from expected model")
    for key in ("requested_revision", "resolved_revision"):
        if runtime.get(key) != revision:
            errors.append(f"model_runtime.{key} differs from required pin")
    if config.get("intention") is not False or config.get("project_evaluations_skipped") is not True:
        errors.append("Twelve-call protocol requires intention=false and skipped project evaluations")
    for key in ("backend", "model_class", "tokenizer_class"):
        if not isinstance(runtime.get(key), str) or not runtime[key]:
            errors.append(f"Missing runtime {key}")
    if "device_map" not in runtime or not isinstance(runtime["device_map"], (dict, type(None))):
        errors.append("Missing or malformed runtime device_map")
    effective = runtime.get("effective_generation_config")
    overrides = runtime.get("explicit_generation_overrides")
    if not isinstance(effective, dict) or not isinstance(overrides, dict):
        raise ValueError("Missing effective generation configuration or explicit overrides")
    expected = expected_responses(result)
    records = result["generation_records"]
    if not isinstance(records, list) or len(records) != 12:
        raise ValueError("Expected exactly twelve generation records")
    observations = Counter(calls=12, reached_max_new_tokens=0, ended_with_eos=0,
                           response_parse_errors=0, empty_returned_text=0)
    flagged_calls = []
    for index, (record, (stage, text)) in enumerate(zip(records, expected)):
        if not isinstance(record, dict):
            raise ValueError(f"Generation record {index} is not an object")
        if type(record.get("call_index")) is not int or record["call_index"] != index:
            errors.append(f"Call {index}: incorrect call_index")
        if record.get("returned_text") != text:
            errors.append(f"Call {index} ({stage}): returned_text differs from saved protocol response")
        if not isinstance(record.get("raw_generated_text"), str):
            errors.append(f"Call {index}: missing raw_generated_text")
        for key in ("input_tokens", "generated_tokens"):
            if type(record.get(key)) is not int or record[key] < 0:
                errors.append(f"Call {index}: invalid {key}")
        for key in ("reached_max_new_tokens", "ended_with_eos"):
            if type(record.get(key)) is not bool:
                errors.append(f"Call {index}: invalid {key}")
            elif record[key]:
                observations[key] += 1
        if record.get("generation_overrides") != overrides:
            errors.append(f"Call {index}: generation overrides differ from recorded runtime")
        parse_error = record.get("response_parse_error")
        if "response_parse_error" not in record or not isinstance(parse_error, (str, type(None))):
            errors.append(f"Call {index}: missing or malformed response_parse_error")
        if parse_error:
            observations["response_parse_errors"] += 1
        if text == "":
            observations["empty_returned_text"] += 1
        if record.get("reached_max_new_tokens") or parse_error or text == "":
            flagged_calls.append({"call_index": index, "stage": stage,
                                  "reached_max_new_tokens": record.get("reached_max_new_tokens"),
                                  "response_parse_error": parse_error, "empty_returned_text": text == ""})
    settings = {key: runtime.get(key) for key in (
        "backend", "model_class", "tokenizer_class", "processor_class", "device_map",
        "dtype", "thinking", "tokenization", "response_handling")}
    settings["effective_generation_config"] = effective
    # These are inherited effective settings, not reconstructed original defaults.
    settings["inherited_generation_settings"] = {key: value for key, value in effective.items() if key not in overrides}
    return {"scenario": config.get("run_label"), "seed": config.get("seed"),
            "errors": errors, "observations": dict(observations),
            "flagged_calls": flagged_calls, "runtime": settings}


def check_directory(results_dir, model, revision, expected_count=60):
    directory = Path(results_dir).expanduser().resolve()
    rows, runtime_groups = [], {}
    observations = Counter(calls=0, reached_max_new_tokens=0, ended_with_eos=0,
                           response_parse_errors=0, empty_returned_text=0)
    identities = set()
    for path in sorted(directory.glob("*.json")):
        if path.name in IGNORE:
            continue
        row = {"file": path.name}
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
            info = inspect_run(result, model, revision)
            row.update({key: value for key, value in info.items() if key != "runtime"})
            identity = (info["scenario"], info["seed"])
            if identity in identities:
                row["errors"].append("Duplicate scenario/seed result")
            identities.add(identity)
            if not row["errors"]:
                observations.update(info["observations"])
                key = json.dumps(info["runtime"], sort_keys=True)
                runtime_groups.setdefault(key, {"runs": 0, **info["runtime"]})["runs"] += 1
        except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
            row["errors"] = [f"{type(exc).__name__}: {exc}"]
        row["status"] = "checked" if not row["errors"] else "diagnostic_mismatch"
        rows.append(row)
    checked = sum(row["status"] == "checked" for row in rows)
    complete = len(rows) == expected_count and checked == expected_count
    return {
        "results_dir": str(directory), "model": model, "required_revision": revision,
        "expected_runs": expected_count, "found_runs": len(rows), "checked_runs": checked,
        "diagnostic_mismatches": len(rows) - checked,
        "missing_by_count": max(0, expected_count - len(rows)),
        "status": "complete" if complete else "partial_or_mismatched",
        "diagnostics_complete": complete, "observations": dict(observations),
        "runtime_variants": list(runtime_groups.values()), "entries": rows,
        "scope": "Generation diagnostics only; run check_full_results.py for matrix coverage and result structure.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expected-count", type=int, default=60)
    args = parser.parse_args(argv)
    if args.expected_count < 1 or len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
        parser.error("Expected a positive run count and a full lowercase 40-character revision")
    report = check_directory(args.results_dir, args.model, args.revision, args.expected_count)
    print(json.dumps(report, separators=(",", ":")))
    return 0 if report["diagnostics_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
