---
name: databricks-local-loop
description: Develop Databricks projects locally in Cursor, Antigravity or any AI IDE and reflect them in the workspace - project layout, dev target, the edit-run-deploy inner loop (Databricks Connect, bundle deploy/run, sync), and what differs between local and workspace. Use when the user asks to develop Databricks code locally, connect the IDE to Databricks, run or deploy local changes to the workspace, set up a Databricks project from scratch, or says "desenvolver local", "conectar a IDE ao Databricks", "refletir no workspace", "deploy do projeto", "rodar no cluster pelo Cursor/Antigravity".
metadata:
  version: "1.0.0"
---

# Databricks Local Loop

Orchestrates the inner loop: edit locally, run on Databricks compute, deploy as a bundle. It owns the order of steps and the decisions. Details live in other skills; load them at the step that needs them.

## Load order

1. `databricks-core` first: CLI install, auth, profile. Never use an implicit default profile; ask which one.
2. `databricks-setup-local`: local `.venv` with uv and Databricks Connect.
3. `databricks-execution-compute`: run code on serverless or a cluster.
4. `databricks-dabs`: validate, deploy, run the bundle.
5. Product skill for the resource (`databricks-jobs`, `databricks-pipelines`, `databricks-apps`, `databricks-aibi-dashboards`).
6. `pyspark-testing` and `databricks-notebook-source` when tests or notebooks are involved.

## Step 0 - Classify the situation

| Situation | Action |
|---|---|
| Empty folder | Scaffold with `databricks bundle init` (see `databricks-dabs`), then Step 1 |
| Repo exists with `databricks.yml` | Run `databricks bundle validate --strict -t dev`, then Step 1 |
| Repo without bundle | Ask before adding `databricks.yml`; do not move existing files |
| Workspace has the resource, repo does not | `databricks bundle generate job|pipeline|dashboard|app <id>` pulls it into the repo |

## Step 1 - Layout

Keep logic out of notebooks. Notebooks and job entry points stay thin.

```
databricks.yml        bundle root, targets: dev, prod
resources/            one YAML per job/pipeline/app/dashboard
src/<package>/        pure transformation functions, importable and testable
notebooks/            thin entry points (source format, see databricks-notebook-source)
tests/                pytest, see pyspark-testing
pyproject.toml        runtime deps plus dev extras (databricks-connect, pytest, ruff)
```

If the repo already has a layout, follow it. Do not reorganize without being asked.

## Step 2 - Connect the IDE

1. `databricks auth describe --profile <PROFILE>` confirms auth.
2. `databricks-setup-local` previews, then provisions the `.venv`. The Databricks Connect version must match the target runtime or serverless; mismatch is the top cause of confusing errors.
3. Point the IDE interpreter at `.venv`. Same steps in Cursor and Antigravity: select interpreter, run tests from the terminal.
4. Tell the user which profile and target were used. Write nothing into `~/.databrickscfg` without consent.

## Step 3 - The loop

Pick the fastest mode that answers the question.

| Need | Mode | Cost |
|---|---|---|
| Does this transformation work on real data? | Databricks Connect: local Python, remote Spark | seconds |
| Does this notebook run as a task? | `databricks jobs submit` of a source notebook (`databricks-execution-compute`) | tens of seconds |
| Does the whole job/pipeline run with real config? | `databricks bundle deploy -t dev` then `databricks bundle run <key> -t dev` | minutes |
| Prod rollout | Same bundle, `-t prod`, after review | explicit approval |

Rules:
- Always `-t dev` and an explicit `--profile`. Prod needs the user's explicit instruction.
- `bundle validate --strict` after every configuration change, before deploy.
- Dev target uses `mode: development` so resources get per-user prefixes and schedules are paused.
- `bundle destroy` is destructive. Name the target and confirm first.
- Apps: `bundle deploy` leaves an app stopped; run the app resource or use `databricks apps deploy`.

## Step 4 - Local versus workspace differences

Code that passes locally can still fail on the workspace. Check these before declaring done:

- `spark` and `dbutils` are injected in notebooks; in `src/` create the session with `DatabricksSession` or receive it as a parameter. Never build a local `SparkSession` inside library code.
- Connect (Spark Connect) has limits: no RDD API, no `.cache()`/`.persist()` on serverless, no `SparkContext`. Rewrite instead of working around.
- Paths: use Unity Catalog volumes (`/Volumes/...`) and three-part table names, not local paths or `dbfs:/`.
- Dependencies: locally in `pyproject.toml`; on the workspace via the wheel in the bundle or the job environment. A package that imports locally may be missing remotely.
- Secrets: `dbutils.secrets` or environment config, never literals in the repo.

## Step 5 - Verify before saying "reflected"

Evidence, not assumption:

1. `databricks bundle validate --strict -t dev` exits 0.
2. `databricks bundle deploy -t dev` succeeds.
3. `databricks bundle summary -t dev` lists the resource with its workspace URL.
4. `databricks bundle run <key> -t dev` finishes SUCCESS, or the user confirmed the resource in the UI.
5. Local tests pass (`pyspark-testing`).

Report each as done, failed, or not run. Do not claim the workspace matches the repo without steps 2 and 3.

## Safety

- Nothing is installed globally by this skill; project-local `.venv` only.
- Deploys, runs and deletes touch a shared workspace. Confirm profile and target before each state-changing command.
- Do not paste tokens or `.databrickscfg` contents into chat or files.
