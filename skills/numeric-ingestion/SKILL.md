---
name: numeric-ingestion
description: Lossless ingestion contract for numeric data on Databricks - read .csv, .xlsx and source tables without silent precision loss (no inferred doubles, explicit DecimalType, Brazilian locale "1.234,56", Excel stored vs displayed values, pandas float64 traps) and prove it with a source-versus-table reconciliation right after load. Use when writing or reviewing code that reads CSV, Excel or tables with monetary, percentage or rate columns, when loaded values differ from the file by small amounts, or when the user says "importar csv/xlsx", "carregar planilha no Databricks", "diferença de arredondamento na carga", "valor diferente do arquivo", "reconciliar carga", "ler Excel no PySpark".
metadata:
  version: "1.0.0"
---

# Numeric Ingestion

Most rounding differences on Databricks are born at read time, before any calculation. This skill prevents them at the entry point. Diagnosis of differences that already exist belongs to `calculos-python`. Tests that prove the load belong to `pyspark-testing`.

Golden rule: **a numeric value enters as text and becomes `DecimalType(p, s)` through an explicit, logged conversion. It never passes through `double`.**

## Step 1 - Inventory the numeric columns

Before writing the reader, list for each numeric column: meaning (money, percentage, rate, quantity, id), max integer digits, decimal places present in the source, scale (is 9.94% stored as `9.94` or `0.0994`), and locale (`1.234,56` or `1,234.56`). Ask the user when the source does not answer. Choose `DECIMAL(p, s)` from this, with headroom in `p`. Identifiers with leading zeros or more than 15 digits (CPF, CNPJ, account) stay `string`.

## Step 2 - Read CSV as text, then convert

Never `inferSchema=True` and never rely on inference defaults, which differ between `spark.read`, `read_files` and Auto Loader. Read the numeric columns as `string`:

```python
from pyspark.sql import functions as F

raw = (spark.read
       .option("header", True)
       .option("inferSchema", False)        # everything as string
       .option("encoding", "UTF-8")         # confirm: ISO-8859-1 is common in BR exports
       .option("sep", ";")                  # confirm the real separator
       .csv("/Volumes/cat/sch/vol/file.csv"))

def br_decimal(name, p, s):
    # "1.234,56" -> "1234.56" -> DECIMAL(p, s); invalid -> NULL (counted in Step 5)
    return F.expr(
        f"try_cast(replace(replace(trim(`{name}`), '.', ''), ',', '.') AS DECIMAL({p},{s}))"
    )

df = (raw.withColumnRenamed("valor", "valor_raw")      # keep the original text
        .withColumn("valor", br_decimal("valor_raw", 18, 2)))
```

Same conversion in SQL:

```sql
SELECT try_cast(replace(replace(trim(valor), '.', ''), ',', '.') AS DECIMAL(18,2)) AS valor
FROM raw
```

Rules:
- `try_cast` returns NULL on bad input instead of failing or truncating. Count those NULLs; never drop them silently.
- Ambiguity check: in a `pt-BR` file, `1.234` is one thousand two hundred thirty-four. In `en-US` it is one point two. Confirm locale per file, not per project.
- Casting a string with more decimals than `s` rounds it (HALF_UP). If the source has 4 decimals, the target scale is at least 4. Rounding at load is a business decision; record it.
- Scientific notation (`1,5E+03`) and currency symbols (`R$`) are cleaned explicitly or rejected; never left to the cast.
- Keep the original text column in bronze (`valor_raw`) so any value can be traced back.

## Step 3 - Read Excel through its stored value

Facts that cause the differences:
- Excel stores numbers as IEEE 754 doubles with 15 significant digits. The cell shows a formatted value; the file holds the stored one. `9,94%` displayed may be `0.099399999...` stored.
- Percent cells store the fraction (`0.0994`), not `9.94`.
- Dates are serial numbers unless the reader converts them.
- `pandas.read_excel` returns `float64` for numeric cells, and `spark.createDataFrame(pandas_df)` keeps `double`.

Pattern:

```python
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

pdf = pd.read_excel("/Volumes/cat/sch/vol/file.xlsx", sheet_name="Base",
                    dtype=object, engine="openpyxl")   # object: keep Python float/str, no coercion

def to_decimal(x, scale):
    if x is None or (isinstance(x, float) and x != x):  # None or NaN
        return None
    if isinstance(x, float):
        x = format(x, ".15g")                            # Excel's 15 significant digits, not the binary expansion
    # explicit HALF_UP: quantize defaults to HALF_EVEN, which differs from Spark cast and Excel ROUND
    return Decimal(str(x).strip()).quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)
```

Then build the Spark DataFrame with an explicit schema of `DecimalType` fields from these `Decimal` objects. Never `Decimal(float)` directly: `Decimal(0.1)` is `0.1000000000000000055511151231257827...`.

Also check:
- Hidden rows, merged cells, header not on row 1, totals rows at the bottom: drop them explicitly and log how many.
- Formula cells: `openpyxl` returns the cached result only if the file was saved by Excel; `data_only=True` and an empty result mean the cache is missing.
- Text-formatted numbers (`'0123`) arrive as `str`; route them through the same locale cleaning as CSV.

## Step 4 - Tables and conversions

- Reading from a table: keep its `DECIMAL` type. Do not `.cast("double")`, `.toPandas()` math, or a Python UDF returning `float` in between.
- `toPandas()` turns `DecimalType` into Python `Decimal` objects (object dtype). Arrow may convert differently by version; check the dtype instead of assuming.
- Joining or unioning a `DECIMAL` column with a `double` column promotes the result to `double`. Align types before the join.

## Step 5 - Reconcile immediately after load

A load is done only when this report matches. Compute the source side from the raw text, the target side from the loaded table, both in exact decimal:

| Check | Source (raw text) | Target (table) |
|---|---|---|
| Rows | data rows in the file minus explicitly dropped rows | `count(*)` |
| NULL or rejected per numeric column | empty cells | `count_if(col IS NULL)` |
| Sum per numeric column | `sum(try_cast(cleaned AS DECIMAL(38, s)))` | `sum(col)` |
| Min and max per numeric column | same | same |

Any difference: stop, show the first differing rows side by side (raw text, converted value), and hand off to `calculos-python` if the cause is not obvious. Never "fix" a reconciliation by rounding the totals.

## Code review checklist

Flag these patterns in any Databricks reading code:

- `inferSchema=True`, `inferColumnTypes` left implicit, or no schema on CSV/JSON with numeric columns
- `.cast("double")`, `.cast("float")`, `DoubleType()`, `FloatType()` on money, percent or rate
- `pd.read_excel(...)` without `dtype`, followed by `spark.createDataFrame(pdf)`
- `Decimal(some_float)`
- `round()` or `F.round()` before the last step
- Python UDF returning `float` on a decimal column
- Locale cleaning done with a single `replace(",", ".")` (breaks thousands separators)
- No reconciliation after load

## Report

- Column inventory: name, chosen `DECIMAL(p, s)`, locale, scale convention.
- Rejected values: count and sample per column.
- Reconciliation table with match or difference per check.
- Decisions the user made (rounding at load, dropped rows).
