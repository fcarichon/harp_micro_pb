"""Record experiment inputs and the installed environment without loading a model."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--upstream-commit", required=True)
    parser.add_argument("--matrix", type=Path, default=ROOT / "experiments" / "matrix_fullconfigs_qwen30b.json")
    parser.add_argument("--revision", default=os.environ.get("HARP_MODEL_REVISION"))
    args = parser.parse_args()
    matrix = args.matrix if args.matrix.is_absolute() else ROOT / args.matrix
    entries = json.loads(matrix.read_text())
    models = {entry["model"] for entry in entries}
    if len(models) != 1:
        raise SystemExit("A per-model manifest requires exactly one model in the matrix")
    model = models.pop()
    hf_cache = Path(os.environ["HF_HOME"])
    model_cache = hf_cache / ("models--" + model.replace("/", "--"))
    revision = args.revision or (model_cache / "refs" / "main").read_text().strip()
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        raise SystemExit("Expected an exact 40-character model revision")
    loader_revision = os.environ.get("HARP_MODEL_REVISION")
    if loader_revision and loader_revision != revision:
        raise SystemExit("HARP_MODEL_REVISION differs from the manifest revision")
    snapshot = model_cache / "snapshots" / revision
    index = json.loads((snapshot / "model.safetensors.index.json").read_text())
    required = sorted(set(index["weight_map"].values()) | {
        "config.json", "tokenizer_config.json", "tokenizer.json", "generation_config.json",
        "model.safetensors.index.json"
    })
    if model == "google/gemma-4-31B-it":
        required = sorted(set(required) | {"processor_config.json", "chat_template.jinja"})
    missing = [name for name in required if not (snapshot / name).is_file()]
    if missing:
        raise SystemExit(f"Incomplete cached checkpoint: {missing}")
    inputs = [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for folder, pattern in (("src", "*.py"), ("prompts", "*.txt"),
                            ("data", "*.json"), ("experiments", "*.py"),
                            ("experiments", "*.sbatch")):
        inputs.extend(sorted((ROOT / folder).glob(pattern)))
    inputs.append(matrix)
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_commit": args.upstream_commit,
        "checkout": str(ROOT),
        "host": socket.gethostname(),
        "python": platform.python_version(),
        "environment": os.environ.get("UV_PROJECT_ENVIRONMENT"),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("torch", "transformers", "accelerate", "numpy", "huggingface-hub")},
        "model": model,
        "cached_model_revision": revision,
        "revision_pinned_in_loader": loader_revision == revision,
        "model_cache": str(model_cache),
        "checkpoint_files_present": len(required),
        "checkpoint_shards": len(set(index["weight_map"].values())),
        "checkpoint_metadata_sha256": {
            name: hashlib.sha256((snapshot / name).read_bytes()).hexdigest()
            for name in required if not name.endswith(".safetensors")
        },
        "matrix_entries": len(entries),
        "seed": sorted({entry["seed"] for entry in entries}),
        "input_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted(inputs)},
        "runtime_note": "Shared existing environment; uv --frozen --no-sync; HF offline mode.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
