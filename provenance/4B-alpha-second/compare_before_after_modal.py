"""Run the historical three-prompt illustration, not the current submission pair.

From the repository root: modal run --detach provenance/4B-alpha-second/compare_before_after_modal.py
Weights stay on Modal. This script does not invoke ChatEval or sealed TEST data.
"""

import json
from pathlib import Path
import time

import modal

ROOT = Path(__file__).resolve().parent.parent.parent
BASE = "Qwen/Qwen3-4B"
REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
RUN = "multitask2258-20260922-v1--qwen4-e2-lr3-s20260824"
SYSTEM = (
    "When and only when the exact EdgeIMCI extraction-v2 wrapper is present, return one JSON object matching the pinned extraction-routing schema. "
    "Return the existing model-facing encounter object for recoverable encounter findings. "
    'Return only {"route":"INFORMATIONAL_NON_ENCOUNTER"} for general EdgeIMCI or project questions, '
    '{"route":"OUT_OF_SCOPE"} for unsupported requests, {"route":"OUT_OF_SCOPE_URGENT"} for explicit urgent unsupported findings, '
    'or {"route":"UNCERTAIN"} when the input cannot be interpreted safely. '
    "Never invent encounter observations to avoid a route, and never emit classifications, referrals, treatments, rule IDs, markdown, or prose."
)
FREE_SYSTEM = "Respond in clear natural language. Be accurate about EdgeIMCI, preserve uncertainty and negation, stay within supported scope, and never claim autonomous clinical authority."
FREE_PROMPT = "What is EdgeIMCI, and how does its language model relate to the deterministic rules engine?"

source = modal.Volume.from_name("edge-imci-beta0-1k-enriched-2258-matrix-v1-artifacts", create_if_missing=False)
cache = modal.Volume.from_name("edge-imci-hf-cache", create_if_missing=False)
evidence = modal.Volume.from_name("edge-imci-4b-alpha-second-gguf-20260922", create_if_missing=False)
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .pip_install("torch==2.7.1", "transformers==4.57.1", "accelerate==1.9.0", "huggingface_hub==0.34.2")
    .add_local_file(ROOT / "acceptance/historical_extraction_prompts.json", "/inputs/public_prompts.json", copy=True)
    .add_local_file(ROOT / "provenance/4B-alpha-second/artifact_hashes.json", "/inputs/artifact_hashes.json", copy=True)
    .add_local_file(ROOT / "scripts/verify_model_artifact.py", "/root/verify_model_artifact.py", copy=True)
)
app = modal.App("edge-imci-alpha-second-before-after-demo")


@app.function(image=image, gpu="L4", cpu=4, memory=32768, timeout=1800, retries=0,
              volumes={"/source": source, "/model-cache": cache, "/evidence": evidence})
