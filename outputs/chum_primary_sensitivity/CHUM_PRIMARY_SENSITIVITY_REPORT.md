# CHUM Primary-Cell Sensitivity Report

## Decision

**PASS**: `4/4` locked primary cells retained the uniformly applied post-hoc two-architecture robustness rule across residual block lengths 5/10/20 and conditional draw counts 1/3/10.
Git history does not establish prospective preregistration: the config, analyzer, decision JSON, and result CSVs first appear together in commit `63771cc`.

The 390 executed model-condition tasks comprise 360 perturbations (`4 cells x 2 architectures x 5 seeds x 9 settings`) and 30 shared original baselines (`3 unique faults x 2 architectures x 5 seeds`). The two fault-19 channels share the same original baseline. Therefore the cell-delta table has 360 rows while the raw fault/run tables retain all 390 tasks.

## Locked Decision Rule

Each architecture-cell must keep positive mean delta AUROC in 9/9 settings; material delta AUROC (>=0.02), >=4/5 positive seeds, and positive hierarchical run CI in at least 8/9 settings; the absolute pre-fault FPR shift must remain <=0.005 in 9/9 settings; and the reference setting block=20/draws=3 must pass all setting-level gates. Overall PASS requires both architectures to pass for all four locked cells.

## Architecture-Cell Robustness

| architecture | fault_id | channel | settings | positive_settings | material_settings | seed_stable_settings | fpr_guardrail_settings | ci_positive_settings | strict_pass_settings | min_delta_auroc | median_delta_auroc | max_delta_auroc | worst_abs_fpr_shift | reference_delta_auroc | reference_setting_pass | architecture_cell_robust |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tcn | 4 | 10 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.16527 | 0.165306 | 0.16534 | 0.00075 | 0.165285 | True | True |
| tcn | 19 | 7 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.135412 | 0.135603 | 0.135787 | 0.0015 | 0.13547 | True | True |
| tcn | 19 | 8 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.055426 | 0.055508 | 0.05554 | 0.0005 | 0.05549 | True | True |
| tcn | 25 | 2 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.289792 | 0.289938 | 0.29017 | 0.00125 | 0.289938 | True | True |
| transformer | 4 | 10 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.105497 | 0.105511 | 0.105557 | 0.00075 | 0.105502 | True | True |
| transformer | 19 | 7 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.123558 | 0.123662 | 0.123879 | 0.00075 | 0.123656 | True | True |
| transformer | 19 | 8 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.053043 | 0.053076 | 0.0531 | 0.00075 | 0.053056 | True | True |
| transformer | 25 | 2 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0.263432 | 0.264052 | 0.264422 | 0.0015 | 0.263676 | True | True |

## Cross-Architecture Consensus

| fault_id | channel | robust_architecture_count | min_delta_auroc_across_settings | median_delta_auroc_across_architectures | worst_abs_fpr_shift | two_architecture_robust |
|---|---|---|---|---|---|---|
| 4 | 10 | 2 | 0.105497 | 0.135408 | 0.00075 | True |
| 19 | 7 | 2 | 0.123558 | 0.129632 | 0.0015 | True |
| 19 | 8 | 2 | 0.053043 | 0.054292 | 0.00075 | True |
| 25 | 2 | 2 | 0.263432 | 0.276995 | 0.0015 | True |

## Interpretation Boundary

This no-retraining sensitivity test checks whether the CHUM conclusion depends on two stochastic replacement hyperparameters. It does not establish a causal controller effect, a physical root cause, or independence beyond the fixed TEP test distribution.
