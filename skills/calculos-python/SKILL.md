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

## Step 1b — Databricks and Spark traps
Check each of these explicitly; they produce differences in the last decimal places
that survive code review:

- **Decimal arithmetic precision.** `DECIMAL(p1,s1) * DECIMAL(p2,s2)` has precision
  `p1+p2+1` and scale `s1+s2`; division widens the scale further. When the result
  exceeds precision 38, Spark reduces the scale (keeping at least 6) while
  `spark.sql.decimalOperations.allowPrecisionLoss` is true (default). Chained
  multiplications of wide decimals lose digits silently. Fix: cast operands to the
  narrowest `DECIMAL(p, s)` the data needs before multiplying, and check the result
  type with `df.schema` or `typeof()`.
- **Decimal mixed with double.** Any expression combining `DECIMAL` and `DOUBLE`
  (literal `1.5` in Python, `float` column, `F.lit(0.1)`) is computed as `DOUBLE`.
  Fix: `F.lit(Decimal("0.1"))` or `CAST('0.1' AS DECIMAL(...))`.
- **Non-deterministic double sums.** `sum`/`avg` over `DOUBLE` adds in partition
  order, which changes between runs and cluster sizes; the last digits drift. Exact
  totals require `DECIMAL`.
- **`F.round` vs `F.bround`.** `round` is HALF_UP (away from zero, same as Excel
  `ROUND` and BigQuery `ROUND`); `bround` is HALF_EVEN (same as Python built-in
  `round`). Pick one policy per output and use it everywhere.
- **Rounding at load.** Casting a string with more decimals than the target scale
  rounds it. The difference appears at ingestion, not in the calculation. See
  `numeric-ingestion`.
- **Python round-trips.** `toPandas()`, Python UDFs returning `float`, and
  `Decimal(float)` each change values. Look for them in the critical path.

Code patterns to grep for first: `inferSchema=True`, `.cast("double")`,
`DoubleType()`, `FloatType()`, `F.round(` or `round(` before the final step,
`F.lit(` with a float literal, `@udf` returning float, `.toPandas()` followed by math,
`Decimal(` applied to a float.

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
