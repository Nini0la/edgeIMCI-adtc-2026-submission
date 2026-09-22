import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_model_artifact", ROOT / "scripts/verify_model_artifact.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_selected_artifact_is_consistent():
    metadata = json.loads((ROOT / "metadata.json").read_text())
    artifact = json.loads((ROOT / "provenance/4B-alpha-second/artifact.json").read_text())
    downloader = (ROOT / "download_model.sh").read_text()
    assert metadata["model"]["name"] == "EdgeIMCI-4B-alpha-second-Q4_K_M"
    assert metadata["model"]["parameters_estimate"] == "4B"
    assert metadata["model"]["quantization"] == "GGUF Q4_K_M"
    assert metadata["_runtime"]["model_path"] == f"model/{artifact['gguf']['filename']}"
    # ADTC profiler schema 1.3.0 rejects additional provenance properties.
    assert set(metadata["provenance"]) == {
        "base_model_source",
        "base_model_commit_sha",
        "fine_tuning_method",
        "training_datasets",
    }
    assert metadata["provenance"]["base_model_source"] == "huggingface:Qwen/Qwen3-4B"
    assert metadata["provenance"]["base_model_commit_sha"] == artifact["base_model_revision"]
    assert metadata["provenance"]["fine_tuning_method"] == "lora"
    assert "beta0_1k_multitask_enriched_2258_v1" in metadata["provenance"]["training_datasets"][0]
    publication = json.loads((ROOT / "provenance/dataset/publication.json").read_text())
    assert publication["repository"]["repo_id"] in metadata["provenance"]["training_datasets"][0]
    assert publication["repository"]["revision"] in metadata["provenance"]["training_datasets"][0]
    assert publication["frozen_training_release"]["manifest_sha256"] == "0820f092ed585a46182e075477f9246917629061b03a3f57d92cb1087e303706"
    assert len(metadata["test_prompts"]) == 2
    assert artifact["training_run_id"] == "multitask2258-20260922-v1--qwen4-e2-lr3-s20260824"
    assert artifact["gguf"]["bytes"] == 2497280288
    assert artifact["gguf"]["sha256"] == "a4a8c5bb2d9f3401defa1cb8ea007812d5916c0242d8306a1c7ed6322d550919"
    assert re.fullmatch(r"[a-f0-9]{40}", artifact["hosting"]["revision"])
    assert f'MODEL_FILE="$MODEL_DIR/{artifact["gguf"]["filename"]}"' in downloader
    assert f'MODEL_URL="{artifact["hosting"]["url"]}"' in downloader
    assert f'/resolve/{artifact["hosting"]["revision"]}/' in artifact["hosting"]["url"]
    assert "[YOUR_" not in downloader
    assert "reproducibility" not in metadata


def test_original_receipts_and_smokes_match():
    root = ROOT / "provenance/4B-alpha-second"
    inventory_file = root / "artifact_hashes.json"
    assert hashlib.sha256(inventory_file.read_bytes()).hexdigest() == "7f53d7a0eac4938194fdbc977f64bd0b17bbb8fc6131f3573fcc790edfbca1a0"
    inventory = json.loads(inventory_file.read_text())
    for local, remote in (("training_config.json", "config.json"), ("trainer_log_history.json", "trainer_log_history.json")):
        content = (root / local).read_bytes()
        assert len(content) == inventory[remote]["bytes"]
        assert hashlib.sha256(content).hexdigest() == inventory[remote]["sha256"]
    remote = json.loads((root / "remote_run_manifest.json").read_text())
    assert remote["tokenization"]["TRAIN"]["count"] == 2258
    assert remote["status"] == "SUCCEEDED"
    assert remote["epoch_evidence"]["exported_epoch"] == 2
    smoke = json.loads((root / "smoke_results.json").read_text())
    assert len(smoke) == 4
    assert all(row["exact_target"] and row["schema_valid"] and row["state_match"] and row["error"] is None for row in smoke)


def test_paired_demonstration_retains_all_outputs_and_boundaries():
    result = json.loads((ROOT / "provenance/4B-alpha-second/before_after_results.json").read_text())
    assert result["base"]["revision"] == "1cfa9a7208912126459214e8b04321603b3df60c"
    assert result["fine_tuned"]["run"] == "multitask2258-20260922-v1--qwen4-e2-lr3-s20260824"
    assert result["identical_rendered_prompts_and_input_ids"] is True
    assert result["identical_effective_generation_settings"] is True
    assert result["quantized_artifact_tested"] is False
    assert "no unseen-data claim" in result["training_overlap"]
    assert len(result["cases"]) == 3
    assert len(result["outputs"]) == 6
    outputs = {(row["model"], row["case_id"]): row for row in result["outputs"]}
    assert len(outputs) == 6
    for case in result["cases"]:
        for model in ("base", "fine_tuned"):
            row = outputs[model, case["id"]]
            assert row["text"]
            assert row["reached_token_limit"] is False
            if case["mode"] == "EXTRACTION":
                exact = json.dumps(json.loads(row["text"]), sort_keys=True) == json.dumps(case["expected_target"], sort_keys=True)
                assert row["exact_target"] is exact
                assert exact is (model == "fine_tuned")


@pytest.mark.parametrize("failure", [None, "size", "hash", "header", "missing"])
def test_streaming_verification_fails_closed(tmp_path, failure):
    payload = b"GGUF" + b"test bytes"
    path = tmp_path / "model.gguf"
    if failure != "missing":
        path.write_bytes(payload if failure != "header" else b"NOPE" + payload[4:])
    expected = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    if failure == "size":
        expected["bytes"] += 1
    if failure == "hash":
        expected["sha256"] = "0" * 64
    if failure:
        with pytest.raises(ValueError):
            verifier.verify_artifact(path, expected)
    else:
        assert verifier.verify_artifact(path, expected)["status"] == "VERIFIED"
