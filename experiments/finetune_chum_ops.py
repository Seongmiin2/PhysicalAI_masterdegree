"""Fine-tune a pretrained Qwen backbone with LoRA for observed-state routing.

Split by source run before training. Test labels are used once for final reporting,
never checkpoint selection. All outputs are operational suggestions, not evidence.
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


def load_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    for row in rows:
        if "label" not in row:
            answer = next(m["content"] for m in row["messages"] if m["role"] == "assistant")
            row["label"] = json.loads(answer)["next_action"]
        if row["label"] not in ACTIONS or not record_text(row).strip():
            raise ValueError("Invalid routing label or empty evidence input")
    return rows


def audit_splits(splits):
    seen = {}
    for name, rows in splits.items():
        if not rows:
            raise ValueError(f"Empty {name} split")
        for row in rows:
            group = row.get("provenance", {}).get("group_id")
            if not group:
                raise ValueError("Every sample needs source-run group_id")
            if group in seen and seen[group] != name:
                raise ValueError(f"Source-run leakage: {group}")
            seen[group] = name


def validate_run_outputs(output, report, epochs, max_length, batch_size):
    if min(epochs, max_length, batch_size) < 1:
        raise ValueError("Training budgets must be positive")
    if (Path(output) / "adapter_model.safetensors").exists() or Path(report).exists():
        raise ValueError("Preserve previous runs: choose new --output and --report paths")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--test", required=True)
    parser.add_argument("--base", default=str(ROOT / "outputs/harness/models/qwen2.5-0.5b-instruct"))
    parser.add_argument("--output", default=str(ROOT / "outputs/harness/models/chum-ops-lora"))
    parser.add_argument("--report", default=str(ROOT / "outputs/chum_ops_training_20261001/TRAINING_REPORT.json"))
    parser.add_argument("--db", default=str(ROOT / "outputs/harness/research.sqlite3"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()
    validate_run_outputs(args.output, args.report, args.epochs, args.max_length, args.batch_size)
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from peft import LoraConfig, TaskType, get_peft_model
    from harness.store import Store
    torch.manual_seed(47); random.seed(47)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required for this bounded training run")
    splits = {name: load_rows(getattr(args, name)) for name in ("train", "validation", "test")}
    audit_splits(splits)
    store = Store(args.db)
    task_id = "finetune-" + uuid.uuid4().hex
    owner = task_id
    if not store.acquire_resource("compute:gpu0", owner):
        raise RuntimeError("GPU training resource is already held")
    config = vars(args) | {"seed": 47, "rank": 8, "alpha": 16,
                         "dataset_hashes": {name: hashlib.sha256(Path(getattr(args, name)).read_bytes()).hexdigest() for name in splits}}
    store.create_task(task_id, config)
    store.claim_task(task_id, owner)
    start = time.perf_counter()
    try:
        store.append_event("finetune_started", config, task_id)
        tokenizer = AutoTokenizer.from_pretrained(args.base, local_files_only=True, trust_remote_code=False)
        tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForSequenceClassification.from_pretrained(
            args.base, num_labels=len(ACTIONS), torch_dtype=torch.bfloat16,
            local_files_only=True, trust_remote_code=False, attn_implementation="sdpa")
        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.use_cache = False
        model = get_peft_model(model, LoraConfig(task_type=TaskType.SEQ_CLS, r=8,
                 lora_alpha=16, lora_dropout=0.05, target_modules=["q_proj", "v_proj"]))
        model.to("cuda")
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=2e-4)
        output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
        initial = {name: p.detach().float().cpu().clone() for name,p in model.named_parameters() if p.requires_grad}
        def batch(rows):
            encoded = tokenizer([record_text(r) for r in rows], padding=True, truncation=True,
                                 max_length=args.max_length, return_tensors="pt").to("cuda")
            return encoded, torch.tensor([ACTIONS.index(r["label"]) for r in rows], device="cuda")
        def evaluate(rows):
            model.eval(); predictions=[]; correct=0; started=time.perf_counter()
            with torch.inference_mode():
                for offset in range(0,len(rows),args.batch_size):
                    subset=rows[offset:offset+args.batch_size]; x,y=batch(subset)
                    pred=model(**x).logits.argmax(-1).tolist()
                    for row,index in zip(subset,pred):
                        predictions.append({"group_id":row["provenance"]["group_id"],
                                            "expected":row["label"],"predicted":ACTIONS[index]})
                        correct += ACTIONS[index] == row["label"]
            return {"accuracy":correct/len(rows),"count":len(rows),"latency_seconds":time.perf_counter()-started,
                    "predictions":predictions}
        history=[]; best=-1
        for epoch in range(args.epochs):
            model.train(); rows=list(splits["train"]); random.shuffle(rows); losses=[]
            for offset in range(0,len(rows),args.batch_size):
                x,y=batch(rows[offset:offset+args.batch_size]); optimizer.zero_grad(set_to_none=True)
                loss=model(**x,labels=y).loss
                if not torch.isfinite(loss): raise RuntimeError("Nonfinite training loss")
                loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); optimizer.step()
                losses.append(float(loss.detach()))
            validation=evaluate(splits["validation"])
            item={"epoch":epoch+1,"loss":sum(losses)/len(losses),"validation_accuracy":validation["accuracy"]}
            history.append(item); print(json.dumps(item),flush=True)
            store.append_event("finetune_epoch",item,task_id)
            if validation["accuracy"] > best:
                best=validation["accuracy"]; model.save_pretrained(output,safe_serialization=True)
        # Reload validation-selected weights before the one held-out test evaluation.
        from safetensors.torch import load_file
        from peft import set_peft_model_state_dict
        set_peft_model_state_dict(model,load_file(str(output/"adapter_model.safetensors")))
        test=evaluate(splits["test"])
        test["classwise"] = {label: {
            "support": sum(r["expected"] == label for r in test["predictions"]),
            "correct": sum(r["expected"] == label and r["predicted"] == label for r in test["predictions"]),
        } for label in ACTIONS}
        delta=sum(float((p.detach().float().cpu()-initial[name]).abs().sum()) for name,p in model.named_parameters() if name in initial)
        router={"base_model_path":str(Path(args.base).resolve()),"labels":ACTIONS,"max_length":args.max_length,
                "task":"sequence_classification","adaptation":"LoRA plus trained classification head"}
        (output/"router_config.json").write_text(json.dumps(router,indent=2),encoding="utf-8")
        counts={name:dict(Counter(r["label"] for r in rows)) for name,rows in splits.items()}
        majority=Counter(r["label"] for r in splits["train"]).most_common(1)[0][0]
        report={"status":"TRAINED_EXPERIMENTAL_NOT_PRODUCTION","task_id":task_id,"config":config,
                "base":"Qwen/Qwen2.5-0.5B-Instruct","trainable_parameters":trainable,"total_parameters":total,
                "adapter_parameter_absolute_delta":delta,"adapter_sha256":hashlib.sha256((output/"adapter_model.safetensors").read_bytes()).hexdigest(),
                "production_gate": False, "production_gate_reason": "Small rule-labeled dataset with missing action classes; human-reviewed experimental use only.",
                "dependencies":{name:importlib.metadata.version(name) for name in ("torch","transformers","peft","accelerate","safetensors")},
                "counts":counts,"missing_training_classes":sorted(set(ACTIONS)-set(counts["train"])),
                "history":history,"selected_validation_accuracy":best,"heldout_test":test,
                "majority_baseline_test_accuracy":sum(r["label"]==majority for r in splits["test"])/len(splits["test"]),
                "deterministic_label_rule_baseline":"Labels are generated by observed-state rules. On covered states their generating rule is an oracle baseline; learned model cannot claim an advantage over it.",
                "elapsed_seconds":time.perf_counter()-start,"peak_gpu_memory_mb":torch.cuda.max_memory_allocated()/1024**2,
                "limitations":["Small source-run grouped project dataset; no operational generalization claim.","Confidence uncalibrated; human review always required.","No efficiency improvement established over deterministic rules."]}
        Path(args.report).parent.mkdir(parents=True,exist_ok=True)
        Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        store.append_event("finetune_evaluated",report,task_id); store.finish_task(task_id,owner,result={"report":args.report,"adapter":args.output})
        print(json.dumps({"status":report["status"],"test_accuracy":test["accuracy"],"adapter_delta":delta,"seconds":report["elapsed_seconds"]}),flush=True)
    except Exception as exc:
        store.append_event("finetune_failed",{"error":str(exc)},task_id)
        store.finish_task(task_id,owner,status="failed",result={"error":str(exc)})
        raise
    finally:
        store.release_resource("compute:gpu0",owner)


if __name__ == "__main__":
    main()
