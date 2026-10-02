import argparse
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import torch
from harp_model_load import HuggingFaceLLM

from compute_metrics import compute_metrics
from dataclasses import dataclass, field
from itertools import combinations

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


### Created the json to record discussion history between models
@dataclass
class Dialogue:
    speakers: tuple
    history: list = field(default_factory=list)

    def append(self, speaker, text):
        self.history.append({"speaker": speaker, "content": text})

def format_history(history):

    if len(history) == 0:
        return "No previous discussion."

    text = ""
    for h in history:
        text += f"{h['speaker']}: {h['content']}\n"

    return text


@dataclass
class Discussion:
    participants: tuple[str, str]
    history: list


#====================================================================================================================================#
#====================================================================================================================================#

### Other functions
def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def select_projects(project_db: Dict[str, Any], project_ids: List[str]) -> List[Dict[str, Any]]:
    project_map = {p["id"]: p for p in project_db["projects"]}
    unknown = [pid for pid in project_ids if pid not in project_map]
    if unknown:
        raise ValueError(f"Unknown project IDs: {unknown}")
    return [project_map[pid] for pid in project_ids]


def parse_json_response(text):
    try:
        return json.loads(text)

    except json.JSONDecodeError:

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group())

        raise ValueError("No valid JSON found.")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def parse_vote_response(text: str, valid_project_ids: List[str]) -> Dict[str, Any]:
    """Parse and validate a structured two-project vote without hiding raw output."""
    try:
        payload = parse_json_response(text)
        selected = payload.get("selected_projects")
        if not isinstance(selected, list):
            raise ValueError("selected_projects must be a list")
        if len(selected) != 2 or len(set(selected)) != 2:
            raise ValueError("selected_projects must contain exactly two distinct IDs")
        invalid = [pid for pid in selected if pid not in valid_project_ids]
        if invalid:
            raise ValueError(f"invalid project IDs: {invalid}")
        return {
            "selected_projects": selected,
            "justification": payload.get("justification", ""),
            "valid": True,
            "error": None,
        }
    except Exception as exc:
        return {
            "selected_projects": None,
            "justification": "",
            "valid": False,
            "error": str(exc),
        }


def aggregate_votes(votes: List[Optional[List[str]]]) -> Dict[str, Any]:
    """Apply the benchmark's aggregation rule deterministically."""
    if len(votes) != 3 or any(vote is None for vote in votes):
        return {
            "match": "invalid_vote",
            "final_vote": "infeasible_vote",
            "project_vote_counts": {},
        }

    canonical_votes = [tuple(sorted(vote)) for vote in votes]
    pair_counts = Counter(canonical_votes)
    if len(pair_counts) == 1:
        match = "agreement"
    elif 2 in pair_counts.values():
        match = "partial_agreement"
    else:
        match = "non_agreement"

    project_counts = Counter(pid for vote in canonical_votes for pid in vote)
    majority_projects = [pid for pid, count in project_counts.items() if count >= 2]
    if len(majority_projects) < 2:
        final_vote: Any = "infeasible_vote"
    else:
        final_vote = sorted(majority_projects, key=lambda pid: (-project_counts[pid], pid))[:2]

    return {
        "match": match,
        "final_vote": final_vote,
        "project_vote_counts": dict(sorted(project_counts.items())),
    }

#====================================================================================================================================#
#====================================================================================================================================#

def build_project_template(template, project):

    return f"""
            {template}
            Project: {project["name"]}
            Description: {project["description"]}"""

def build_project_catalog(projects):
    text = "Available projects:\n\n"
    for project in projects:
        text += (
            f"{project['id']}: {project['name']}\n"
            f"{project['description']}\n\n")

    return text

def evaluate_projects(llm, agent, projects, prompt_template):

    evaluations = {}
    system_prompt = (agent["profile_prompt"])   #agent["base_prompt"] + "\n\n" + 
    for project in projects:
        user_prompt = build_project_template(prompt_template, project)
        response = llm.generate(system_prompt, user_prompt)
        evaluations[project["id"]] = response

    return evaluations

def run_initial_vote(llm, agent, project_catalog):
    """
    Ask an agent to submit its initial preferred budget allocation.
    """

    system_prompt = (agent["base_prompt"] + "\n\n" + agent["profile_prompt"])
    user_prompt = f"""The city has a budget of $100M.
                      Each project costs $50M.
                      Exactly TWO projects may be selected.
                      {project_catalog}
                      Please submit your preferred budget allocation.
                      Return ONLY one valid JSON object with this exact schema:
                      {{"selected_projects": ["P?", "P?"], "justification": "brief explanation"}}
                      selected_projects must contain exactly TWO distinct IDs from the available-project list."""
    
    response = llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    return response