def compare():
    import gc
    import platform
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
    from verify_model_artifact import verify_training_files

    manifest = json.loads((Path("/source") / RUN / "remote_run_manifest.json").read_text())
    if manifest["run_id"] != RUN or manifest["base_model"]["revision"] != REVISION or manifest["status"] != "SUCCEEDED":
        raise ValueError("wrong fine-tuned source")
    if manifest["artifact_manifest_sha256"] != "7f53d7a0eac4938194fdbc977f64bd0b17bbb8fc6131f3573fcc790edfbca1a0":
        raise ValueError("wrong fine-tuned artifact inventory")
    remote_output = Path("/evidence/before-after-public-demo-v1.json")
    if remote_output.exists():
        raise FileExistsError("Preserve the existing remote comparison")
    verified_files = verify_training_files(
        Path("/source") / RUN,
        Path("/inputs/artifact_hashes.json"),
        "7f53d7a0eac4938194fdbc977f64bd0b17bbb8fc6131f3573fcc790edfbca1a0",
    )
    cases = []
    for item in json.loads(Path("/inputs/public_prompts.json").read_text()):
        cases.append({
            "id": item["prompt_id"], "mode": "EXTRACTION", "expected_target": item["expected_target"],
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f'<EDGEIMCI_EXTRACT_V2>\n{item["prompt"]}\n</EDGEIMCI_EXTRACT_V2>'}],
        })
    cases.append({"id": "freeform_architecture_demo", "mode": "FREE_FORM", "messages": [
        {"role": "system", "content": FREE_SYSTEM}, {"role": "user", "content": FREE_PROMPT},
    ]})
    result = {
        "purpose": "Historical three-prompt illustration; not the current submission pair, held-out evaluation, or clinical qualification",
        "selection": "Two historical extraction fixtures plus one architecture question; no response-based selection",
        "training_overlap": "Not ruled out; no unseen-data claim",
        "base": {"model": BASE, "revision": REVISION},
        "fine_tuned": {"name": "4B-alpha-second", "run": RUN, "artifact_manifest_sha256": manifest["artifact_manifest_sha256"]},
        "configuration": {"dtype": "bfloat16", "do_sample": False, "max_new_tokens": 1200, "seed": 0, "enable_thinking": False},
        "environment": {"python": platform.python_version(), "torch": str(torch.__version__), "transformers": str(transformers.__version__), "gpu": torch.cuda.get_device_name()},
        "started_at_unix": time.time(), "cases": cases, "outputs": [],
        "quantized_artifact_tested": False,
        "verified_merged_model_files": verified_files,
    }
    expected_inputs = {}
    for label, path, options in (
        ("base", BASE, {"revision": REVISION, "cache_dir": "/model-cache"}),
        ("fine_tuned", str(Path("/source") / RUN / "merged_model"), {"local_files_only": True}),
    ):
        print(f"Loading {label}", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=False, **options)
        model = AutoModelForCausalLM.from_pretrained(path, trust_remote_code=False, dtype=torch.bfloat16, device_map={"": 0}, **options)
        model.eval()
        generation = GenerationConfig(do_sample=False, max_new_tokens=1200, num_beams=1,
                                      repetition_penalty=1.0, eos_token_id=tokenizer.eos_token_id,
                                      pad_token_id=tokenizer.eos_token_id, bos_token_id=tokenizer.bos_token_id)
        if label == "base":
            result["effective_generation_config"] = generation.to_dict()
        elif generation.to_dict() != result["effective_generation_config"]:
            raise ValueError("effective generation settings differ")
        for case in cases:
            prompt = tokenizer.apply_chat_template(case["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            ids = inputs["input_ids"][0].tolist()
            if label == "base":
                expected_inputs[case["id"]] = (prompt, ids)
                case["rendered_prompt"] = prompt
                case["input_tokens"] = len(ids)
            elif expected_inputs[case["id"]] != (prompt, ids):
                raise ValueError("base/fine-tuned prompt rendering or tokenization differs")
            torch.manual_seed(0)
            torch.cuda.manual_seed_all(0)
            start = time.monotonic()
            with torch.inference_mode():
                generated = model.generate(**inputs, generation_config=generation)
            continuation = generated[0, len(ids):]
            text = tokenizer.decode(continuation, skip_special_tokens=True)
            output = {"model": label, "case_id": case["id"], "text": text, "generated_tokens": len(continuation), "elapsed_seconds": time.monotonic() - start, "reached_token_limit": len(continuation) >= 1200}
            if case["mode"] == "EXTRACTION":
                try:
                    def strict_pairs(pairs):
                        value = {}
                        for key, item in pairs:
                            if key in value:
                                raise ValueError("duplicate JSON key")
                            value[key] = item
                        return value

                    def reject_constant(value):
                        raise ValueError(f"nonfinite JSON constant: {value}")

                    parsed = json.loads(text, object_pairs_hook=strict_pairs, parse_constant=reject_constant)
                    output["json_object"] = isinstance(parsed, dict)
                    output["exact_target"] = json.dumps(parsed, sort_keys=True) == json.dumps(case["expected_target"], sort_keys=True)
                except (ValueError, TypeError) as exc:
                    output.update(json_object=False, exact_target=False, parse_error=str(exc))
            result["outputs"].append(output)
            print(f"{label} {case['id']}: generated {len(continuation)} tokens", flush=True)
        del model, tokenizer, inputs, generated, continuation
        gc.collect()
        torch.cuda.empty_cache()
    result["finished_at_unix"] = time.time()
    result["identical_rendered_prompts_and_input_ids"] = True
    result["identical_effective_generation_settings"] = True
    remote_output.write_text(json.dumps(result, indent=2) + "\n")
    evidence.commit()
    cache.commit()
    return result


@app.local_entrypoint()
def main():
    target = Path(__file__).parent / "before_after_results.json"
    if target.exists():
        raise FileExistsError("Preserve the existing results; do not overwrite a comparison")
    call = compare.spawn()
    print(f"COMPARISON_CALL_ID={call.object_id}", flush=True)
    result = call.get()
    result["modal_call_id"] = call.object_id
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Retained {len(result['outputs'])} raw outputs in {target}", flush=True)
