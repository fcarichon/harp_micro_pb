from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "prompts"


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read().strip()


def build_agent_prompt(agent: Dict[str, Any]) -> str:
    """Build the system prompt for one stakeholder agent."""
    base = read_text(PROMPT_DIR / "base_agent_prompt.txt")
    profile_file = agent.get("profile_prompt_file")
    if not profile_file:
        raise ValueError(f"Missing profile_prompt_file for agent: {agent}")
    profile = read_text(PROMPT_DIR / profile_file)
    return f"{base}\n\n---\n\n{profile}"


def build_project_description(projects: List[Dict[str, Any]]) -> str:
    """Build a natural-language project list for agent prompts."""
    lines = ["Candidate projects:"]
    for p in projects:
        lines.append(
            f"\n{p['id']}: {p['name']}\n"
            f"Cost: ${p['cost']}M\n"
            f"Description: {p['description']}"
        )
    return "\n".join(lines)


def round_prompt(round_name: str, project_text: str, transcript_text: str = "") -> str:
    """Return the user prompt for a deliberation round."""
    if round_name == "preference_disclosure":
        instruction = (
            "Round 1: Preference disclosure.\n\n"
            "Please state your stakeholder group's main priorities and identify which projects appear most relevant to your group. "
            "Do not propose a final allocation yet."
        )
    elif round_name == "initial_proposal":
        instruction = (
            "Round 2: Initial proposal.\n\n"
            "Based on your stakeholder group's priorities and the project descriptions, propose an allocation of at most two projects under the $100M budget. "
            "Explain why your proposal serves your group and how it may affect other groups."
        )
    elif round_name == "negotiation_and_critique":
        instruction = (
            "Round 3: Negotiation and critique.\n\n"
            "You have seen the other agents' proposals. Please respond to them. Identify agreements, disagreements, possible compromises, "
            "and any concerns about fairness, feasibility, or value safeguards."
        )
    elif round_name == "revision":
        instruction = (
            "Round 4: Revised proposal.\n\n"
            "Based on the discussion so far, submit a revised allocation of at most two projects. You may keep your original proposal or revise it. "
            "Explain the compromise you are willing to accept."
        )
    else:
        raise ValueError(f"Unknown round name: {round_name}")

    if transcript_text:
        return f"{project_text}\n\nCurrent transcript:\n{transcript_text}\n\n{instruction}"
    return f"{project_text}\n\n{instruction}"


def build_moderator_prompt(project_text: str, transcript_text: str) -> str:
    moderator = read_text(PROMPT_DIR / "moderator_prompt.txt")
    return f"{moderator}\n\n{project_text}\n\nFull deliberation transcript:\n{transcript_text}"


def transcript_to_text(transcript: List[Dict[str, Any]]) -> str:
    lines = []
    for item in transcript:
        lines.append(f"[{item['round']}] {item['agent_id']}: {item['content']}")
    return "\n".join(lines)
