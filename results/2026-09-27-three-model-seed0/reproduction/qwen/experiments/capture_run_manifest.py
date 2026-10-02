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
    args = parser.parse_args()
    model = "Qwen/Qwen3-30B-A3B-Instruct-2507"
    hf_cache = Path(os.environ["HF_HOME"])
    model_cache = hf_cache / ("models--" + model.replace("/", "--"))
    revision = (model_cache / "refs" / "main").read_text().strip()
    snapshot = model_cache / "snapshots" / revision
    index = json.loads((snapshot / "model.safetensors.index.json").read_text())
    required = sorted(set(index["weight_map"].values()) | {
        "config.json", "tokenizer_config.json", "tokenizer.json", "generation_config.json"
    })
    missing = [name for name in required if not (snapshot / name).is_file()]
    if missing:
        raise SystemExit(f"Incomplete cached checkpoint: {missing}")
    inputs = [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for folder, pattern in (("src", "*.py"), ("prompts", "*.txt"),
                            ("data", "*.json"), ("experiments", "*.py"),
                            ("experiments", "*.sbatch")):
        inputs.extend(sorted((ROOT / folder).glob(pattern)))
    matrix = ROOT / "experiments" / "matrix_fullconfigs_qwen30b.json"
    inputs.append(matrix)
    entries = json.loads(matrix.read_text())
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
        "model_cache": str(model_cache),
        "checkpoint_files_present": len(required),
        "checkpoint_shards": len(set(index["weight_map"].values())),
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
