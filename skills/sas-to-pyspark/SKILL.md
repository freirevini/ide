---
name: sas-to-pyspark
description: Convert SAS programs (DATA steps, PROC SQL, PROC MEANS/FREQ/SORT/TRANSPOSE/FORMAT, macros) to PySpark or Spark SQL on Databricks with the SAS semantics preserved - missing values, BY-group FIRST./LAST., RETAIN, LAG, MERGE, numeric/character coercion, formats, dates - optionally driving the sas2databricks engine when it is installed, and always finishing with a source-versus-target reconciliation. Use when the user asks to migrate, convert, port or translate SAS code to Python, PySpark, Spark SQL or Databricks, review a converted program, or says "converter SAS", "migrar SAS para PySpark", "código SAS no Databricks", "traduzir DATA step", "PROC SQL para Spark", "o resultado não bate com o SAS".
metadata:
  version: "1.0.0"
  attribution: Semantic checklist and prompt rules adapted from navintkr/sas2databricks (MIT).
---

# SAS to PySpark

A SAS program is a sequence of steps that each produce a dataset. Convert step by step, keep the dataset names, and prove every step with data. Prompt-only conversion is acceptable for the logic; it is never acceptable for the result. The result is proven in Step 5 or the work is not done.

## Step 0 - Inventory before converting

1. List every `.sas` file in scope and the order they run (autoexec, `%include`, macro libraries first).
2. For each file, list the steps: `DATA`, `PROC`, `%MACRO`, `%LET`, `%INCLUDE`. If `sas2databricks` is installed, `s2db report file.sas` gives this list with line spans (see Step 3). Otherwise do it by reading; a step ends at `RUN;` or `QUIT;`.
3. List inputs and outputs per step: librefs and tables read, tables written, external files (`INFILE`, `PROC IMPORT`, `FILENAME`), macro variables consumed.
4. Map every `libref.table` to a three-part Unity Catalog name. Ask the user for the mapping; never guess a catalog.
5. Record which steps have reference outputs available (SAS datasets, exports, listings). Reconciliation needs them. If none exist, ask the user to produce them before converting; `sas-mcp` or a SAS session can generate them.

## Step 1 - Semantics that break silently

Every item below produces a different number, not an error. Check each one in every step.

| SAS behavior | What Spark does by default | What the conversion must do |
|---|---|---|
| Missing numeric `.` is less than every number; `.` + 1 = `.`; `SUM(a, b)` ignores missing | `NULL` compares as unknown; `NULL + 1 = NULL`; `sum` ignores NULL | Filters like `x < 0` catch missing in SAS. Add `OR x IS NULL` where SAS would include the missing row. `SUM()` function versus `+` operator differ in SAS; keep the distinction. |
| Missing character is blank `''` | `NULL` and `''` are different | Decide one convention per project, usually `NULL`, and apply it on ingest. |
| Numeric/character comparison coerces implicitly, with a NOTE | Type error or `NULL` | Explicit `cast` with the SAS width and informat in mind. |
| Numbers are 8-byte doubles; `ROUND(x, .01)` rounds half away from zero | `F.round` is HALF_UP, `bround` is HALF_EVEN; decimals and doubles mix into double | Money and rates become `DecimalType`; rounding only at output; see `calculos-python`. |
| `BY` groups with `FIRST.var`/`LAST.var` depend on sort order | No implicit order | `Window.partitionBy(by).orderBy(sort keys)`, `row_number`, and the reverse window for `LAST.`. The ordering columns must reproduce the `PROC SORT` that preceded the step, including ties. |
| `RETAIN` carries a value across rows | Stateless rows | Running aggregate over an ordered window, or `last(col, ignorenulls=True)` over the window for carry-forward. |
| `LAG(x)` is a queue, not the previous row, when called conditionally | `lag` is positional | If `LAG` is inside an `IF`, the queue semantics differ; flag for manual review. |
| `MERGE a b; BY k;` is a one-to-one match within BY group, with many-to-many producing a cartesian within group plus a NOTE; `IN=` flags; later dataset overwrites common columns | SQL join semantics | Full outer join on `k` with `coalesce` in dataset order for shared columns; `IN=` becomes `IS NOT NULL` on a key from each side; many-to-many groups must be detected and reported. |
| `SET a b;` concatenates; `SET a; BY k;` interleaves | `union` needs matching columns | `unionByName(allowMissingColumns=True)`, then sort for interleave. |
| `IF ... THEN OUTPUT;` with multiple `OUTPUT` targets | One result per DataFrame | One filter per target dataset; a step with no explicit `OUTPUT` writes every row once at end of iteration. |
| `WHERE` versus subsetting `IF` | Both filters | `WHERE` filters before the step reads the row; `IF` after. Equivalent unless `FIRST.`, `RETAIN`, `_N_` or `OUTPUT` are involved. |
| `_N_`, `_ERROR_`, `STOP`, `DO UNTIL` loops over rows | No row loop | Row-iteration logic usually becomes a window or an aggregation. If it cannot, escalate to manual review with a note. Never write a Python loop over rows. |
| Dates are day counts since 1960-01-01; datetimes are seconds; `INTNX`, `INTCK`, `MDY`, formats like `DATE9.` | Spark dates are dates | Convert at ingest; `INTNX('month', d, 1, 'B')` becomes `trunc` plus `add_months`; `INTCK` boundaries count boundary crossings, not elapsed time. |
| `PROC SORT NODUPKEY` keeps the first occurrence in current order | `dropDuplicates` keeps an arbitrary one | Window with `row_number` ordered as the sort, then `row_number = 1`. |
| `PROC MEANS` with no `VAR` uses all numerics; `NWAY`, `_TYPE_`, `_FREQ_` in output | Plain aggregation | Reproduce `_TYPE_` rows only when downstream uses them; otherwise `groupBy` plus `agg` with the SAS statistic names. |
| Character truncation to declared `LENGTH` | No truncation | `substr` to the SAS length when a downstream join or key depends on it. |
| Formats applied with `PUT`/`FORMAT` change display and sometimes grouping (`PROC FREQ` groups by formatted value) | No formats | `PROC FORMAT` values become a mapping table joined or a `CASE`. Grouping by a formatted variable must group by the mapped value. |

