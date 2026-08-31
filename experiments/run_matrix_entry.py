import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one HARP experiment-matrix entry.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--index", type=int, required=True)
    args = parser.parse_args()

    matrix_path = Path(args.matrix)
    if not matrix_path.is_absolute():
        matrix_path = ROOT / matrix_path
    with matrix_path.open("r", encoding="utf-8") as handle:
        matrix = json.load(handle)

    entry = matrix[args.index]
    output_name = f"v2_{entry['scenario']}_seed{entry['seed']}.json"
    command = [
        sys.executable,
        str(ROOT / "src" / "run_pilot.py"),
        "--profiles",
        *entry["profiles"],
        "--project_ids",
        *entry["project_ids"],
        "--model",
        entry["model"],
        "--seed",
        str(entry["seed"]),
        "--temperature",
        str(entry.get("temperature", 0.7)),
        "--top_p",
        str(entry.get("top_p", 0.9)),
        "--max_new_tokens",
        str(entry.get("max_new_tokens", 512)),
        "--run_label",
        entry["scenario"],
        "--output",
        output_name,
    ]
    if entry.get("intention", False):
        command.append("--intention")
    if entry.get("discussion_prompt_file"):
        command.extend(["--discussion_prompt_file", entry["discussion_prompt_file"]])
    if entry.get("skip_project_evaluations", True):
        command.append("--skip_project_evaluations")

    print("Experiment entry:", json.dumps(entry, sort_keys=True), flush=True)
    print("Executing:", " ".join(command), flush=True)
    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
