# Shape Signals

Used by Phase 3 of `forever-clean`. Exaggeration is judged against the
project, not against a universal number. The numbers in section 4 are
orientation for projects that declare nothing of their own - a reason to
look closer, never a gate.

## 1. Find the project's own limits first

They override everything else in this file. Look, in this order, for:

- Linter/analyzer config at the repo root or inside package directories:
  - JS/TS: ESLint `max-lines`, `max-lines-per-function`, `complexity`,
    `max-params`, `max-depth` in `eslint.config.*` / `.eslintrc*`; Biome
    `complexity` rules in `biome.json`.
  - Python: `[tool.ruff.lint.pylint]` `max-args`, `max-branches`,
    `max-statements`; `[tool.ruff.lint.mccabe] max-complexity`; pylint
    `max-module-lines`; `max-complexity` in `setup.cfg` / `.flake8`.
  - Go: `.golangci.yml` `funlen`, `gocyclo`, `gocognit`, `lll`.
  - Rust: `clippy.toml` `too-many-arguments-threshold`,
    `cognitive-complexity-threshold`.
  - Java/Kotlin: `checkstyle.xml` `FileLength`, `MethodLength`;
    `detekt.yml` `LongMethod`, `LargeClass`, `ComplexMethod`.
  - Swift: `.swiftlint.yml` `file_length`, `function_body_length`,
    `cyclomatic_complexity`.
  - C#: analyzer rules in `.editorconfig`; SonarQube `S138` / `S1541`.
  - Ruby: `.rubocop.yml` `Metrics/*`. PHP: `phpmd.xml`, `phpstan.neon`.
- Written conventions: `CONTRIBUTING.md`, `ARCHITECTURE.md`, `CLAUDE.md`,
  `AGENTS.md`, `.cursor/rules/*.mdc`, `.rules/`, `docs/`.
- The layout itself: median file size per directory, how features are
  grouped, where tests live, what a "module" means in this codebase.

Run the project's linter when one exists; its output counts as measured.
Everything else is estimated unless you computed it with the commands in
section 5.

## 2. Sprawl signals (too many moving parts)

Relative to the directory or module being touched:

- Files that only re-export or forward calls (wrapper with no behavior).
- One-function files whose only caller is a single file.
- Directories where every level contains exactly one child.
- Files that always change together in `git log` - they share a secret and
  probably belong together.
- `utils`, `helpers`, `common`, `misc` buckets collecting unrelated snippets.
- Hedge-named siblings: `thing.py` next to `thing_v2.py` or `thing_old.py`.
- A task that creates more files than it edits, outside scaffolding the
  user asked for.
- Many files far below the directory median (for example a module of
  twenty files under 30 lines each).

## 3. Bloat signals (one file doing too much)

- Several reasons to change in one file: HTTP routing + SQL + templates +
  business rules, or many unrelated classes.
- A file several times larger than its siblings (rule of thumb: above 3x
  the directory median) with no single secret explaining it.
- Functions that interleave distinct steps with different reasons to
  change, or need scrolling to read once.
- A one-line change means scrolling past unrelated code or reading
  hundreds of lines to find the spot.
- Deep nesting (past 3-4 levels) and long parameter lists (past 5-6) in
  code that is edited often.
- The file is the whole program while the project clearly has distinct
  modules elsewhere.

Not bloat by itself: a long file that is one coherent concern - a parser, a
large data table, a cohesive component, a generated file. Length alone is
not a signal.

## 4. Fallback orientation bands (when the project declares nothing)

A reason to check cohesion, never a violation:

| Shape | Look closer when |
|---|---|
| Source file | in the thousands of lines, or dozens of files under ~30 lines in one module |
| Function | past ~100 lines, or past ~10 independent branches |
| Parameters | more than 5-6 without a bundling object |
| Nesting | more than 3-4 levels of control flow |
| Context radius | one change touching more than 3 directories |

Widely used linter defaults sit near these values (ESLint `complexity` 20,
`mccabe` 10, gocyclo 15, detekt `LongMethod` 60, SwiftLint `file_length`
warning 400). A project that wants stricter numbers states them in its own
config - the skill never imposes them.

## 5. Measuring cheaply

```bash
wc -l path/to/file                                            # size of the target
find src/module -name '*.py' | xargs wc -l | sort -n           # siblings, spot outliers
git log --format= --name-only -n 50 -- src/module | sort | uniq -c | sort -rn   # co-change
grep -rn "from .thing import\|import thing" src | wc -l        # fan-in of a wrapper candidate
```

State in the report which numbers came from commands and which were
eyeballed.

## 6. Exemptions

Generated code, vendored dependencies, lockfiles, fixtures, snapshots, data
files, and applied migrations are not shape targets. Do not split, merge or
trim them as organization work.