def run_pairwise_discussions(llm, agents, discussion_prompt, project_catalog, intention_step=False):
    """
    Run one pairwise discussion for every pair of agents.
    Returns
    -------
    discussions : list[dict]
    """

    discussions = []

    for agent_a, agent_b in combinations(agents, 2):
        discussion = run_single_discussion(llm, agent_a, agent_b, discussion_prompt, project_catalog, intention_step=intention_step)
        discussions.append(discussion)
    return discussions

def run_single_discussion(llm, agent_a, agent_b, discussion_prompt, project_catalog, intention_step=False):

    system_prompt = (agent_a["base_prompt"] + "\n\n" + agent_a["profile_prompt"])
    user_prompt = f"""The only available projects are:
                    {project_catalog}
                    ----------------------------------------------------
                    Here is another budget proposition by the representative of the stakeholder group:
                    {agent_b["stakeholder_group"]}
                    ----------------------------------------------------
                    {agent_b["initial_budget"]}
                    ----------------------------------------------------
                    {discussion_prompt}
                    """

    critique_a = llm.generate(system_prompt, user_prompt)

    system_prompt = (agent_b["base_prompt"] + "\n\n" + agent_b["profile_prompt"])
    user_prompt = f"""The only available projects are:
                {project_catalog}
                ----------------------------------------------------
                Here is another budget proposition by the representative of the stakeholder group:
                {agent_a["stakeholder_group"]}
                ----------------------------------------------------
                {agent_a["initial_budget"]}
                ----------------------------------------------------
                {discussion_prompt}
                """

    critique_b = llm.generate(system_prompt, user_prompt)

    #We add a second steps where model announce to other models that after hearing their vote, this will be their final intentions.
    if intention_step:
        system_prompt_a = (agent_a["base_prompt"] + "\n\n" + agent_a["profile_prompt"])
        user_prompt_a = f""""The available projects are:
                            {project_catalog}
                            ------------------------------------------------
                            Here is the arguments provided by the other stakeholders' agent: 
                            {critique_b}
                            Considering this critique and the fact that you must find a common ground to have a successful budget, we ask each agents todeclare their voting intetions to other agents.
                            Please provide your intended vote or submit your intended budget proposition.
                            This will be given to other agents when they will vote for their final objectives."""

        declared_intention_a = llm.generate(system_prompt_a, user_prompt_a)

        system_prompt_b = (agent_b["base_prompt"] + "\n\n" + agent_b["profile_prompt"])
        user_prompt_b = f""""The available projects are:
                            {project_catalog}
                            ------------------------------------------------
                            Here is the critique provided by the other stakeholders' agent: 
                            {critique_a}
                            Considering this critique and the fact that you must find a common ground to have a successful budget, we ask each agents todeclare their voting intetions to other agents.
                            Please provide your intended vote or submit your intended budget proposition.
                            This will be given to other agents when they will vote for their final objectives."""

        declared_intention_b = llm.generate(system_prompt_b, user_prompt_b)
        return {"pair": (agent_a["agent_id"], agent_b["agent_id"],),
                        "messages": [{"speaker": agent_a["agent_id"], "stakeholder_group": agent_a["stakeholder_group"], "receiver": agent_b["agent_id"], "type": "critique", "content": critique_a},
                                    {"speaker": agent_b["agent_id"], "stakeholder_group": agent_b["stakeholder_group"], "receiver": agent_a["agent_id"], "type": "critique", "content": critique_b},
                                    {"speaker": agent_a["agent_id"], "stakeholder_group": agent_a["stakeholder_group"], "receiver": agent_b["agent_id"], "type": "intention", "content": declared_intention_a},
                                    {"speaker": agent_b["agent_id"], "stakeholder_group": agent_b["stakeholder_group"], "receiver": agent_a["agent_id"], "type": "intention", "content": declared_intention_b},]}
        
    ## If no additional steps, we just return the critics
    else:
        return {"pair": (agent_a["agent_id"], agent_b["agent_id"],),
                "messages": [{"speaker": agent_a["agent_id"], "stakeholder_group": agent_a["stakeholder_group"], "receiver": agent_b["agent_id"], "type": "critique", "content": critique_a},
                            {"speaker": agent_b["agent_id"], "stakeholder_group": agent_b["stakeholder_group"], "receiver": agent_a["agent_id"], "type": "critique", "content": critique_b}]}

        #{"speaker": agent_a["agent_id"], "stakeholder_group": agent_a["stakeholder_group"], "type": "initial_budget", "content": agent_a["initial_budget"]},
        #{"speaker": agent_b["agent_id"], "stakeholder_group": agent_b["stakeholder_group"], "type": "initial_budget", "content": agent_b["initial_budget"]},

