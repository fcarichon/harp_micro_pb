import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID_RE = re.compile(r"\bP\d+\b")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_pair(pair: Optional[List[str]]) -> Optional[tuple[str, str]]:
    if not isinstance(pair, list) or len(pair) != 2 or len(set(pair)) != 2:
        return None
    return tuple(sorted(pair))


def agreement_level(pairs: List[Optional[tuple[str, str]]]) -> str:
    if len(pairs) != 3 or any(pair is None for pair in pairs):
        return "invalid_vote"
    counts = Counter(pairs)
    if len(counts) == 1:
        return "agreement"
    if 2 in counts.values():
        return "partial_agreement"
    return "non_agreement"


def aggregate_pair_votes(pairs: List[Optional[tuple[str, str]]]) -> Optional[tuple[str, str]]:
    if len(pairs) != 3 or any(pair is None for pair in pairs):
        return None
    project_counts = Counter(pid for pair in pairs for pid in pair)
    majority = [pid for pid, count in project_counts.items() if count >= 2]
    if len(majority) < 2:
        return None
    return tuple(sorted(majority, key=lambda pid: (-project_counts[pid], pid))[:2])


def utility(pair: Optional[tuple[str, str]], profile: str, project_map: Dict[str, Any]) -> Optional[float]:
    if pair is None:
        return None
    return sum(float(project_map[pid]["utility"].get(profile, 0)) for pid in pair)


def best_utility(project_ids: List[str], profile: str, project_map: Dict[str, Any]) -> float:
    return max(utility(tuple(pair), profile, project_map) or 0.0 for pair in combinations(project_ids, 2))


def group_welfare(pair: tuple[str, str], utility_profiles: List[str], project_map: Dict[str, Any]) -> float:
    return mean(utility(pair, profile, project_map) or 0.0 for profile in utility_profiles)


def safe_mean(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(value) for value in values if value is not None]
    return mean(clean) if clean else None


def iter_generated_strings(result: Dict[str, Any]) -> Iterable[str]:
    for section in ("initial_votes", "final_votes"):
        for vote in result.get(section, {}).values():
            raw = vote.get("vote")
            if isinstance(raw, str):
                yield raw
    for discussion in result.get("pairwise_discussions", []):
        for message in discussion.get("messages", []):
            content = message.get("content")
            if isinstance(content, str):
                yield content


def analyze_run(path: Path, agents: Dict[str, Any], project_map: Dict[str, Any]) -> Dict[str, Any]:
    result = load_json(path)
    config = result["run_config"]
    profiles = config["profiles"]
    project_ids = config["project_ids"]

    initial_pairs = []
    final_pairs = []
    for i in range(3):
        agent_id = f"A{i + 1}"
        initial_pairs.append(canonical_pair(result["initial_votes"][agent_id]["parsed_vote"]["selected_projects"]))
        final_pairs.append(canonical_pair(result["final_votes"][agent_id]["parsed_vote"]["selected_projects"]))

    initial_self = [utility(initial_pairs[i], agents[profiles[i]]["utility_profile"], project_map) for i in range(3)]
    final_self = [utility(final_pairs[i], agents[profiles[i]]["utility_profile"], project_map) for i in range(3)]
    utility_profiles = [agents[profile]["utility_profile"] for profile in profiles]
    maxima = [best_utility(project_ids, utility_profiles[i], project_map) for i in range(3)]
    adherence = [final_self[i] / maxima[i] if final_self[i] is not None and maxima[i] else None for i in range(3)]
    self_utility_changes = [
        final_self[i] - initial_self[i]
        if final_self[i] is not None and initial_self[i] is not None
        else None
        for i in range(3)
    ]
    utility_spreads = []
    for profile in profiles:
        utility_profile = agents[profile]["utility_profile"]
        values = [float(project_map[pid]["utility"].get(utility_profile, 0)) for pid in project_ids]
        utility_spreads.append(max(values) - min(values))

    available = set(project_ids)
    referenced = [pid for text in iter_generated_strings(result) for pid in PROJECT_ID_RE.findall(text)]
    invalid_references = sorted({pid for pid in referenced if pid not in available})

    metrics = result.get("metrics") or {}
    final_allocation = result.get("orchestrator", {}).get("decision", {}).get("final_vote")
    initial_allocation = aggregate_pair_votes(initial_pairs)
    optimal_group_welfare = max(
        group_welfare(tuple(pair), utility_profiles, project_map)
        for pair in combinations(project_ids, 2)
    )
    initial_normalized_welfare = (
        group_welfare(initial_allocation, utility_profiles, project_map) / optimal_group_welfare
        if initial_allocation is not None and optimal_group_welfare
        else None
    )
    initial_min_utility = (
        min(utility(initial_allocation, profile, project_map) or 0.0 for profile in utility_profiles)
        if initial_allocation is not None
        else None
    )
    final_normalized_welfare = metrics.get("normalized_welfare")
    final_min_utility = metrics.get("min_utility")
    return {
        "file": path.name,
        "model": config["model"].split("/")[-1],
        "scenario": config.get("run_label", ""),
        "seed": config["seed"],
        "intention": config["intention"],
        "profiles": "+".join(profiles),
        "project_ids": "+".join(project_ids),
        "valid_initial_votes": sum(pair is not None for pair in initial_pairs),
        "valid_final_votes": sum(pair is not None for pair in final_pairs),
        "initial_agreement": agreement_level(initial_pairs),
        "final_agreement": agreement_level(final_pairs),
        "unique_initial_pairs": len({pair for pair in initial_pairs if pair is not None}),
        "unique_final_pairs": len({pair for pair in final_pairs if pair is not None}),
        "changed_agents": sum(initial_pairs[i] != final_pairs[i] for i in range(3)),
        "initial_allocation": "+".join(initial_allocation) if initial_allocation else "infeasible_vote",
        "initial_feasible_aggregation": initial_allocation is not None,
        "initial_normalized_welfare": initial_normalized_welfare,
        "final_allocation": "+".join(final_allocation) if isinstance(final_allocation, list) else str(final_allocation),
        "feasible_aggregation": isinstance(final_allocation, list),
        "normalized_welfare": final_normalized_welfare,
        "normalized_welfare_change": (
            final_normalized_welfare - initial_normalized_welfare
            if final_normalized_welfare is not None and initial_normalized_welfare is not None
            else None
        ),
        "initial_min_utility": initial_min_utility,
        "welfare": metrics.get("welfare"),
        "min_utility": final_min_utility,
        "min_utility_change": (
            final_min_utility - initial_min_utility
            if final_min_utility is not None and initial_min_utility is not None
            else None
        ),
        "mean_initial_self_utility": safe_mean(initial_self),
        "mean_final_self_utility": safe_mean(final_self),
        "mean_self_utility_change": safe_mean(self_utility_changes),
        "mean_final_profile_adherence": safe_mean(adherence),
        "non_discriminating_agents": sum(spread == 0 for spread in utility_spreads),
        "out_of_catalog_reference_count": sum(pid not in available for pid in referenced),
        "out_of_catalog_ids": "+".join(invalid_references),
    }


