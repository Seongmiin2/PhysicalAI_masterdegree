# Extended Tennessee Eastman Data Specification

Source: DTU Figshare article `13385936`, version 1. Evidence used here is limited
to the public article API response and the official `Readme.html` (MD5 verified).
Unknown fields are intentionally not inferred.

## Files and naming

- Six HDF5 files: `TEP_Mode1.h5` through `TEP_Mode6.h5`.
- One file corresponds to one initial production mode.
- Each mode file is approximately 23–24 GB; Mode 1 is 23,924,710,848 bytes.
- All mode files use the same hierarchy.
- Fault group example: `Mode1/SingleFault/SimulationCompleted/IDV1/Mode1_IDVInfo_1_100/Run1`.
- Fault magnitude suffixes documented for IDV1: `100`, `75`, `50`, `25` percent.
- Repetition/run names use `Run1`, `Run2`, ... . The article says each fault is
  simulated 500 times with different random seeds.

## Operating mode

- Modes: 1–6.
- `TEP_Mode1.h5` contains simulations whose initial condition is Mode 1.
- Mode-transition simulations are grouped separately under `ModeTransition`.

## Fault ID and outcome grouping

- Single faults are named `IDV1` through `IDV28`.
- Runs are separated into `SimulationCompleted` and `SimulationStopped`.
- `SimulationStopped` means inputs triggered an emergency shutdown.
- Exact physical meaning of each IDV: **UNKNOWN from README**.
- Abrupt versus gradual/incipient classification: **UNKNOWN from README**.

## Fault onset

- Per-run fault profile data is stored in `idv_init`.
- Exact onset time/sample: **UNKNOWN until a run dataset is inspected**.
- No fixed onset is assumed by the loader or experiment design.

## Sampling and duration

- Sampling interval: 3 minutes.
- Simulation duration: 100 hours.
- Expected nominal sample count from those two facts: 2,000; this is an
  arithmetic expectation, not a confirmed run shape.

## Process variables

Each run includes `processdata`, described as time plus measured and manipulated
variables from the original Tennessee Eastman publication.

- Labels are stored in root dataset `Processdata_Labels`.
- Canonical measured-variable targets: `XMEAS_01` ... `XMEAS_41`.
- Canonical manipulated-variable candidates: `XMV_01` ... `XMV_12`.
- Exact source label strings and order: **UNKNOWN until HDF5 labels are read**.
- `additional_meas`, `economic_data`, `setpoint_init`, `idv_init`, and
  `time_info` are separate datasets. They are not model inputs in this pilot.

Semantic roles:

| Source | Canonical role |
|---|---|
| XMEAS | STATE |
| past XMV | ACTION_CANDIDATE |
| initial mode | CONTEXT |
| IDV | LABEL |

Future XMV is never used as an input.

## Normal-run structure

- Dedicated normal-run path/name: **UNKNOWN from README**.
- Setpoint variation and mode-transition groups are documented, but they must not
  be silently treated as normal steady-state runs.
- A normal-training selection cannot be finalized until Mode 1 hierarchy and run
  metadata are available.

## Pilot acquisition status

The public API exposes Mode 1 only as a single 23.9 GB object; it does not expose
individual runs as downloadable files. HTTP byte ranges work, but remote HDF5
metadata traversal did not complete within two minutes at the observed transfer
rate. No TLS verification was disabled and no full mode file was downloaded.

Consequently, abrupt/incipient fault selection and real-run extraction remain
blocked pending one of:

1. a locally supplied `TEP_Mode1.h5`, or
2. a smaller official Mode 1 subset published by the source.
