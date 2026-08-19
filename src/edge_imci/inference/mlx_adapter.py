"""Local untuned generative adapter for pinned Hugging Face checkpoints on Apple Silicon."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from edge_imci.inference.adapters import GenerationOutput

DEFAULT_MODEL_CONFIG = Path(__file__).resolve().parents[3] / "configs" / "model_baselines.json"


class MlxModelAdapter:
    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        tokenizer_revision: str,
        base_or_instruct: str,
        parameter_count_billions: float,
        context_length: int,
        weights_modified: bool,
        checkpoint_selection: str,
        max_tokens: int,
        temperature: float = 0.0,
        enable_thinking: bool = False,
        seed: int = 20260819,
        dtype: str = "bfloat16",
        quantization: str | None = None,
    ) -> None:
        try:
            import mlx.core as mx
            from mlx_lm import load
            from mlx_lm.sample_utils import make_sampler
        except ImportError as error:
            raise RuntimeError('MLX model support requires: python -m pip install -e ".[models]"') from error
        if tokenizer_revision != revision:
            raise ValueError("MLX loader uses one repository revision for model and tokenizer; revisions must match")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        self._mx = mx
        self._model_id = model_id
        self._revision = revision
        self._tokenizer_revision = tokenizer_revision
        self._base_or_instruct = base_or_instruct
        self._parameter_count_billions = parameter_count_billions
        self._context_length = context_length
        self._weights_modified = weights_modified
        self._checkpoint_selection = checkpoint_selection
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._enable_thinking = enable_thinking
        self._seed = seed
        self._dtype = dtype
        self._quantization = quantization
        self._sampler = make_sampler(temp=temperature)
        mx.random.seed(seed)
        self._model, self._tokenizer, self._loaded_config = load(
            model_id,
            revision=revision,
            return_config=True,
        )

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_metadata(self) -> dict[str, Any]:
        return {
            "model_id": self._model_id,
            "model_revision": self._revision,
            "tokenizer_revision": self._tokenizer_revision,
            "base_or_instruct": self._base_or_instruct,
            "parameter_count_billions": self._parameter_count_billions,
            "context_length": self._context_length,
            "weights_modified": self._weights_modified,
            "checkpoint_selection": self._checkpoint_selection,
            "dtype": self._dtype,
            "quantization": self._quantization,
        }

    @property
    def runtime_metadata(self) -> dict[str, Any]:
        return {
            "backend": "mlx-lm",
            "backend_version": importlib.metadata.version("mlx-lm"),
            "mlx_version": importlib.metadata.version("mlx"),
            "device": str(self._mx.default_device()),
            "cpu_gpu_model": _sysctl("machdep.cpu.brand_string"),
            "ram_bytes": _int_sysctl("hw.memsize"),
            "operating_system": platform.platform(),
            "machine": platform.machine(),
            "thread_count": os.cpu_count(),
            "batch_size": 1,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "enable_thinking": self._enable_thinking,
            "seed": self._seed,
            "dtype": self._dtype,
            "quantization": self._quantization,
        }

    def generate(self, prompt: str) -> GenerationOutput:
        from mlx_lm import stream_generate

        formatted_prompt = self._tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self._enable_thinking,
        )
        chunks: list[str] = []
        last_response = None
        for response in stream_generate(
            self._model,
            self._tokenizer,
            formatted_prompt,
            max_tokens=self._max_tokens,
            sampler=self._sampler,
        ):
            chunks.append(response.text)
            last_response = response
        if last_response is None:
            return GenerationOutput("")
        generation_seconds = (
            last_response.generation_tokens / last_response.generation_tps
            if last_response.generation_tps
            else None
        )
        return GenerationOutput(
            text="".join(chunks),
            input_token_count=last_response.prompt_tokens,
            output_token_count=last_response.generation_tokens,
            generation_seconds=generation_seconds,
        )


def load_model_matrix(path: str | Path = DEFAULT_MODEL_CONFIG) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def adapter_from_config(model_name: str, *, external: bool = False) -> MlxModelAdapter:
    matrix = load_model_matrix()
    try:
        model = next(item for item in matrix["models"] if item["name"] == model_name)
    except StopIteration as error:
        choices = [item["name"] for item in matrix["models"]]
        raise ValueError(f"unknown model name {model_name!r}; choose one of {choices}") from error
    runtime = matrix["runtime"]
    return MlxModelAdapter(
        model_id=model["model_id"],
        revision=model["revision"],
        tokenizer_revision=model["tokenizer_revision"],
        base_or_instruct=model["base_or_instruct"],
        parameter_count_billions=model["parameter_count_billions"],
        context_length=model["context_length"],
        weights_modified=matrix["weights_modified"],
        checkpoint_selection=matrix["checkpoint_selection"],
        max_tokens=runtime["max_tokens_external" if external else "max_tokens_internal"],
        temperature=runtime["temperature"],
        enable_thinking=runtime["enable_thinking"],
        seed=runtime["seed"],
        dtype=runtime["dtype"],
        quantization=model.get("quantization", runtime["quantization"]),
    )


def _sysctl(name: str) -> str | None:
    try:
        return subprocess.check_output(["sysctl", "-n", name], text=True).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _int_sysctl(name: str) -> int | None:
    value = _sysctl(name)
    return int(value) if value and value.isdigit() else None
