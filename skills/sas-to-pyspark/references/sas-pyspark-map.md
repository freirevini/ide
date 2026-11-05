# SAS to PySpark construct map

Code pairs for the constructs that appear in most SAS programs. `F` is `pyspark.sql.functions`, `W` is `pyspark.sql.Window`. Every pair assumes missing numerics were ingested as `NULL` and character blanks as `NULL`. Not executed in this repository; validate each with the reconciliation in the skill.

## DATA step basics

```sas
data out; set in; where region = 'SUL'; keep id valor; rename valor = valor_bruto; run;
```
```python
out = (in_df.filter(F.col("region") == "SUL")
       .select("id", "valor")
       .withColumnRenamed("valor", "valor_bruto"))
```

`WHERE` applies before the row enters the step; subsetting `IF` applies after. They differ only when the step uses `FIRST.`, `RETAIN`, `_N_` or `OUTPUT`.

```sas
data out; set in; if valor > 100 then faixa = 'ALTA'; else if valor > 10 then faixa = 'MEDIA'; else faixa = 'BAIXA'; run;
```
```python
out = in_df.withColumn("faixa",
    F.when(F.col("valor") > 100, "ALTA")
     .when(F.col("valor") > 10, "MEDIA")
     .otherwise("BAIXA"))
```
Trap: in SAS a missing `valor` falls into `BAIXA` because `.` is less than every number. In Spark `NULL > 10` is unknown and also falls to `otherwise`. Same result here, but `if valor < 10` includes missing in SAS and excludes it in Spark; add `| F.col("valor").isNull()` when SAS would include the row.

## SET with several datasets

```sas
data all; set a b; run;             /* concatenate */
data all; set a b; by id; run;      /* interleave, both sorted by id */
```
```python
all_df = a.unionByName(b, allowMissingColumns=True)
all_df = a.unionByName(b, allowMissingColumns=True).orderBy("id")   # interleave; order is only guaranteed at the point of use
```

## BY groups, FIRST. and LAST.

```sas
proc sort data=in; by cliente data; run;
data out; set in; by cliente;
  if first.cliente then n = 0;
  n + 1;                              /* sum statement: RETAIN implied, missing treated as 0 */
  if last.cliente then output;
run;
```
```python
w = W.partitionBy("cliente").orderBy("data")
w_desc = W.partitionBy("cliente").orderBy(F.col("data").desc())
out = (in_df
       .withColumn("n", F.row_number().over(w))
       .withColumn("_last", F.row_number().over(w_desc) == 1)
       .filter("_last").drop("_last"))
```
Ties in `data` make `row_number` nondeterministic. Add the remaining `PROC SORT` keys, or a stable tiebreaker that reproduces SAS physical order, to `orderBy`.

## RETAIN and cumulative values

```sas
data out; set in; by conta; retain saldo 0;
  if first.conta then saldo = 0;
  saldo = saldo + movimento;
run;
```
```python
w = (W.partitionBy("conta").orderBy("data")
      .rowsBetween(W.unboundedPreceding, W.currentRow))
out = in_df.withColumn("saldo", F.sum("movimento").over(w))
```
Trap: `saldo + movimento` with a missing `movimento` gives missing in SAS and the missing propagates to every later row of the group. `F.sum` skips NULL. Reproduce the SAS behavior only if the program relied on it; usually it was a bug in the SAS and the user wants `coalesce(movimento, 0)`. Ask.

Carry-forward of a value:
```sas
retain ultimo_valor; if valor ne . then ultimo_valor = valor;
```
```python
w = W.partitionBy("conta").orderBy("data").rowsBetween(W.unboundedPreceding, W.currentRow)
out = in_df.withColumn("ultimo_valor", F.last("valor", ignorenulls=True).over(w))
```

## LAG and DIF

```sas
data out; set in; by conta; anterior = lag(valor); if first.conta then anterior = .; delta = dif(valor); run;
```
```python
w = W.partitionBy("conta").orderBy("data")
out = (in_df.withColumn("anterior", F.lag("valor", 1).over(w))
       .withColumn("delta", F.col("valor") - F.col("anterior")))
```
`LAG` inside an `IF` in SAS returns the value from the last time the `LAG` call executed, not the previous row. That pattern needs `# MANUAL REVIEW:`; usually it becomes `last(..., ignorenulls=True)` over the rows that satisfied the condition.

