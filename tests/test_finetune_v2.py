import pytest

from experiments.finetune_chum_ops_v2 import (
    ACTIONS, checkpoint_improved, classification_metrics, class_loss_weights,
    group_balanced_weights, parser, validate_args,
)


def row(label, group):
    return {"label": label, "text": "status: running", "provenance": {"group_id": group}}


def test_group_sampler_gives_each_source_equal_total_mass():
    rows = [row(ACTIONS[0], "long")] * 10 + [row(ACTIONS[1], "short")]
    weights = group_balanced_weights(rows)
    assert sum(weights[:10]) == pytest.approx(weights[10])


def test_class_loss_uses_independent_group_counts():
    rows = [row(ACTIONS[0], "a")] * 20 + [row(ACTIONS[1], str(i)) for i in range(4)]
    weights = class_loss_weights(rows)
    assert weights[0] == pytest.approx(2 * weights[1])
    assert weights[2:] == [0, 0, 0]
    assert sum(weights) == pytest.approx(2)


def test_macro_f1_exposes_majority_collapse():
    predictions = [{"expected": ACTIONS[0], "predicted": ACTIONS[0]}] * 90
    predictions += [{"expected": ACTIONS[1], "predicted": ACTIONS[0]}] * 10
    result = classification_metrics(predictions)
    assert result["accuracy"] == .9
    assert result["macro_f1"] == pytest.approx((180 / 190) / 5)
    assert result["classwise"][ACTIONS[1]]["recall"] == 0


def test_checkpoint_selection_uses_macro_f1_then_loss():
    best = {"macro_f1": .5, "loss": 1.0}
    assert checkpoint_improved({"macro_f1": .6, "loss": 2.0}, best)
    assert checkpoint_improved({"macro_f1": .5, "loss": .9}, best)
    assert not checkpoint_improved({"macro_f1": .4, "loss": .1}, best)
    assert not checkpoint_improved(best, best)
    assert checkpoint_improved(best, None)


def args_for(tmp_path, extra=()):
    return parser().parse_args(["--train", "train.jsonl", "--validation", "val.jsonl",
        "--output", str(tmp_path / "model"), "--report", str(tmp_path / "report.json"), *extra])


@pytest.mark.parametrize("extra", [("--test", "test.jsonl"), ("--final-evaluation",)])
def test_test_input_requires_explicit_final_evaluation(tmp_path, extra):
    with pytest.raises(ValueError, match="final-evaluation"):
        validate_args(args_for(tmp_path, extra))


def test_ablation_needs_no_test_file(tmp_path):
    args = args_for(tmp_path)
    validate_args(args)
    assert args.test is None
    assert args.device == "cpu"
    assert args.cpu_threads == 4


def test_rejects_inconsistent_early_stopping_budget(tmp_path):
    with pytest.raises(ValueError, match="min-epochs"):
        validate_args(args_for(tmp_path, ["--epochs", "2"]))


def test_preserves_partial_prior_run(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "router_config.json").write_text("{}")
    with pytest.raises(ValueError, match="Preserve"):
        validate_args(args_for(tmp_path))
