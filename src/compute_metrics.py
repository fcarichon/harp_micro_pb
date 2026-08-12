from itertools import combinations
from typing import Dict, List, Any


def index_projects(projects: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {p["id"]: p for p in projects}


def compute_agent_utilities(selected_projects: List[str], projects: List[Dict[str, Any]], agent_profiles: List[str]) -> Dict[str, float]:
    project_map = index_projects(projects)
    utilities = {profile: 0.0 for profile in agent_profiles}
    for pid in selected_projects:
        p = project_map[pid]
        for profile in agent_profiles:
            utilities[profile] += float(p["utility"].get(profile, 0))
    return utilities


def compute_total_cost(selected_projects: List[str], projects: List[Dict[str, Any]]) -> float:
    project_map = index_projects(projects)
    return sum(float(project_map[pid]["cost"]) for pid in selected_projects)


def brute_force_optimal_welfare(projects: List[Dict[str, Any]], agent_profiles: List[str], budget: float) -> float:
    best = 0.0
    project_ids = [p["id"] for p in projects]
    project_map = index_projects(projects)

    for r in range(len(project_ids) + 1):
        for subset in combinations(project_ids, r):
            cost = sum(float(project_map[pid]["cost"]) for pid in subset)
            if cost <= budget:
                utilities = compute_agent_utilities(list(subset), projects, agent_profiles)
                welfare = sum(utilities.values()) / max(len(agent_profiles), 1)
                best = max(best, welfare)
    return best


def compute_metrics(selected_projects: List[str], projects: List[Dict[str, Any]], agent_profiles: List[str], budget: float) -> Dict[str, Any]:
    total_cost = compute_total_cost(selected_projects, projects)
    feasible = total_cost <= budget
    budget_violation = max(0.0, total_cost - budget)

    agent_utilities = compute_agent_utilities(selected_projects, projects, agent_profiles)
    welfare = sum(agent_utilities.values()) / max(len(agent_profiles), 1)
    min_utility = min(agent_utilities.values()) if agent_utilities else 0.0

    optimal_welfare = brute_force_optimal_welfare(projects, agent_profiles, budget)
    normalized_welfare = welfare / optimal_welfare if optimal_welfare > 0 else 0.0
    regret = optimal_welfare - welfare

    return {
        "selected_projects": selected_projects,
        "total_cost": total_cost,
        "budget": budget,
        "feasible": feasible,
        "budget_violation": budget_violation,
        "agent_utilities": agent_utilities,
        "welfare": welfare,
        "min_utility": min_utility,
        "optimal_welfare": optimal_welfare,
        "normalized_welfare": normalized_welfare,
        "regret": regret
    }