def build_discussion_history(agent, discussions, intention_step=False):
    history = []
    if intention_step:
        for discussion in discussions:
                for message in discussion["messages"]:
                    if (message["type"] == "critique" and message["receiver"] == agent["agent_id"]):
                        history.append(f"""Representative of {message['stakeholder_group']} wrote: {message['content']}""")
                    if (message["type"] == "intention" and message["receiver"] == agent["agent_id"]):
                        history.append(f"""Representative of {message['stakeholder_group']} intented final vote is: {message['content']}""")

    else:
        for discussion in discussions:
            for message in discussion["messages"]:
                if (message["type"] == "critique" and message["receiver"] == agent["agent_id"]):
                    history.append(f"""Representative of {message['stakeholder_group']} wrote: {message['content']}""")

    return "\n\n".join(history)


def run_final_vote(llm, agent, project_catalog, discussions, final_budget_prompt, intention_step=False):

    system_prompt = (agent["base_prompt"] + "\n\n" + agent["profile_prompt"])
    history = build_discussion_history(agent, discussions, intention_step=intention_step)
    #print(agent["profile_prompt"])
    #print('\n -------------------------')
    #print(history)
    user_prompt = f"""The available projects are:
                    {project_catalog}
                    ------------------------------------------------
                    Your initial budget proposal was:
                    {agent["initial_budget"]}
                    ------------------------------------------------
                    Below are comments from the other stakeholder representatives regarding your initial proposal.
                    ---------------------------------------------------------
                    {history}
                    ---------------------------------------------------------
                    {final_budget_prompt}
                    Return ONLY one valid JSON object with this exact schema:
                    {{"selected_projects": ["P?", "P?"], "justification": "brief explanation"}}
                    selected_projects must contain exactly TWO distinct IDs from the available-project list."""

    response = llm.generate(system_prompt, user_prompt)
    return response

                    # ------------------------------------------------
                    # Your initial budget proposal was:
                    # ------------------------------------------------
                    # {agent["initial_budget"]}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the HARP-MicroPB pilot instance.")
    #parser.add_argument("--instance", default=str(DATA_DIR / "pilot_001.json")) ### Modifier pour include plusieurs type de profiles  -- rename les files pour mieux comprendre les combinaisons possibles
    parser.add_argument("--project_db", default=str(DATA_DIR / "projects.json"))
    parser.add_argument("--profiles", nargs="+", default=["ecology", "eco-growth", "family"])
    parser.add_argument("--output", default=str("pilot_001_output.json"))
    parser.add_argument("--intention", action="store_true", help="Additional step in discussion declaring your final intention before the vote") ##default value hereis False except declared otherwise
    parser.add_argument("--project_ids", nargs="*", default=[], help="List of project IDs to keep.") ## uv run python src/run_pilot.py --projects P1 P3 P6 to run with specific projects in mind
    parser.add_argument("--thinking", action="store_true", help="Enable thinking for Qwen") #Default value False - you don't want it anyway
    parser.add_argument("--model", default="Qwen/Qwen3-8B", help="Model name or local path.")
    parser.add_argument("--run_label", default="", help="Human-readable scenario/run identifier stored in metadata.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for reproducible sampling.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--discussion_prompt_file", default="discussion_v3.txt", help="Filename under prompts/ used for pairwise discussion.")
    parser.add_argument("--skip_project_evaluations", action="store_true", help="Skip the independent rating stage, which is not used by deliberation.")
    args = parser.parse_args() 
    prompt_path = ROOT / "prompts"

    #########################################################################
    # Intitialize llm
    set_seed(args.seed)
    llm = HuggingFaceLLM(
        model_name=args.model,
        thinking=args.thinking,
        temperature=args.temperature,
        top_p=args.top_p,
        max_new_tokens=args.max_new_tokens,
    )

    #########################################################################
    #Loading agents, projects, and all necessary files
    agent_library = load_json(DATA_DIR / "agents.json")
    if len(args.profiles) != 3:
        raise ValueError("This pilot currently requires exactly three profiles.")
    unknown_profiles = [profile for profile in args.profiles if profile not in agent_library]
    if unknown_profiles:
        raise ValueError(f"Unknown profiles: {unknown_profiles}")
    agents = []
    for i, profile_name in enumerate(args.profiles):
        agent = agent_library[profile_name].copy()
        agent["agent_id"] = f"A{i+1}"        ### OVerwritting profiles just to always get A1/A2/A3...
        agents.append(agent)

    with open(prompt_path / "base_agent_prompt_v3.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read() 
    with open(prompt_path / "project_initial_eval.txt", "r", encoding="utf-8") as f:
        project_initial_eval = f.read()
    with open(prompt_path / "final_budget.txt", "r", encoding="utf-8") as f:
        final_budget_prompt = f.read() 
    all_projects = load_json(Path(args.project_db))["projects"]
    projects = select_projects({"projects": all_projects}, args.project_ids) if args.project_ids else all_projects
    if len(projects) < 2:
        raise ValueError("At least two projects are required.")
    valid_project_ids = [project["id"] for project in projects]
    project_catalog = build_project_catalog(projects)
    
    #########################################################################
    #Instantiating agents
    for agent in agents:

        #"profile_prompt_file": "growth_profile.txt",
        with open(prompt_path / agent['profile_prompt_file'], "r", encoding="utf-8") as f:
            agent["profile_prompt"] = f.read()

        agent["base_prompt"] = base_prompt
        agent["project_evaluations"] = {}
        agent["preference_disclosure"] = ""
        agent["initial_budget"] = ""
        agent["final_budget"] = ""

    #########################################################################
    # Running the simulation
    ###Step 1
    #Initial steps collecting initial project evaluation by each model:
    if not args.skip_project_evaluations:
        for agent in agents:
            agent["project_evaluations"] = evaluate_projects(llm, agent, projects, project_initial_eval)
        
    #Saving results
    result: Dict[str, Any] = {
        "run_config": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "run_label": args.run_label,
            "model": args.model,
            "profiles": args.profiles,
            "project_ids": valid_project_ids,
            "intention": args.intention,
            "thinking": args.thinking,
            "seed": args.seed,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_new_tokens": args.max_new_tokens,
            "discussion_prompt_file": args.discussion_prompt_file,
            "project_evaluations_skipped": args.skip_project_evaluations,
        },
        "project_initial_evaluation": {agent['agent_id']: agent['project_evaluations'] for agent in agents},
        "model_runtime": llm.runtime_metadata,
    }

    ##Step 2 -- Initial formulation
    for agent in agents:
        agent["initial_budget"] = run_initial_vote(llm, agent, project_catalog)
        agent["initial_selection"] = parse_vote_response(agent["initial_budget"], valid_project_ids)
    #Saving results
    result["initial_votes"] = {agent["agent_id"]: {"stakeholder_group": agent["stakeholder_group"], "vote": agent["initial_budget"], "parsed_vote": agent["initial_selection"]} for agent in agents}

    ###########################################################################################
    ##########################################################################################
    ##########################################################################################
    ## Step 3 -- Discussion phase
    with open(prompt_path / args.discussion_prompt_file) as f:
        discussion_prompt = f.read()

    discussions = run_pairwise_discussions(llm, agents, discussion_prompt, project_catalog, intention_step=args.intention)
    #Saving results
    result["pairwise_discussions"] = discussions

    ###########################################################################################
    ## Step 4 -- Final formulation
    #### DO YOU WANT TO ADD FINAL INTENTION IN THE VOTING??
    for agent in agents:
        agent["final_budget"] = run_final_vote(llm, agent, project_catalog, discussions, final_budget_prompt, intention_step=args.intention)
        agent["final_selection"] = parse_vote_response(agent["final_budget"], valid_project_ids)
    #Saving results
    result["final_votes"] = {agent["agent_id"]: {"stakeholder_group": agent["stakeholder_group"], "vote": agent["final_budget"], "parsed_vote": agent["final_selection"]} for agent in agents}

    ###########################################################################################
    ## Step 5 -- Orchestrator decision
    decision = aggregate_votes([agent["final_selection"]["selected_projects"] for agent in agents])

    #Saving results
    result["orchestrator"] = {"method": "deterministic_majority_aggregation", "decision": decision}

    if isinstance(decision["final_vote"], list):
        result["metrics"] = compute_metrics(
            selected_projects=decision["final_vote"],
            projects=projects,
            agent_profiles=[agent["utility_profile"] for agent in agents],
            budget=100,
        )
    else:
        result["metrics"] = None

    ###########################################################################################
    ## Step 6 -- saving all json
    # Save complete simulation
    # Keep the model-native raw completion and stopping diagnostics alongside
    # the protocol responses; invalid/truncated generations remain observations.
    result["generation_records"] = llm.generation_records
    output_path = OUTPUT_DIR / args.output
    output_path = output_path.with_name(f"{llm.name}_{output_path.name}")
    save_json(result, output_path)

    print(f"\nSimulation saved to: {output_path}")
