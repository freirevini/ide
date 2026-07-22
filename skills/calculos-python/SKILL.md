---
name: calculos-python
description: Review numeric calculations for decimal rounding integrity across Python, PySpark/Databricks, BigQuery, and Excel sources. Use when the user asks to review, validate, or debug calculations (division, trends, means, weighted means, outlier-trimmed means, subtractive derivation, percentage multiplication) where rounding differences between steps could change final results.
---

# Cálculos Python — Rounding Integrity Review

Review calculations end-to-end so that NO rounding difference between steps affects
final results. Golden rule the code must always follow:

> **Carry full precision through every intermediate step. Round ONLY at the final
> presentation/output step.** Never feed a rounded value into a subsequent calculation.

## Calculation scope
- Division and ratios; trends.
- Simple and weighted means; both variants with outlier removal (document the
  outlier criterion — IQR, z-score, percentile — since it changes the input set).
- Subtractive derivation, e.g. `100% - result_x - result_y = 99.94%`: verify the
  residual is computed from UNROUNDED components; rounded components make the parts
  not sum back to 100%.
- Multiplication using variables that hold percentage results (confirm scale:
  0.0994 vs 9.94 — a 100x error hides here).
- Intermediate results consumed by subsequent calculations (the critical path for
  rounding drift).

## Step 1 — Investigate how each technology rounds
Map, for every source and tool in the pipeline, how values are stored and rounded:

| Tech | Key behaviors to check |
|---|---|
| Python | `float` is IEEE 754 double; built-in `round()` uses banker's rounding (half-to-even: `round(2.5) == 2`); `decimal.Decimal` allows explicit context (`ROUND_HALF_UP`, precision) |
| PySpark / Databricks | `F.round()` = HALF_UP, `F.bround()` = HALF_EVEN — different results on .5; `DecimalType(precision, scale)` truncates/rounds on cast; watch silent casts to double in UDFs |
| BigQuery | `NUMERIC` (scale 9) / `BIGNUMERIC` are exact; `FLOAT64` is IEEE 754; `ROUND()` rounds half away from zero; check the column type actually used by the reader |
| Excel | 15 significant digits; `ROUND()` half away from zero; displayed value ≠ stored value; "Precision as displayed" setting may have physically rounded the data |

Direction to enforce in code: read/ingest the FULL value (no rounding at read time,
no lossy casts), compute with full precision, apply rounding only afterwards, at output.

## Step 2 — Research precision particularities
For the specific versions/connectors in use, check how data crosses boundaries:
BigQuery → pandas/PySpark reader type mapping (NUMERIC to decimal vs float64),
Excel → pandas (`openpyxl` reads stored value, not displayed), Spark ↔ pandas
conversions, and any schema with DecimalType scale smaller than the data's.
Flag every point where a value silently changes type or scale.

## Step 3 — Test and compare
1. Reproduce the calculation per source/tool combination on the same input sample.
2. Compare results at EACH intermediate step, not just the final number — locate the
   exact step where values diverge and by how much.
3. Show both values side by side with full precision (print 15+ digits, not the
   rounded display).

## Step 4 — Iterate until exact
Repeat Steps 1-3, fixing one divergence at a time (usually: an early `round()`, a
lossy cast, a HALF_UP vs HALF_EVEN mismatch, or float accumulation), until results
match the exact values the user provided. If the user's target values cannot be
reproduced by any consistent rounding policy, report which policy produces which
value and raise it as an open question instead of forcing a match.

## Final report
- Pipeline map: source → transformations → output, with type/scale at each hop.
- Divergences found: step, cause, magnitude, fix applied.
- Rounding policy adopted (mode, decimal places, applied only at output).
- Evidence: side-by-side values per tool before/after the fix.
