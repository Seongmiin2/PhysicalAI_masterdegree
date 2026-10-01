"""Validation-selected LoRA routing with group-balanced learning and sealed test inputs.

Inputs are JSONL with text, label and provenance.group_id; text must be prepared
from evidence only by the dataset builder. This script never rewrites v1 assets.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from providers.finetuned import ACTIONS, record_text
from experiments.finetune_chum_ops import audit_splits, load_rows, validate_run_outputs


def group_balanced_weights(rows):
    counts = Counter(row["provenance"]["group_id"] for row in rows)
    return [1.0 / counts[row["provenance"]["group_id"]] for row in rows]


def class_loss_weights(rows):
    """Count independent source groups per action, not repeated epoch snapshots."""
    groups = {action: set() for action in ACTIONS}
    for row in rows:
        groups[row["label"]].add(row["provenance"]["group_id"])
    raw = [1.0 / len(groups[action]) ** 0.5 if groups[action] else 0.0 for action in ACTIONS]
    present = sum(value > 0 for value in raw)
    scale = present / sum(raw)
    return [value * scale for value in raw]


def classification_metrics(predictions):
    """Macro F1 always includes the full five-action schema."""
    classwise = {}
    for label in ACTIONS:
        tp = sum(p["expected"] == label and p["predicted"] == label for p in predictions)
        fp = sum(p["expected"] != label and p["predicted"] == label for p in predictions)
        fn = sum(p["expected"] == label and p["predicted"] != label for p in predictions)
        classwise[label] = {"support": tp + fn, "correct": tp,
                            "precision": tp / (tp + fp) if tp + fp else 0.0,
                            "recall": tp / (tp + fn) if tp + fn else 0.0,
                            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    return {"accuracy": sum(p["expected"] == p["predicted"] for p in predictions) / len(predictions),
            "macro_f1": sum(value["f1"] for value in classwise.values()) / len(ACTIONS),
            "classwise": classwise, "count": len(predictions), "predictions": predictions}


def checkpoint_improved(candidate, best):
    return best is None or (candidate["macro_f1"], -candidate["loss"]) > (best["macro_f1"], -best["loss"])


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--train", required=True)
    result.add_argument("--validation", required=True)
    result.add_argument("--test")
    result.add_argument("--final-evaluation", action="store_true")
    result.add_argument("--base", default=str(ROOT / "outputs/harness/models/qwen2.5-0.5b-instruct"))
    result.add_argument("--output", required=True)
    result.add_argument("--report", required=True)
    result.add_argument("--db", default=str(ROOT / "outputs/harness/research.sqlite3"))
    result.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    result.add_argument("--variant", choices=("coverage", "balanced"), default="balanced")
    result.add_argument("--preprocessing", choices=("raw", "normalized"), default="normalized")
    result.add_argument("--epochs", type=int, default=8)
    result.add_argument("--min-epochs", type=int, default=3)
    result.add_argument("--patience", type=int, default=2)
    result.add_argument("--max-length", type=int, default=256)
    result.add_argument("--batch-size", type=int, default=2)
    result.add_argument("--learning-rate", type=float, default=2e-4)
    result.add_argument("--head-learning-rate", type=float, default=1e-3)
    result.add_argument("--cpu-threads", type=int, default=4)
    result.add_argument("--seed", type=int, default=47)
    return result


def validate_args(args):
    validate_run_outputs(args.output, args.report, args.epochs, args.max_length, args.batch_size)
    if bool(args.test) != args.final_evaluation:
        raise ValueError("Test inputs require --final-evaluation, after the recipe has been frozen")
    if not 1 <= args.min_epochs <= args.epochs or args.patience < 1:
        raise ValueError("Require 1 <= min-epochs <= epochs and positive patience")
    if min(args.learning_rate, args.head_learning_rate, args.cpu_threads) <= 0:
        raise ValueError("Learning rates and CPU threads must be positive")
    if Path(args.output).exists() and any(Path(args.output).iterdir()):
        raise ValueError("Preserve previous runs: output directory must be empty")


def main(argv=None):
    args = parser().parse_args(argv)
    validate_args(args)
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from peft import LoraConfig, TaskType, get_peft_model, set_peft_model_state_dict
    from safetensors.torch import load_file
    from harness.store import Store

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    torch.set_num_threads(args.cpu_threads)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; use --device cpu")
    splits = {name: load_rows(getattr(args, name)) for name in ("train", "validation")}
    # Test files are neither opened nor hashed in ordinary ablation runs.
    if args.final_evaluation:
        splits["test"] = load_rows(args.test)
    audit_splits(splits)
    counts = {name: dict(Counter(row["label"] for row in rows)) for name, rows in splits.items()}
    config = vars(args) | {"rank": 8, "alpha": 16, "version": "chum-ops-lora-v2",
                          "class_loss_weights": class_loss_weights(splits["train"]),
                          "dataset_hashes": {name: hashlib.sha256(Path(getattr(args, name)).read_bytes()).hexdigest() for name in splits},
                          "trainer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    store = Store(args.db)
    task_id = "finetune-v2-" + uuid.uuid4().hex
    locked = False
    if args.device == "cuda":
        locked = store.acquire_resource("compute:gpu0", task_id)
        if not locked:
            raise RuntimeError("GPU training resource is already held")
    start = time.perf_counter()
    try:
        store.create_task(task_id, config)
        store.claim_task(task_id, task_id)
        store.append_event("finetune_started", config, task_id)
        tokenizer = AutoTokenizer.from_pretrained(args.base, local_files_only=True, trust_remote_code=False)
        tokenizer.pad_token = tokenizer.eos_token
        dtype = torch.bfloat16 if args.device == "cuda" else torch.float32
        model = AutoModelForSequenceClassification.from_pretrained(
            args.base, num_labels=len(ACTIONS), torch_dtype=dtype, local_files_only=True,
            trust_remote_code=False, attn_implementation="sdpa")
        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.use_cache = False
        model = get_peft_model(model, LoraConfig(task_type=TaskType.SEQ_CLS, r=8,
            lora_alpha=16, lora_dropout=0.05, target_modules=["q_proj", "v_proj"]))
        model.to(args.device)
        trainable = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
        initial = {name: parameter.detach().float().cpu().clone() for name, parameter in trainable}
        optimizer = torch.optim.AdamW([
            {"params": [parameter for name, parameter in trainable if "score" not in name], "lr": args.learning_rate},
            {"params": [parameter for name, parameter in trainable if "score" in name], "lr": args.head_learning_rate},
        ], weight_decay=0.01)
        loss_weights = torch.tensor(config["class_loss_weights"], device=args.device, dtype=torch.float32)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)

        def batch(rows):
            encoded = tokenizer([record_text(row) for row in rows], padding=True, truncation=True,
                                max_length=args.max_length, return_tensors="pt").to(args.device)
            return encoded, torch.tensor([ACTIONS.index(row["label"]) for row in rows], device=args.device)

        def evaluate(rows):
            model.eval()
            predictions, loss_total = [], 0.0
            started = time.perf_counter()
            with torch.inference_mode():
                for offset in range(0, len(rows), args.batch_size):
                    subset = rows[offset:offset + args.batch_size]
                    x, y = batch(subset)
                    logits = model(**x).logits.float()
                    loss_total += float(torch.nn.functional.cross_entropy(logits, y, reduction="sum"))
                    probabilities = logits.softmax(-1).cpu().tolist()
                    for row, probability in zip(subset, probabilities):
                        index = max(range(len(ACTIONS)), key=probability.__getitem__)
                        predictions.append({"group_id": row["provenance"]["group_id"],
                            "expected": row["label"], "predicted": ACTIONS[index],
                            "confidence": probability[index], "probabilities": dict(zip(ACTIONS, probability))})
            return classification_metrics(predictions) | {"loss": loss_total / len(rows),
                "latency_seconds": time.perf_counter() - started}

        history, best, best_epoch, stale = [], None, 0, 0
        generator = torch.Generator().manual_seed(args.seed)
        for epoch in range(1, args.epochs + 1):
            model.train()
            if args.variant == "balanced":
                sampler = torch.utils.data.WeightedRandomSampler(group_balanced_weights(splits["train"]),
                    num_samples=len(splits["train"]), replacement=True, generator=generator)
                rows = [splits["train"][index] for index in sampler]
            else:
                rows = list(splits["train"])
                random.shuffle(rows)
            losses = []
            for offset in range(0, len(rows), args.batch_size):
                x, y = batch(rows[offset:offset + args.batch_size])
                optimizer.zero_grad(set_to_none=True)
                logits = model(**x).logits.float()
                # Divide by sample count: weighted-mean CE cancels weights in homogeneous batches.
                loss = torch.nn.functional.cross_entropy(logits, y,
                    weight=loss_weights if args.variant == "balanced" else None, reduction="sum") / len(y)
                if not torch.isfinite(loss):
                    raise RuntimeError("Nonfinite training loss")
                loss.backward()
                torch.nn.utils.clip_grad_norm_([parameter for _, parameter in trainable], 1.0)
                optimizer.step()
                losses.append(float(loss.detach()))
            validation = evaluate(splits["validation"])
            item = {"epoch": epoch, "train_loss": sum(losses) / len(losses),
                    "validation_accuracy": validation["accuracy"], "validation_macro_f1": validation["macro_f1"],
                    "validation_loss": validation["loss"], "elapsed_seconds": time.perf_counter() - start}
            history.append(item)
            print(json.dumps(item), flush=True)
            store.append_event("finetune_epoch", item, task_id)
            if checkpoint_improved(validation, best):
                best, best_epoch, stale = validation, epoch, 0
                model.save_pretrained(output, safe_serialization=True)
            else:
                stale += 1
            if epoch >= args.min_epochs and stale >= args.patience:
                break
        set_peft_model_state_dict(model, load_file(str(output / "adapter_model.safetensors")))
        delta = sum(float((parameter.detach().float().cpu() - initial[name]).abs().sum()) for name, parameter in trainable)
        router = {"base_model_path": str(Path(args.base).resolve()), "labels": ACTIONS,
                  "max_length": args.max_length, "task": "sequence_classification",
                  "adaptation": "LoRA plus trained classification head", "version": "chum-ops-lora-v2",
                  "preprocessing": args.preprocessing, "selected_epoch": best_epoch}
        (output / "router_config.json").write_text(json.dumps(router, indent=2), encoding="utf-8")
        report = {"status": "TRAINED_EXPERIMENTAL_NOT_PRODUCTION", "task_id": task_id, "config": config,
                  "trainable_parameters": sum(parameter.numel() for _, parameter in trainable),
                  "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
                  "adapter_parameter_absolute_delta": delta,
                  "adapter_sha256": hashlib.sha256((output / "adapter_model.safetensors").read_bytes()).hexdigest(),
                  "dependencies": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "safetensors")},
                  "counts": counts, "missing_training_classes": sorted(set(ACTIONS) - set(counts["train"])),
                  "history": history, "selected_epoch": best_epoch,
                  "selection_metric": "validation macro F1; unweighted validation loss breaks ties",
                  "selected_validation": best, "production_gate": False,
                  "limitations": ["Rule-labeled examples are not independent human truth.",
                                  "Operational generalization and confidence calibration remain unproven."]}
        if args.final_evaluation:
            report["heldout_test"] = evaluate(splits["test"])
        report["elapsed_seconds"] = time.perf_counter() - start
        report["peak_gpu_memory_mb"] = torch.cuda.max_memory_allocated() / 1024**2 if args.device == "cuda" else None
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        store.append_event("finetune_evaluated", report, task_id)
        store.finish_task(task_id, task_id, result={"report": args.report, "adapter": args.output})
        print(json.dumps({"status": report["status"], "selected_epoch": best_epoch,
                          "validation_macro_f1": best["macro_f1"], "seconds": report["elapsed_seconds"]}), flush=True)
    except Exception as exc:
        store.append_event("finetune_failed", {"error": str(exc)}, task_id)
        store.finish_task(task_id, task_id, status="failed", result={"error": str(exc)})
        raise
    finally:
        if locked:
            store.release_resource("compute:gpu0", task_id)


if __name__ == "__main__":
    main()