## MERGE

```sas
data out; merge a(in=ina) b(in=inb); by id; if ina; run;
```
```python
out = (a.withColumn("_ina", F.lit(True))
        .join(b.withColumn("_inb", F.lit(True)), on="id", how="full")
        .filter(F.col("_ina").isNotNull())
        .drop("_ina", "_inb"))
```
Rules:
- Columns present in both datasets: the value from the later dataset wins when both rows exist. After the join, `coalesce(b.col, a.col)` in that order, then drop the duplicates.
- Many-to-many within a `BY` group: SAS does not produce a cartesian product; it matches row by row and reuses the last row of the shorter side. Spark join produces the product. Detect it first:
```python
dup = (a.groupBy("id").count().filter("count > 1")
        .join(b.groupBy("id").count().filter("count > 1"), "id", "inner"))
assert dup.count() == 0, "many-to-many MERGE: SAS semantics differ, review"
```
- `MERGE` without `BY` pairs rows by position; it has no Spark equivalent without an explicit row index on both sides.

## Multiple OUTPUT targets

```sas
data aprovado reprovado; set in;
  if score >= 600 then output aprovado; else output reprovado;
run;
```
```python
aprovado = in_df.filter(F.col("score") >= 600)
reprovado = in_df.filter(~(F.col("score") >= 600) | F.col("score").isNull())
```
The second filter includes NULL explicitly because SAS sends missing `score` to `reprovado` (`.` is less than 600).

## Arrays and DO loops

```sas
data out; set in; array m{12} m1-m12; total = 0;
  do i = 1 to 12; if m{i} ne . then total = total + m{i}; end; drop i;
run;
```
```python
cols = [f"m{i}" for i in range(1, 13)]
out = in_df.withColumn("total", sum(F.coalesce(F.col(c), F.lit(0)) for c in cols))
```
Unrolling works when bounds are literals and the body is column-wise. `DO WHILE`, `DO UNTIL`, loops that depend on other rows, and `_TEMPORARY_` arrays that carry across rows need manual review.

## PROC SORT

```sas
proc sort data=in out=out nodupkey; by cliente descending data; run;
```
```python
w = W.partitionBy("cliente").orderBy(F.col("data").desc())
out = (in_df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn"))
```
`NODUPKEY` keeps the first row per key in the sorted order. `dropDuplicates(["cliente"])` keeps an arbitrary row.

## PROC SQL

Most `PROC SQL` runs on Spark SQL with these edits:

| SAS SQL | Spark SQL |
|---|---|
| `CALCULATED alias` | repeat the expression or wrap in a subquery |
| `MONOTONIC()` | `row_number() over (order by <explicit order>)` |
| Summary function next to detail columns (remerge) | window function: `sum(x) over (partition by k)` |
| `SELECT DISTINCT` plus `ORDER BY` column not selected | add the column or use a subquery |
| `libref.table` | `catalog.schema.table` |
| `'01JAN2024'd` | `DATE '2024-01-01'` |
| `x ? 'abc'` or `CONTAINS` | `x LIKE '%abc%'` |
| `INTO :macrovar` | collect the value in Python and pass it as a parameter |
| `CASE` with missing: `WHEN x = . THEN` | `WHEN x IS NULL THEN` |
| Outer join with `COALESCE(a.k, b.k) AS k` | same; Spark supports it |

## PROC MEANS / SUMMARY

```sas
proc means data=in noprint nway; class regiao produto; var valor; output out=res sum=total mean=media n=qtd; run;
```
```python
res = (in_df.groupBy("regiao", "produto")
       .agg(F.sum("valor").alias("total"), F.avg("valor").alias("media"), F.count("valor").alias("qtd")))
```
Without `NWAY`, SAS also emits the subtotal rows (`_TYPE_` 0 to 3). Reproduce them with `cube` or `rollup` only if a downstream step reads `_TYPE_`. `N` counts non-missing; `F.count("valor")` also skips NULL; `F.count("*")` does not.

## PROC FREQ