def format_mean(values: Iterable[Optional[float]]) -> str:
    clean = [float(value) for value in values if value is not None]
    return f"{mean(clean):.3f}" if clean else "NA"


def write_markdown(rows: List[Dict[str, Any]], path: Path) -> None:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["scenario"])].append(row)

    lines = [
        "# HARP experimental summary",
        "",
        "| Model | Scenario | n | Valid final votes | Initial exact agreement | Final exact agreement | Final pair match | Feasible aggregate | Normalized welfare | Welfare change | Min-utility change | Profile adherence | Utility change | Mean switches | Non-discriminating agents | Out-of-catalog refs |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (model, scenario), group in sorted(grouped.items()):
        n = len(group)
        valid = sum(row["valid_final_votes"] for row in group) / (3 * n)
        initial_agreement = sum(row["initial_agreement"] == "agreement" for row in group) / n
        final_agreement = sum(row["final_agreement"] == "agreement" for row in group) / n
        final_pair_match = sum(row["final_agreement"] in {"agreement", "partial_agreement"} for row in group) / n
        feasible = sum(bool(row["feasible_aggregation"]) for row in group) / n
        lines.append(
            f"| {model} | {scenario} | {n} | {valid:.1%} | {initial_agreement:.1%} | {final_agreement:.1%} | {final_pair_match:.1%} | {feasible:.1%} | "
            f"{format_mean(row['normalized_welfare'] for row in group)} | "
            f"{format_mean(row['normalized_welfare_change'] for row in group)} | "
            f"{format_mean(row['min_utility_change'] for row in group)} | "
            f"{format_mean(row['mean_final_profile_adherence'] for row in group)} | "
            f"{format_mean(row['mean_self_utility_change'] for row in group)} | "
            f"{format_mean(row['changed_agents'] for row in group)} | "
            f"{max(row['non_discriminating_agents'] for row in group)} | "
            f"{sum(row['out_of_catalog_reference_count'] for row in group)} |"
        )

    lines.extend([
        "",
        "## Individual runs",
        "",
        "| Model | Scenario | Seed | Intention | Initial | Final | Switches | Allocation | Norm. welfare | Min utility | Invalid refs |",
        "|---|---|---:|---:|---|---|---:|---|---:|---:|---:|",
    ])
    for row in sorted(rows, key=lambda item: (item["model"], item["scenario"], item["seed"])):
        norm = "NA" if row["normalized_welfare"] is None else f"{row['normalized_welfare']:.3f}"
        minimum = "NA" if row["min_utility"] is None else f"{row['min_utility']:.1f}"
        lines.append(
            f"| {row['model']} | {row['scenario']} | {row['seed']} | {row['intention']} | "
            f"{row['initial_agreement']} | {row['final_agreement']} | {row['changed_agents']} | "
            f"{row['final_allocation']} | {norm} | {minimum} | {row['out_of_catalog_reference_count']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    agents = load_json(ROOT / "data" / "agents.json")
    projects = load_json(ROOT / "data" / "projects.json")["projects"]
    project_map = {project["id"]: project for project in projects}
    paths = sorted(Path(args.results_dir).glob("*v2_*.json"))
    rows = [analyze_run(path, agents, project_map) for path in paths]
    if not rows:
        raise SystemExit("No v2 result JSON files found.")

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    markdown_path = Path(args.markdown)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(rows, markdown_path)
    print(f"Analyzed {len(rows)} runs")
    print(csv_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
