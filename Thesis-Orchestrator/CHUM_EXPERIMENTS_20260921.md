# CHUM experiment extension — 2026-09-21

This package contains the completed seed-47 extension and Stage 1A training-budget experiment.

- Execution order and reasons: state/CHUM_EXPERIMENT_ROADMAP_KO.md
- Results: outputs/chum_training_budget_20260921/RESULT_SUMMARY.md
- Comparison: outputs/chum_training_budget_20260921/TRAINING_BUDGET_COMPARISON.csv
- Models and learning curves: per-model subdirectories under that output directory.

Run from Thesis-Orchestrator with the repository's research Python environment:

```powershell
python experiments/run_chum_training_budget.py --config configs/chum_training_budget.yaml
```

The feature cache is intentionally excluded from Git. Prepare data/processed/reinartz_f0_f1 in the parent repository using its existing data instructions. The split and scaler are included. Portable configs refer to the parent repository; original executed configs and their hashes are preserved under executed_configs. The model import supports both standalone and nested repository layouts.

The seed-47 channel results are included. Re-running the channel experiment additionally requires the original normal_xmv_loo_imputer_weights.npy and normal_xmv_loo_residual_bank.npy from the original CHUM environment; these are not bundled here. No new causal claims or final-paper completion claims are made. This export contains experiment code and results, not the earlier draft-writing and archive-validation work.
