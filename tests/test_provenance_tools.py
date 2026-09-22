import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_tool(relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("destination", ["existing", "file", "source", "ancestor", "child", "symlink", "dangling_symlink"])
def test_dataset_builder_never_removes_existing_or_source_paths(tmp_path, monkeypatch, destination):
    builder = load_tool("provenance/dataset/build_dataset_package.py")
    source = tmp_path / "sources"
    source.mkdir()
    sentinel = source / "keep.txt"
    sentinel.write_text("source must survive")
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep.txt").write_text("existing must survive")
    output = {
        "existing": existing,
        "file": sentinel,
        "source": source,
        "ancestor": tmp_path,
        "child": source / "new-output",
    }.get(destination, tmp_path / "link")
    if destination == "symlink":
        output.symlink_to(existing, target_is_directory=True)
    elif destination == "dangling_symlink":
        output.symlink_to(tmp_path / "missing", target_is_directory=True)
    monkeypatch.setattr(builder, "parse_args", lambda: argparse.Namespace(source_root=source, output=output))
    with pytest.raises((ValueError, FileExistsError)):
        builder.main()
    assert sentinel.read_text() == "source must survive"
    assert (existing / "keep.txt").read_text() == "existing must survive"
    assert not (source / "new-output").exists()
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("missing_dependency", [False, True])
def test_dataset_preflight_does_not_create_partial_output(tmp_path, monkeypatch, missing_dependency):
    builder = load_tool("provenance/dataset/build_dataset_package.py")
    source = tmp_path / "sources"
    source.mkdir()
    output = tmp_path / "new-package"
    if missing_dependency:
        for name in ("beta0_1k_multitask_v1/train.jsonl", "beta0_1k_multitask_v1/validation.jsonl", "beta0_1k_multitask_v1/manifest.json", "expansion_20260922/addition_candidates.jsonl", "expansion_20260922/manifest.json"):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n")

        def missing(_):
            raise ImportError("pyarrow not installed")

        monkeypatch.setattr(builder.importlib, "import_module", missing)
    monkeypatch.setattr(builder, "parse_args", lambda: argparse.Namespace(source_root=source, output=output))
    with pytest.raises(RuntimeError if missing_dependency else FileNotFoundError):
        builder.main()
    assert not output.exists()


@pytest.mark.parametrize("failure", [None, "truncated", "checksum", "oversized", "network"])
def test_adapter_fetch_preserves_existing_file_on_failure(tmp_path, monkeypatch, failure):
    downloader = load_tool("provenance/4B-alpha-second/download_adapter.py")
    monkeypatch.setattr(downloader, "__file__", str(tmp_path / "download_adapter.py"))
    payload = b"verified adapter bytes"
    name = "adapter_model.safetensors"
    (tmp_path / "artifact.json").write_text(json.dumps({"adapter": {"files": {
        name: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "url": "https://example.invalid/pinned/adapter"}
    }}}))
    target = tmp_path / "adapter" / name
    target.parent.mkdir()
    target.write_bytes(b"previous verified copy")
    transferred = {"truncated": payload[:-1], "checksum": b"x" * len(payload), "oversized": payload + b"extra"}.get(failure, payload)

    def response(url, timeout):
        assert url == "https://example.invalid/pinned/adapter"
        if failure == "network":
            raise OSError("network failure")
        return io.BytesIO(transferred)

    monkeypatch.setattr(downloader.urllib.request, "urlopen", response)
    if failure:
        with pytest.raises((ValueError, OSError)):
            downloader.main()
        assert target.read_bytes() == b"previous verified copy"
    else:
        downloader.main()
        assert target.read_bytes() == payload
    assert not target.with_suffix(target.suffix + ".partial").exists()


@pytest.mark.parametrize("failure", [None, "missing", "size", "checksum", "extra", "escape", "inventory", "root_symlink"])
def test_training_inventory_rejects_modified_files(tmp_path, failure):
    verifier = load_tool("scripts/verify_model_artifact.py")
    root = tmp_path / "run"
    model = root / "merged_model"
    model.mkdir(parents=True)
    payload = b"original weights"
    weights = model / "model.safetensors"
    weights.write_bytes(payload)
    expected = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    inventory = {"merged_model/model.safetensors": expected}
    if failure == "missing":
        weights.unlink()
    elif failure == "size":
        weights.write_bytes(payload + b"extra")
    elif failure == "checksum":
        weights.write_bytes(b"x" * len(payload))
    elif failure == "extra":
        (model / "untracked.json").write_text("{}")
    elif failure == "escape":
        outside = tmp_path / "outside.safetensors"
        outside.write_bytes(payload)
        inventory["merged_model/../../outside.safetensors"] = expected
    elif failure == "root_symlink":
        model.rename(tmp_path / "outside-model")
        model.symlink_to(tmp_path / "outside-model", target_is_directory=True)
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory))
    digest = "0" * 64 if failure == "inventory" else hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    if failure:
        with pytest.raises(ValueError):
            verifier.verify_training_files(root, inventory_path, digest)
    else:
        assert verifier.verify_training_files(root, inventory_path, digest) == 1
