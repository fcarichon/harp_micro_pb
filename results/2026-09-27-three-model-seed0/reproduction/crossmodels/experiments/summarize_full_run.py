"""Write coverage, full per-run CSV, and a scenario-grouped experimental report."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

if __package__:
    from .analyze_results import analyze_run, load_json
    from .check_full_results import ROOT, check_results
else:
    from analyze_results import analyze_run, load_json
    from check_full_results import ROOT, check_results


def scenario_type(label):
    return label.split("_", 1)[1] if "_" in label else label


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def summarize_group(rows):
    feasible = [row for row in rows if row["feasible_aggregation"]]
    welfare = [row["normalized_welfare"] for row in feasible if numeric(row["normalized_welfare"])]
    minimum = [row["min_utility"] for row in feasible if numeric(row["min_utility"])]
    paired = [row["normalized_welfare"] - row["initial_normalized_welfare"]
              for row in feasible if row["initial_feasible_aggregation"]
              and numeric(row["normalized_welfare"]) and numeric(row["initial_normalized_welfare"])]
    return {
        "runs": len(rows), "votes_per_stage": 3 * len(rows),
        "valid_initial_votes": sum(row["valid_initial_votes"] for row in rows),
        "valid_final_votes": sum(row["valid_final_votes"] for row in rows),
        "initial_exact_agreement": sum(row["initial_agreement"] == "agreement" for row in rows),
        "final_exact_agreement": sum(row["final_agreement"] == "agreement" for row in rows),
        "initial_feasible_aggregates": sum(row["initial_feasible_aggregation"] for row in rows),
        "final_feasible_aggregates": len(feasible),
        "final_agreement_categories": dict(Counter(row["final_agreement"] for row in rows)),
        "normalized_welfare": {"mean": mean(welfare) if welfare else None, "n": len(welfare)},
        "min_utility": {"mean": mean(minimum) if minimum else None, "n": len(minimum)},
        "paired_welfare_change": {"mean": mean(paired) if paired else None, "n": len(paired)},
        "out_of_catalog_references": sum(row["out_of_catalog_reference_count"] for row in rows),
    }


def ratio(numerator, denominator):
    return f"{numerator}/{denominator} ({numerator / denominator:.1%})" if denominator else "0/0 (NA)"


def conditional_mean(stat):
    return f"{stat['mean']:.3f} (n={stat['n']})" if stat["n"] else "NA (n=0)"


def number(value):
    return f"{value:.3f}" if numeric(value) else "NA"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(coverage, rows, matrix, analysis_errors):
    counts = coverage["counts"]
    total = summarize_group(rows)
    complete = coverage["coverage_complete"] and not analysis_errors
    expected_groups = Counter((Path(entry["model"]).name, scenario_type(entry["scenario"]))
                              for entry in matrix)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["scenario_type"])].append(row)
    seeds = sorted({entry["seed"] for entry in matrix})
    lines = [
        "# HARP full-configuration experiment results", "",
        f"Status: **{'COMPLETE' if complete else 'PARTIAL'}** — "
        f"{counts['completed']}/{coverage['expected']} expected results are structurally complete "
        f"and configuration-matched; {len(rows)}/{coverage['expected']} are included in this analysis.", "",
        f"Generated (UTC): {coverage['report_analysis']['generated_utc']}", "",
        "## Coverage", "",
        "| Category | Matrix entries |", "|---|---:|",
        f"| Expected | {coverage['expected']} |",
        *[f"| {key} | {value} |" for key, value in counts.items()],
        f"| Analysis errors among completed records | {len(analysis_errors)} |", "",
        "Only completed records whose recorded settings match the requested matrix are analyzed. "
        "Model vote failures and non-agreement remain results and are included in the denominators. "
        "Missing, malformed, or mismatched files are excluded.", "",
        "## Experimental scope and interpretation", "",
        f"Requested seed values: {', '.join(map(str, seeds))}. "
        "Each matrix entry represents one run of a particular profile/project configuration.", "",
        ("This is one seed-0 run per configuration. " if seeds == [0] else "")
        + "Scenario groups pool different profile/project configurations. They are not independent "
        "seed repetitions of the same experiment; these descriptive averages do not establish "
        "sampling uncertainty or statistical significance.", "",
        "Exact agreement means all three agents chose the same project pair. A feasible aggregate "
        "can also result from disagreement under the deterministic majority rule. "
        "The labels `optimal`, `impossible`, and similar names identify the configured scenarios, "
        "not a correctness judgment about an observed response.", "",
        "Normalized welfare and minimum utility are averaged only over runs with a feasible final "
        "aggregate and an available numeric metric. Every mean displays its own denominator n. "
        "Paired welfare change is final minus initial normalized welfare, averaged only over runs "
        "with feasible aggregates and numeric welfare at both stages. Infeasible runs are not assigned "
        "zero welfare. `NA` means the required observations are absent.", "",
        "## Overall results", "",
        "| Measure | Count / denominator or conditional mean |", "|---|---:|",
        f"| Valid initial votes | {ratio(total['valid_initial_votes'], total['votes_per_stage'])} |",
        f"| Valid final votes | {ratio(total['valid_final_votes'], total['votes_per_stage'])} |",
        f"| Initial exact agreement | {ratio(total['initial_exact_agreement'], total['runs'])} |",
        f"| Final exact agreement | {ratio(total['final_exact_agreement'], total['runs'])} |",
        f"| Feasible initial aggregates | {ratio(total['initial_feasible_aggregates'], total['runs'])} |",
        f"| Feasible final aggregates | {ratio(total['final_feasible_aggregates'], total['runs'])} |",
        f"| Final normalized welfare, conditional | {conditional_mean(total['normalized_welfare'])} |",
        f"| Final minimum utility, conditional | {conditional_mean(total['min_utility'])} |",
        f"| Paired normalized-welfare change | {conditional_mean(total['paired_welfare_change'])} |",
        f"| Out-of-catalog project mentions | {total['out_of_catalog_references']} occurrences |", "",
        "Final agreement categories among included runs: "
        + (", ".join(f"{key}: {value}/{len(rows)}" for key, value in
                     sorted(total["final_agreement_categories"].items())) or "none") + ".", "",
        "## Results by scenario type", "",
        "`n / expected` is the number of analyzed configurations versus the requested matrix entries "
        "in that group. Vote denominators are 3 × n; agreement and feasibility denominators are n.", "",
        "| Model | Scenario type | n / expected | Valid initial votes | Valid final votes | "
        "Initial exact agreement | Final exact agreement | Feasible final aggregates | "
        "Final norm. welfare (conditional) | Min utility (conditional) | Paired welfare change |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, expected in sorted(expected_groups.items()):
        stats = summarize_group(groups[key])
        values = [key[0], key[1], f"{stats['runs']}/{expected}",
                  ratio(stats["valid_initial_votes"], stats["votes_per_stage"]),
                  ratio(stats["valid_final_votes"], stats["votes_per_stage"]),
                  ratio(stats["initial_exact_agreement"], stats["runs"]),
                  ratio(stats["final_exact_agreement"], stats["runs"]),
                  ratio(stats["final_feasible_aggregates"], stats["runs"]),
                  conditional_mean(stats["normalized_welfare"]),
                  conditional_mean(stats["min_utility"]),
                  conditional_mean(stats["paired_welfare_change"])]
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines.extend([
        "", "## Per-run results", "",
        "Full analysis fields are in `results.csv`; raw outputs remain in the results directory. "
        "`Switches` counts changed parsed selections, including transitions to or from an invalid vote.", "",
        "| Index | Scenario | Seed | Valid votes initial / final | Initial agreement | Final agreement | "
        "Final allocation | Norm. welfare initial / final | Paired change | Final min utility | "
        "Switches | Out-of-catalog mentions | Raw file |",
        "|---:|---|---:|---|---|---|---|---|---:|---:|---:|---:|---|",
    ])
    for row in rows:
        values = [row["matrix_index"], row["scenario"], row["seed"],
                  f"{row['valid_initial_votes']}/3 / {row['valid_final_votes']}/3",
                  row["initial_agreement"], row["final_agreement"], row["final_allocation"],
                  f"{number(row['initial_normalized_welfare'])} / {number(row['normalized_welfare'])}",
                  number(row["normalized_welfare_change"]), number(row["min_utility"]),
                  row["changed_agents"], row["out_of_catalog_reference_count"], row["file"]]
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines.extend(["", "## Results requiring attention", ""])
    incomplete = [entry for entry in coverage["entries"] if entry["status"] != "completed"]
    if not incomplete and not analysis_errors:
        lines.append("None. All expected result records are included.")
    else:
        for entry in incomplete:
            detail = "; ".join(entry.get("errors", []))
            if entry.get("config_mismatch"):
                detail += ("; " if detail else "") + "mismatched fields: " + ", ".join(entry["config_mismatch"])
            lines.append(f"- Index {entry['index']} `{entry['scenario']}`: {entry['status']} "
                         f"(`{entry['file']}`)" + (f" — {detail}" if detail else ""))
        for error in analysis_errors:
            lines.append(f"- Index {error['index']} `{error['scenario']}`: analysis error — {error['error']}")
    lines.extend([
        "", "## Data and provenance", "",
        f"- Matrix: `{coverage['matrix']}`",
        f"- Raw results directory: `{coverage['results_dir']}`",
        "- Initial-aggregation utilities are calculated with this checkout's `data/agents.json` "
        "and `data/projects.json`; final welfare/minimum utility are the recorded pilot metrics.",
        "- Coverage checks recorded run settings and output structure. It does not independently "
        "verify the model weights or the prompts/project data used at execution time.",
        "- SHA-256 hashes for the matrix and analysis data are stored in `coverage.json`.", "",
    ])
    return "\n".join(lines)


def write_report(matrix_path, results_dir, report_dir):
    coverage = check_results(matrix_path, results_dir)
    agents_path = ROOT / "data" / "agents.json"
    projects_path = ROOT / "data" / "projects.json"
    agents = load_json(agents_path)
    project_map = {project["id"]: project for project in load_json(projects_path)["projects"]}
    matrix = load_json(Path(coverage["matrix"]))
    rows, errors = [], []
    for entry in coverage["entries"]:
        if entry["status"] != "completed":
            continue
        try:
            row = analyze_run(Path(coverage["results_dir"]) / entry["file"], agents, project_map)
            # The coverage checker also validates catalog membership and parsed validity.
            scientific = entry["scientific"]
            for key in ("valid_initial_votes", "valid_final_votes", "initial_agreement", "final_agreement"):
                row[key] = scientific[key]
            row["feasible_aggregation"] = scientific["feasible_aggregate_pair"]
            row["matrix_index"] = entry["index"]
            row["scenario_type"] = scenario_type(row["scenario"])
            rows.append(row)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            errors.append({"index": entry["index"], "scenario": entry["scenario"], "error": str(exc)})
    coverage["report_analysis"] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "included_runs": len(rows), "errors": errors, "overall": summarize_group(rows),
        "input_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (Path(coverage["matrix"]), agents_path, projects_path)},
    }
    destination = Path(report_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    with (destination / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        # Empty reports still contain a usable header; populated reports preserve every analysis field.
        fieldnames = list(rows[0]) if rows else ["file", "model", "scenario", "seed", "matrix_index", "scenario_type"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (destination / "SUMMARY.md").write_text(render_markdown(coverage, rows, matrix, errors), encoding="utf-8")
    return coverage


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--report-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        coverage = write_report(args.matrix, args.results_dir, args.report_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps({"report_dir": str(args.report_dir.expanduser().resolve()),
                      "counts": coverage["counts"], "included_runs": coverage["report_analysis"]["included_runs"],
                      "analysis_errors": len(coverage["report_analysis"]["errors"])}))
    return 0 if coverage["coverage_complete"] and not coverage["report_analysis"]["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
