---
name: databricks-notebook-source
description: Write, convert and review Databricks notebooks in source format (.py or .sql with "Databricks notebook source" header, COMMAND separators, MAGIC cells), versus .ipynb - plus %run, %pip, widgets, and moving logic from notebooks into importable modules. Use when the user asks to create or edit a Databricks notebook as a file, convert a notebook to a module or back, make notebooks work in Git and the IDE, or says "notebook em .py", "formato source do Databricks", "MAGIC %sql", "transformar notebook em módulo", "notebook no Cursor".
metadata:
  version: "1.0.0"
---

# Databricks Notebook Source Format

How to author notebooks as plain files in an IDE so they diff well in Git and run unchanged in the workspace.

## Format

Python source notebook:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Title

# COMMAND ----------

import pkg.transforms as t

# COMMAND ----------

df = spark.table("catalog.schema.orders")
display(t.add_net_amount(df))
```

SQL source notebook starts with `-- Databricks notebook source` and uses `-- COMMAND ----------`.

Rules:
- Line 1 is exactly the header comment. Without it the file imports as a plain script, not a notebook.
- Cells are separated by `# COMMAND ----------` on its own line, with a blank line before and after.
- Non-Python cells: every line prefixed `# MAGIC `, first line `# MAGIC %sql`, `%md`, `%sh`, `%pip`, `%run`.
- No trailing logic after the last separator that is not a cell.

## Source versus ipynb

| Prefer `.py` source | Prefer `.ipynb` |
|---|---|
| Git review, merges, AI editing, bundle deploy | Saved outputs must travel with the file |
| Notebook is an entry point calling a package | Exploratory analysis shared as a report |

Default to source. `.ipynb` stores outputs and metadata in JSON; strip outputs before commit unless the user wants them.

## Thin notebook rule

A notebook does four things: read parameters, call library code, display or write results, nothing else. Logic goes to `src/<package>/` so `pyspark-testing` can cover it and the IDE can navigate it.

Conversion notebook to module:
1. List cells; classify each as setup, logic, display.
2. Move logic cells into functions taking and returning DataFrames; no globals, no `spark` captured implicitly.
3. Replace the cell with an import and a call.
4. Run old and new on the same input; compare outputs before deleting anything.

Do not delete the original notebook content until the comparison passes.

## Parameters and magics

- Parameters: `dbutils.widgets.text("env", "dev")` then `dbutils.widgets.get("env")`. Jobs pass values as base parameters in the bundle YAML.
- `%pip install` restarts the Python process; place it in the first cell and call `dbutils.library.restartPython()` when the runtime asks. Prefer declaring dependencies in the bundle or wheel.
- `%run ./other_notebook` shares globals and hides dependencies. Prefer imports from the package. Use `%run` only for legacy code.
- `display()`, `dbutils` and `spark` exist only in the workspace or through Connect; guard them if the same file must run locally (see `databricks-local-loop`).

## Running a source notebook from the IDE

A source notebook can be uploaded and run as a one-time task with `databricks jobs submit`; the flow and polling are in `databricks-execution-compute`. For repeatable runs, reference the notebook from a job task in the bundle (`databricks-jobs`).

## Review checklist

- Header line present and exact.
- Separators well formed; no cell mixes `%sql` lines with Python.
- No secrets, tokens or hardcoded workspace URLs.
- No `.ipynb` outputs committed by accident.
- Logic extracted to the package where reasonable.
- Three-part table names and `/Volumes/` paths, not `dbfs:/` or local paths.
