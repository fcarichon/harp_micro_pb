import json
import re
from typing import Dict, List, Any


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract a JSON object from text. Assumes the first {...} block is the intended object."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in final output.")
    return json.loads(match.group(0))


def parse_selected_projects(final_output: str, valid_project_ids: List[str]) -> List[str]:
    """Parse selected project IDs from moderator output."""
    obj = extract_json_object(final_output)
    selected = obj.get("selected_projects", [])
    if not isinstance(selected, list):
        raise ValueError("selected_projects must be a list.")

    normalized = []
    for item in selected:
        item_str = str(item).strip()
        pid_match = re.search(r"P\d+", item_str)
        if pid_match:
            pid = pid_match.group(0)
            if pid in valid_project_ids and pid not in normalized:
                normalized.append(pid)
    return normalized


def allocation_vector(selected_projects: List[str], project_order: List[str]) -> List[int]:
    """Convert selected project IDs to a binary allocation vector."""
    selected_set = set(selected_projects)
    return [1 if p in selected_set else 0 for p in project_order]


def parse_allocation(final_output: str, project_order: List[str]) -> Dict[str, Any]:
    selected = parse_selected_projects(final_output, project_order)
    return {
        "selected_projects": selected,
        "project_order": project_order,
        "allocation_vector": allocation_vector(selected, project_order)
    }
