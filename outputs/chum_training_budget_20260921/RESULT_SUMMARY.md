# CHUM Stage 1A: training-budget experiment

Completed six seed-47 models with normal-validation checkpoint selection (maximum 50 epochs, minimum 10, patience 7). Window, model architecture and split remain fixed.

| architecture   | variant   |   epochs_run |   best_epoch |   auroc_epoch10 |   auroc_selected |   delta_auroc |   auprc_selected |   prefault_sample_fpr |   missed_run_ratio |
|:---------------|:----------|-------------:|-------------:|----------------:|-----------------:|--------------:|-----------------:|----------------------:|-------------------:|
| tcn            | F0        |           25 |           24 |        0.746339 |         0.745613 |  -0.000725433 |         0.896687 |            0.00983222 |           0.369643 |
| tcn            | F1        |           25 |           18 |        0.809665 |         0.807946 |  -0.00171842  |         0.925691 |            0.00989391 |           0.319643 |
| tcn            | F0-C      |           31 |           24 |        0.746197 |         0.745433 |  -0.000763386 |         0.896597 |            0.00977979 |           0.369643 |
| transformer    | F0        |           50 |           50 |        0.748931 |         0.749275 |   0.00034388  |         0.898671 |            0.00998335 |           0.357143 |
| transformer    | F1        |           50 |           50 |        0.807394 |         0.804357 |  -0.00303758  |         0.92466  |            0.00987232 |           0.321429 |
| transformer    | F0-C      |           50 |           50 |        0.748931 |         0.749275 |   0.00034388  |         0.898671 |            0.00998335 |           0.357143 |

These are development results on the previously observed TEP test split, not fresh external generalization evidence. Improvements and regressions are both retained. The next step is to interpret training-budget effects before changing windows or score functions.
