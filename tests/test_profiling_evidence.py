import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "provenance/4B-alpha-second/profiling/2026-09-22-ubuntu-adtc"


def test_original_profile_files_match_import_inventory_and_usb_checksums():
    receipt = json.loads((PACKET / "import-verification.json").read_text())
    raw = PACKET / receipt["raw_directory"]
    assert receipt["status"] == "VERIFIED_BYTE_PRESERVING_IMPORT"
    assert len(receipt["files"]) == 17
    assert {path.name for path in raw.iterdir()} == set(receipt["files"])
    for name, expected in receipt["files"].items():
        assert Path(name).name == name
        content = (raw / name).read_bytes()
        assert len(content) == expected["bytes"]
        assert hashlib.sha256(content).hexdigest() == expected["sha256"]
    for line in (raw / "report-and-log.sha256").read_text().splitlines():
        expected_hash, original_path = line.split(maxsplit=1)
        name = Path(original_path).name
        assert receipt["files"][name]["sha256"] == expected_hash
    assert receipt["files"]["submission.json"]["sha256"] == "20244dcb046ef3c68c0d0aa10e2784bb4928d1c1876dbd52adf1d2d7b44b2a48"
    assert receipt["files"]["console.log"]["sha256"] == "b32c92ebf463e859bde7b7650510f88a74fc73f5904d1f63201bea5ea1ffb00e"


def test_full_profile_matches_measured_snapshot_and_selected_artifact():
    raw = PACKET / "raw"
    report = json.loads((raw / "submission.json").read_text())
    metadata = json.loads((raw / "metadata.json").read_text())
    excerpt = json.loads((PACKET / "report-excerpt.console.json").read_text())
    artifact = json.loads((ROOT / "provenance/4B-alpha-second/artifact.json").read_text())
    assert report["schema_version"] == "1.3.0"
    assert report["environment"]["measured_on"] == "participant_laptop"
    assert report["submission"] == {key: value for key, value in metadata.items() if not key.startswith("_")}
    assert all(report[key] == value for key, value in excerpt.items())
    assert report["accuracy"] == [{
        "benchmark": "arc_easy", "dataset_version": "lm-eval-harness", "language": "en",
        "samples": 50, "score": 0.78, "metric": "acc_norm",
    }]
    commit = (raw / "submission-commit.txt").read_text().strip()
    assert commit == "0017d85836d7a0cf7c03f12315ae68502138b8a4"
    assert (raw / "submission-commit-after.txt").read_text().strip() == commit
    assert report["reproducibility"]["git_commit_sha"] == commit[:12]
    assert report["reproducibility"]["random_seed"] == 42
    assert (raw / "worktree-status.txt").read_bytes() == b""
    assert (raw / "worktree-status-after.txt").read_bytes() == b""
    before = json.loads((raw / "model-verification.json").read_text())
    assert before == json.loads((raw / "model-verification-after.json").read_text())
    assert before["status"] == "VERIFIED"
    assert before["sha256"] == artifact["gguf"]["sha256"]
    assert before["bytes"] == artifact["gguf"]["bytes"]
    assert report["model_info"]["params_count"] == artifact["gguf"]["parameters"]
    assert report["model_info"]["params_match"] is True
    assert (raw / "status.txt").read_text().strip() == "Profiler exit status: 0"
    assert "Exit status: 0" in (raw / "time-and-memory.txt").read_text()
