"""Stream-verify the selected GGUF without changing the organizer's downloader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "provenance/4B-alpha-second/artifact.json"


def verify_artifact(path: Path, expected: dict) -> dict:
    if not path.is_file():
        raise ValueError(f"Model not found: {path}")
    size = path.stat().st_size
    if size != expected["bytes"]:
        raise ValueError(f"Model size mismatch: expected {expected['bytes']}, got {size}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if stream.read(4) != b"GGUF":
            raise ValueError("Model does not have a GGUF header")
        stream.seek(0)
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected["sha256"]:
        raise ValueError(f"Model checksum mismatch: expected {expected['sha256']}, got {actual}")
    return {"status": "VERIFIED", "path": str(path.resolve()), "bytes": size, "sha256": actual}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Verify a copy outside the default model directory")
    args = parser.parse_args()
    record = json.loads(ARTIFACT.read_text())
    metadata = json.loads((ROOT / "metadata.json").read_text())
    expected = record["gguf"]
    if metadata["_runtime"]["model_path"] != f"model/{expected['filename']}":
        raise SystemExit("Submission metadata and artifact record disagree")
    path = args.path or ROOT / metadata["_runtime"]["model_path"]
    try:
        result = verify_artifact(path, expected)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