```sas
proc freq data=in; tables regiao*faixa / out=freq; run;
```
```python
freq = in_df.groupBy("regiao", "faixa").count().withColumnRenamed("count", "COUNT")
```
If a `FORMAT` statement is active, SAS groups by the formatted value. Apply the format mapping before grouping.

## PROC TRANSPOSE

```sas
proc transpose data=in out=wide prefix=m; by cliente; id mes; var valor; run;
```
```python
wide = in_df.groupBy("cliente").pivot("mes").agg(F.first("valor"))
wide = wide.select("cliente", *[F.col(c).alias(f"m{c}") for c in wide.columns if c != "cliente"])
```
`F.first` without an order is nondeterministic when a `cliente` and `mes` pair has more than one row. SAS would have warned and taken the last; verify uniqueness first.

## PROC FORMAT

```sas
proc format; value faixa low-<10 = 'BAIXA' 10-<100 = 'MEDIA' 100-high = 'ALTA'; run;
```
```python
def fmt_faixa(col):
    return (F.when(col < 10, "BAIXA").when(col < 100, "MEDIA").when(col >= 100, "ALTA"))
```
Lookup formats with many values become a mapping table joined on the raw value. Keep `low` and `high` bounds and the `-<` exclusive edge.

## Dates

| SAS | PySpark |
|---|---|
| `today()` | `F.current_date()` |
| `mdy(m, d, y)` | `F.make_date(y, m, d)` |
| `intnx('month', d, 1, 'b')` | `F.trunc(F.add_months(d, 1), "month")` |
| `intnx('month', d, 0, 'e')` | `F.last_day(d)` |
| `intck('month', d1, d2)` | `F.months_between(F.trunc(d2, "month"), F.trunc(d1, "month"))` cast to int, because `INTCK` counts boundaries |
| `intck('day', d1, d2)` | `F.datediff(d2, d1)` |
| `put(d, yymmddn8.)` | `F.date_format(d, "yyyyMMdd")` |
| `input(s, ddmmyy10.)` | `F.to_date(s, "dd/MM/yyyy")` |
| `datepart(dt)` | `F.to_date(dt)` |
| `year(d)`, `month(d)` | `F.year(d)`, `F.month(d)` |

SAS dates stored as numbers in a table are days since 1960-01-01: `F.date_add(F.lit("1960-01-01"), F.col("sasdate").cast("int"))`.

## Character functions

| SAS | PySpark |
|---|---|
| `trim(left(s))` or `strip(s)` | `F.trim(s)` |
| `compress(s)` | `F.regexp_replace(s, r"\s", "")` |
| `compress(s, , 'kd')` | `F.regexp_replace(s, r"[^0-9]", "")` |
| `substr(s, 1, 3)` | `F.substring(s, 1, 3)` |
| `scan(s, 2, ',')` | `F.split(s, ",")[1]` |
| `catx(' ', a, b)` | `F.concat_ws(" ", a, b)` (both skip NULL) |
| `upcase(s)` | `F.upper(s)` |
| `index(s, 'x') > 0` | `F.instr(s, "x") > 0` |
| `tranwrd(s, 'a', 'b')` | `F.replace(s, "a", "b")` |
| `put(n, z6.)` | `F.lpad(n.cast("string"), 6, "0")` |
| `input(s, 8.)` | `F.col(s).cast("decimal(p, s)")` with explicit precision |

SAS character comparison ignores trailing blanks. Trim keys before joins and comparisons.

## Numeric functions

| SAS | PySpark | Note |
|---|---|---|
| `sum(a, b, c)` | `F.coalesce(a, 0) + F.coalesce(b, 0) + ...` or a guarded sum | SAS `SUM()` ignores missing; `a + b` propagates missing in both systems |
| `round(x, .01)` | `F.round(x, 2)` | both half away from zero; keep `DecimalType` |
| `int(x)` | `F.col(x).cast("long")` for positive; `F.when(x < 0, F.ceil(x)).otherwise(F.floor(x))` in general | `INT` truncates toward zero |
| `floor`, `ceil` | same | |
| `mean(a, b)` | `(coalesce sum) / (count of non-null)` | SAS ignores missing operands |
| `nmiss(a, b)` | sum of `isNull` casts | |
| `x ** 2` | `F.pow(x, 2)` | |
| `mod(a, b)` | `a % b` | sign follows SAS for positive operands; check negatives |
