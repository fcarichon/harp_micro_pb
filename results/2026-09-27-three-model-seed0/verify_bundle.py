"""Verify archived inputs and regenerate all three analyses without model execution."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(arguments):
    result = subprocess.run(
        [sys.executable, *map(str, arguments)], capture_output=True, text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"Analysis failed (exit {result.returncode}): {result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    publication = read_json(ROOT / "publication_manifest.json")
    for relative, expected in publication["file_sha256"].items():
        path = (ROOT / relative).resolve()
        check(ROOT in path.parents, f"Path leaves bundle: {relative}")
        check(path.is_file() and sha256(path) == expected, f"Checksum mismatch: {relative}")

    common_matrix = None
    with tempfile.TemporaryDirectory(prefix="harp-results-verify-") as temporary:
        for model in publication["models"]:
            label = model["label"]
            snapshot = ROOT / model["snapshot"]
            manifest = read_json(ROOT / model["public_manifest"])
            for relative, expected in manifest["input_sha256"].items():
                path = snapshot / relative
                check(path.is_file() and sha256(path) == expected,
                      f"{label}: frozen input mismatch: {relative}")

            matrix_path = ROOT / model["matrix"]
            matrix = read_json(matrix_path)
            check(len(matrix) == 60, f"{label}: expected 60 matrix entries")
            check(all(row["model"] == manifest["model"] and row["seed"] == 0
                      for row in matrix), f"{label}: wrong model/seed")
            without_model = [{k: v for k, v in row.items() if k != "model"} for row in matrix]
            if common_matrix is None:
                common_matrix = without_model
            else:
                check(without_model == common_matrix, f"{label}: matrix order/settings differ")

            results = ROOT / model["results"]
            published_report = ROOT / model["report"]
            regenerated = Path(temporary) / label
            run_json([
                snapshot / "experiments/summarize_full_run.py",
                "--matrix", matrix_path, "--results-dir", results,
                "--report-dir", regenerated,
            ])
            actual = read_json(regenerated / "coverage.json")
            expected = read_json(published_report / "coverage.json")
            check(actual["coverage_complete"] and actual["counts"]["completed"] == 60,
                  f"{label}: incomplete coverage")
            check(not actual["report_analysis"]["errors"], f"{label}: analysis errors")
            for field in ("counts", "scientific_summary", "entries"):
                check(actual[field] == expected[field], f"{label}: {field} differs")
            check(actual["report_analysis"]["overall"] == expected["report_analysis"]["overall"],
                  f"{label}: overall metrics differ")
            check(csv_rows(regenerated / "results.csv") == csv_rows(published_report / "results.csv"),
                  f"{label}: per-run CSV differs")

            if model["instrumented"]:
                diagnostics = run_json([
                    snapshot / "experiments/check_generation_diagnostics.py",
                    "--results-dir", results, "--model", manifest["model"],
                    "--revision", manifest["cached_model_revision"], "--expected-count", "60",
                ])
                archived = read_json(published_report / "generation_diagnostics.json")
                check(diagnostics["diagnostics_complete"], f"{label}: incomplete diagnostics")
                for key in ("observations", "entries", "runtime_variants"):
                    check(diagnostics[key] == archived[key], f"{label}: diagnostic {key} differs")
            print(f"{label}: 60/60; hashes, coverage, every CSV row and metrics match"
                  + ("; 720-call diagnostics match" if model["instrumented"] else ""))

    print("PASS: 180 raw results verified; no model execution or archive changes.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
