from __future__ import annotations

from edge_imci.inference.adapters import GenerationOutput
from edge_imci.inference.mlx_adapter import load_model_matrix


def test_qwen_baseline_matrix_is_complete_and_immutable():
    matrix = load_model_matrix()
    models = matrix["models"]

    assert matrix["matrix_version"] == "edge-imci-qwen-baseline-v1"
    assert matrix["weights_modified"] is False
    assert "none" in matrix["checkpoint_selection"]
    assert [model["name"] for model in models] == ["qwen3-0.6b", "qwen3-1.7b", "qwen3-4b-4bit"]
    assert len({model["model_id"] for model in models}) == len(models)
    for model in models:
        assert len(model["revision"]) == 40
        assert model["tokenizer_revision"] == model["revision"]
        assert model["base_or_instruct"] == "post-trained chat/instruct"
        assert model["context_length"] == 40960
    assert models[-1]["quantization"] == "4-bit group-size-64 MLX; bfloat16 compute"
    runtime = matrix["runtime"]
    assert runtime["backend"] == "mlx-lm"
    assert runtime["backend_version"] == "0.31.3"
    assert runtime["batch_size"] == 1
    assert runtime["temperature"] == 0.0
    assert runtime["enable_thinking"] is False


def test_generation_output_reports_only_available_throughput():
    assert GenerationOutput("x").tokens_per_second is None
    assert GenerationOutput("x", output_token_count=4, generation_seconds=0).tokens_per_second is None
    assert GenerationOutput("x", output_token_count=4, generation_seconds=0.5).tokens_per_second == 8.0
