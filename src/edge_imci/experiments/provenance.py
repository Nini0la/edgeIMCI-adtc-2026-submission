"""Deterministic hashing, safe paths, atomic writes, and sanitized provenance."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SECRET_KEY = re.compile(
    r"^(authorization|api[_-]?key|access[_-]?token|id[_-]?token|bearer[_-]?token|token|password|"
    r"client[_-]?secret|secret[_-]?key|credentials?)$",
    re.I,
)
SECRET_ARG = re.compile(
    r"(--?(?:api[_-]?(?:key|token)|access[_-]?token|token|password|secret|authorization))"
    r"(?:=|\s+)([^\s]+)",
    re.I,
)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the documented canonical representation used for registry hashes."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_canonical(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def hash_file(path: str | Path) -> tuple[str, int]:
    source = Path(path)
    digest = hashlib.sha256()
    size = 0
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def atomic_write_json(path: str | Path, value: Any, *, overwrite: bool = True) -> Path:
    """Atomically replace a JSON file after fsyncing its temporary sibling."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return destination


def resolve_repo_path(
    repo_root: str | Path, reference: str | Path, *, must_exist: bool = True
) -> Path:
    """Resolve a repository-relative reference without allowing traversal."""
    root = Path(repo_root).resolve()
    raw = Path(reference)
    if raw.is_absolute():
        raise ValueError(f"repository reference must be relative: {reference}")
    resolved = (root / raw).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"repository reference escapes root: {reference}")
    if must_exist and not resolved.exists():
        raise ValueError(f"repository reference does not exist: {reference}")
    return resolved


def repo_relative(repo_root: str | Path, path: str | Path) -> str:
    root = Path(repo_root).resolve()
    resolved = Path(path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"artifact is outside repository: {path}")
    return resolved.relative_to(root).as_posix()


def sanitize_value(value: Any) -> Any:
    """Recursively remove secret-bearing fields from caller/provider payloads."""
    if isinstance(value, Mapping):
        return {
            str(key): sanitize_value(item)
            for key, item in value.items()
            if not SECRET_KEY.search(str(key))
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_value(item) for item in value]
    return value


def sanitize_command(command: Sequence[str]) -> list[str]:
    sanitized: list[str] = []
    redact_next = False
    for raw in command:
        item = str(raw)
        if redact_next:
            sanitized.append("[REDACTED]")
            redact_next = False
            continue
        if SECRET_KEY.search(item.lstrip("-").split("=", 1)[0]):
            if "=" in item:
                sanitized.append(item.split("=", 1)[0] + "=[REDACTED]")
            else:
                sanitized.append(item)
                redact_next = True
            continue
        sanitized.append(SECRET_ARG.sub(r"\1=[REDACTED]", item))
    return sanitized


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def capture_git_provenance(
    repo_root: str | Path,
    *,
    git_runner: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """Capture commit and stable dirty-state evidence without storing the diff."""
    root = Path(repo_root).resolve()
    runner = git_runner or (lambda *args: _git(root, *args))
    try:
        commit = runner("rev-parse", "HEAD").strip()
        status = runner("status", "--porcelain=v1", "--untracked-files=all")
        dirty = bool(status.strip())
        result: dict[str, Any] = {"git_commit": commit, "dirty_worktree": dirty}
        if dirty:
            try:
                tracked = runner("diff", "--binary", "HEAD")
                result["dirty_state_sha256"] = sha256_bytes(
                    (tracked + "\n" + status).encode("utf-8")
                )
            except Exception:
                result["dirty_state_capture"] = "UNAVAILABLE"
        return result
    except Exception:
        return {
            "git_commit": None,
            "dirty_worktree": None,
            "git_capture": "UNAVAILABLE",
        }


def runtime_provenance(
    *, repo_root: str | Path | None = None, command: Sequence[str] | None = None
) -> dict[str, Any]:
    result = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "runner_version": "edge-imci-0.1.0",
        "dependency_identity": f"python:{sys.version_info.major}.{sys.version_info.minor}",
        "command": sanitize_command(command or sys.argv),
    }
    if repo_root is not None:
        root = Path(repo_root)
        for candidate in ("uv.lock", "pyproject.toml"):
            path = root / candidate
            if path.exists():
                digest, _ = hash_file(path)
                result["dependency_identity"] = f"{candidate}:sha256:{digest}"
                break
    return result
