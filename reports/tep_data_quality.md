# TEP Pilot Data Quality

Status: **BLOCKED — not generated**

No real Mode 1 run has been downloaded, so row counts, run counts, variable
statistics, fault distribution, and fault onset cannot be truthfully reported.

The official API exposes Mode 1 as one 23,924,710,848-byte HDF5 file rather than
individual run objects. The repository currently has no smaller official pilot
file. This report must be regenerated with `python -m src.data.tep_quality` after
a real canonical pilot Parquet file has been produced.

No baseline was run because the task explicitly requires Data Quality validation
to finish first.