The full construct map with code pairs is in `references/sas-pyspark-map.md`. Read it when converting a step of the matching kind.

## Step 2 - Conversion rules

- One SAS step becomes one function `DataFrame -> DataFrame` (or several inputs) in a module under `src/`, named after the SAS output dataset. Notebooks only call them. This is what `pyspark-testing` and `databricks-local-loop` expect.
- Keep a comment on every function citing the SAS file and line span.
- Macros: `%MACRO` with parameters becomes a Python function; `%LET` becomes a constant or a function argument; `%IF`/`%DO` control flow becomes Python control flow, not Spark expressions. Expand macro calls mentally before converting the body; the macro body alone is not convertible.
- Prefer Spark SQL for `PROC SQL` steps: the SQL usually passes with dialect fixes (`CALCULATED` becomes a subquery or a repeated expression; `MONOTONIC()` becomes `row_number`; remerging summary statistics means a window). Keep it as SQL text in a `spark.sql` call only when the step is pure SQL.
- Never read or write raw paths. Inputs come from Unity Catalog tables or `/Volumes/`; ingestion of CSV and Excel follows `numeric-ingestion`.
- Anything you could not translate faithfully gets a `# MANUAL REVIEW:` comment with the reason and the SAS lines. Silent approximation is the failure mode this skill exists to prevent.

## Step 3 - Optional engine: sas2databricks

If the project venv has it (`python -c "import sas2databricks"` succeeds), use it for the mechanical part. Do not install it on your own; tell the user the command and let them decide (`pip install sas2databricks`, MIT, beta, single maintainer).

```bash
s2db report path/file.sas                       # step list, engine per step, confidence, review flags
s2db convert path/file.sas --target pyspark     # deterministic conversion; low-confidence steps come back as markers
s2db convert path/file.sas --target sparksql
s2db migrate ./sas --target pyspark --out ./out --html
```

What the engine does well: step splitting, `PROC SQL` through `sqlglot`, `PROC MEANS`, `PROC FORMAT`, simple `DATA` steps, a per-step report. What it hands back to you: macros, arrays, `DO` loops, conditional `LAG`, anything it marks below confidence 0.8. Its "deterministic" layer is regular expressions and its tests are shallow, so treat its output as a draft and apply Step 1 to every generated step. The engine's `MERGE` is a `FULL JOIN USING`; verify `IN=` and many-to-many cases yourself.

Without the engine, do the same work by hand with `references/sas-pyspark-map.md`.

## Step 4 - Code review checklist for converted code

- `dropDuplicates`, `distinct`, `first()` or `collect_set` where SAS order mattered.
- `x < value` or `x != value` filters without a `NULL` clause where SAS data has missing values.
- `.cast("double")` or float literals on money, rates or anything reconciled to the cent.
- Python `for row in df.collect()` or a UDF reimplementing a `DATA` step.
- Joins on keys with different types or trailing spaces (`SAS` pads character keys).
- `groupBy` without the `_TYPE_` subset the downstream step filtered on.
- Any `# MANUAL REVIEW:` still open.

## Step 5 - Reconciliation (required)

For every output dataset, compare SAS reference against the PySpark result, in exact decimal:

| Check | How |
|---|---|
| Row count | `count()` both sides |
| Schema | column names and types after the project's type convention |
| Keys | anti-join both ways; zero rows expected |
| Numeric columns | `sum`, `min`, `max`, count of NULL per column as `DECIMAL(38, s)`; then row-level diff on the full join by key |
| Character columns | row-level diff after `trim`, since SAS pads |
| Dates | row-level diff as `date`, not as string |

Put the comparison in a pytest marked `workspace` (see `pyspark-testing`) or in a validation notebook the user runs. Differences are listed with the first rows side by side, SAS value and Spark value, and traced back to a Step 1 item. Rounding differences go to `calculos-python`. Do not adjust the target to match totals; find the cause.

Report per dataset: match, or difference with count and cause. A step without a reference output is reported as "converted, not reconciled".

## Done means

- Every step converted or marked `# MANUAL REVIEW:` with a reason.
- Unity Catalog mapping confirmed by the user.
- Reconciliation ran for every dataset with a reference; results quoted.
- Code review checklist applied; nothing from it left open.
