import argparse
import json
import os
import shlex
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_entry(matrix_path: Path, index: int) -> dict:
    if not matrix_path.is_absolute():
        matrix_path = ROOT / matrix_path
    with matrix_path.open("r", encoding="utf-8") as handle:
        matrix = json.load(handle)
    if not isinstance(matrix, list) or not matrix:
        raise ValueError("The matrix must be a non-empty JSON list.")
    if not 0 <= index < len(matrix):
        raise ValueError(f"Index {index} is outside the matrix range 0-{len(matrix) - 1}.")
    entry = matrix[index]
    if not isinstance(entry, dict):
        raise ValueError(f"Matrix entry {index} must be an object.")
    for field in ("scenario", "profiles", "project_ids", "model", "seed"):
        if field not in entry:
            raise ValueError(f"Matrix entry {index} is missing {field!r}.")
    scenario = entry["scenario"]
    if not isinstance(scenario, str) or not scenario or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        for char in scenario
    ):
        raise ValueError("Scenario names must contain only letters, digits, '_' or '-'.")
    if not isinstance(entry["seed"], int) or isinstance(entry["seed"], bool):
        raise ValueError("The seed must be an integer.")
    if not isinstance(entry["model"], str) or not Path(entry["model"]).name:
        raise ValueError("The model must be a non-empty name or path.")
    for field in ("profiles", "project_ids"):
        if not isinstance(entry[field], list) or not entry[field] or any(
            not isinstance(value, str) or not value for value in entry[field]
        ):
            raise ValueError(f"{field} must be a non-empty list of strings.")
    return entry


def build_command(entry: dict, output_dir: Path) -> tuple[list[str], Path]:
    """Keep pilot settings unchanged and predict its model-prefixed output name."""
    output_name = f"v2_{entry['scenario']}_seed{entry['seed']}.json"
    requested_output = output_dir.expanduser().resolve() / output_name
    actual_output = requested_output.with_name(
        f"{Path(entry['model']).name}_{output_name}"
    )
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
        str(requested_output),
    ]
    if entry.get("intention", False):
        command.append("--intention")
    if entry.get("discussion_prompt_file"):
        command.extend(["--discussion_prompt_file", entry["discussion_prompt_file"]])
    if entry.get("skip_project_evaluations", True):
        command.append("--skip_project_evaluations")
    return command, actual_output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run one HARP experiment-matrix entry.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs",
        help="Destination for this batch; use a new directory for each new sweep.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command and expected result path without starting the pilot.",
    )
    args = parser.parse_args(argv)
    try:
        entry = load_entry(Path(args.matrix), args.index)
        command, output_path = build_command(entry, args.output_dir)
        if output_path.exists() or output_path.is_symlink():
            raise ValueError(
                f"Refusing to overwrite existing output: {output_path}. "
                "Choose a new --output-dir for a new run."
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print("Experiment entry:", json.dumps(entry, sort_keys=True), flush=True)
    print("Output:", str(output_path), flush=True)
    print("Executing:", shlex.join(command), flush=True)
    if args.dry_run:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
