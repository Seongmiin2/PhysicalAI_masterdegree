"""Local, opt-in operational router using an actually fine-tuned LoRA classifier."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time

from .base import GenerationRequest, Provider

ACTIONS = ["INVESTIGATE_FAILURE", "MONITOR_RUNNING", "RESUME_INCOMPLETE",
           "REVIEW_COMPLETED", "REQUIRE_HUMAN_REVIEW"]
ROOT = Path(__file__).resolve().parents[1]


def record_text(record: dict) -> str:
    """Use input evidence only; exclude labels, teacher messages and provenance."""
    if "messages" in record:
        return "\n".join(m["content"] for m in record["messages"] if m["role"] == "user")
    if isinstance(record.get("text"), str):
        return record["text"]
    return json.dumps({k: v for k, v in record.items()
                       if k not in {"label", "split", "provenance", "next_action"}},
                      ensure_ascii=False, sort_keys=True)


class FineTunedProvider(Provider):
    def __init__(self, adapter_path=None, device=None):
        self.adapter_path = Path(adapter_path or os.getenv(
            "CHUM_FINETUNED_ADAPTER", str(ROOT / "outputs/harness/models/chum-ops-lora")))
        self.device_name = device or os.getenv("CHUM_FINETUNED_DEVICE", "cpu")
        self._model = None
        self._tokenizer = None

    def _load(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from peft import PeftModel
        metadata = json.loads((self.adapter_path / "router_config.json").read_text(encoding="utf-8"))
        base = metadata["base_model_path"]
        self.max_length = metadata["max_length"]
        self.labels = metadata["labels"]
        self.preprocessing = metadata.get("preprocessing", "raw")
        if self.preprocessing not in {"raw", "normalized"}:
            raise ValueError("Unsupported adapter preprocessing")
        if self.labels != ACTIONS:
            raise ValueError("Adapter action schema mismatch")
        self._tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True, trust_remote_code=False)
        self._tokenizer.pad_token = self._tokenizer.eos_token
        dtype = torch.bfloat16 if self.device_name.startswith("cuda") else torch.float32
        model = AutoModelForSequenceClassification.from_pretrained(
            base, num_labels=len(ACTIONS), torch_dtype=dtype, local_files_only=True,
            trust_remote_code=False, attn_implementation="sdpa")
        model.config.pad_token_id = self._tokenizer.pad_token_id
        self._model = PeftModel.from_pretrained(model, str(self.adapter_path), local_files_only=True)
        self._model.to(self.device_name).eval()

    def route(self, record: dict) -> dict:
        import torch
        started = time.perf_counter()
        if self.device_name == "cpu":
            torch.set_num_threads(4)
        cold_load = self._model is None
        if cold_load:
            self._load()
        load_seconds = time.perf_counter() - started if cold_load else 0.0
        inference_started = time.perf_counter()
        from .ops_features import inference_text
        encoded = self._tokenizer(inference_text(record, self.preprocessing), return_tensors="pt", truncation=True,
                                  max_length=self.max_length).to(self.device_name)
        with torch.inference_mode():
            probabilities = self._model(**encoded).logits.float().softmax(-1)[0].cpu().tolist()
        index = max(range(len(probabilities)), key=probabilities.__getitem__)
        return {"next_action": self.labels[index], "confidence": probabilities[index],
                "confidence_calibrated": False, "preprocessing": self.preprocessing, "probabilities": dict(zip(self.labels, probabilities)),
                "needs_human_review": True, "authorizes_execution": False,
                "provenance": "LOCAL_FINETUNED_SUGGESTION", "model": str(self.adapter_path),
                "latency_seconds": time.perf_counter() - started,
                "cold_load": cold_load, "load_seconds": load_seconds,
                "inference_seconds": time.perf_counter() - inference_started}

    def generate(self, request: GenerationRequest) -> dict:
        result = self.route(request.context.get("record", request.context))
        return result | {"agent": request.agent, "summary": "Experimental trained operational routing suggestion",
                         "recommendation": result["next_action"], "citations": []}
