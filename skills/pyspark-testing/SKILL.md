---
name: pyspark-testing
description: Write and run pytest tests for PySpark and Databricks code - pure transformation functions, SparkSession fixtures (local vs Databricks Connect), small synthetic DataFrames, DataFrame equality assertions, marking tests that need a workspace. Use when the user asks to test PySpark or Databricks code, add unit tests for a transformation, set up pytest for Spark, or says "testar PySpark", "teste unitário Databricks", "pytest com Spark", "comparar DataFrames", "testar sem workspace".
metadata:
  version: "1.1.0"
---

# PySpark Testing

Make Spark logic testable by design, then test it with pytest. Pairs with `test-driven-development` (cycle) and `verification-planning` (evidence). This skill supplies the Spark-specific parts.

## Principle

Test transformations, not I/O. A function `DataFrame -> DataFrame` with no reads, writes or `spark.table()` inside is testable with 5 rows. I/O wrappers stay thin and are covered by one integration test.

```python
# src/pkg/transforms.py
from pyspark.sql import DataFrame, functions as F

def add_net_amount(df: DataFrame) -> DataFrame:
    return df.withColumn("net", F.col("gross") - F.col("tax"))
```

If existing code mixes I/O and logic, extract the logic first; do not test through the I/O.

## Session fixture

Choose one mode per project and record it in `tests/conftest.py`.

| Mode | When | Trade-off |
|---|---|---|
| Local Spark (`pyspark` installed) | Logic tests, CI without workspace | Fast, offline. Behavior can differ from Databricks runtime |
| Databricks Connect | Needs real runtime, UC tables, or serverless semantics | Needs auth and network; slower; costs compute |

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession
    s = (SparkSession.builder.master("local[1]")
         .config("spark.sql.shuffle.partitions", "1")
         .config("spark.ui.enabled", "false")
         .getOrCreate())
    yield s
    s.stop()
```

For Connect use `DatabricksSession.builder.profile("<PROFILE>").serverless(True).getOrCreate()` with an explicit profile. Local `pyspark` and `databricks-connect` conflict in one venv; use separate environments or only Connect. Check this before installing anything.

## Writing tests

- Build inputs with explicit schemas, not inference: `spark.createDataFrame(rows, schema)`. Inference hides type bugs (int vs long, decimal vs double).
- Keep inputs under 20 rows. One behavior per test. Name by behavior: `test_net_amount_is_gross_minus_tax`.
- Cover: nulls, empty DataFrame, duplicate keys, boundary dates, decimal rounding, columns in unexpected order.
- Assert on schema and values. Order is not guaranteed; sort or compare as sets unless the function guarantees order.

Equality helper without extra dependencies:

```python
def assert_df_equal(actual, expected, sort_by=None):
    assert actual.schema == expected.schema, f"{actual.schema} != {expected.schema}"
    a, e = actual.collect(), expected.collect()
    key = (lambda r: tuple(r[c] for c in sort_by)) if sort_by else str
    assert sorted(a, key=key) == sorted(e, key=key)
```

Spark's `pyspark.testing.assertDataFrameEqual` exists in recent PySpark and is preferred when the version allows. Libraries such as chispa are optional; add a dependency only with the user's approval.

Numeric results: compare Decimal exactly, floats with tolerance. Rounding policy is covered by `calculos-python`.

## Ingestion fidelity test

For every reader of `.csv`, `.xlsx` or a source table with numeric columns, add one
test proving the load changed no value (contract in `numeric-ingestion`):

- Fixture file in `tests/fixtures/` with edge cases: `x,5` and `x,x5` halves,
  `1.234,56` thousands, negative values, empty cell, scientific notation, value with
  more decimals than the target scale, percent cell, header and totals rows.
- Expected values written as `Decimal("...")` strings by hand, never computed with
  floats.
- Assert schema is `DecimalType(p, s)` for each numeric column, not `DoubleType`.
- Assert exact equality per row, plus row count and rejected-value count.

```python
from decimal import Decimal
from pyspark.sql.types import DecimalType

def test_csv_reader_keeps_exact_values(spark):
    df = read_vendas(spark, "tests/fixtures/vendas_br.csv")
    assert df.schema["valor"].dataType == DecimalType(18, 2)
    got = {r.id: r.valor for r in df.collect()}
    assert got == {1: Decimal("1234.56"), 2: Decimal("-0.50"), 3: None}
```

## Markers

Separate tests that need a workspace so CI and offline runs stay green.

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = ["workspace: needs a Databricks workspace (Connect, UC tables)"]
```

- Offline: `pytest -m "not workspace"`
- Full: `pytest` with the profile configured

## Streaming and pipelines

- Streaming logic: test the batch function used in `foreachBatch` with a static DataFrame. Use `availableNow` triggers for integration tests, never sleeps.
- Lakeflow pipelines: keep the transformation in plain functions; test them as above. Pipeline decorators are exercised by `bundle run` on the dev target.

## Verification

Before saying tests pass: run the command, quote the result line (`N passed`), and state which mode ran (local or Connect) and which markers were deselected. A test that never ran against the runtime proves logic, not runtime compatibility; say so.

## Anti-patterns

- Asserting `df.count() > 0` as the only check.
- Tests that read and write real prod tables.
- Session created per test (slow); keep it session-scoped.
- Sleeping to wait for streams.
- Mocking `DataFrame` methods: you test the mock, not Spark.
