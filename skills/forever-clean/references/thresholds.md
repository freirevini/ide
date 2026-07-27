# Thresholds Reference

Used by Phase 3 (size/complexity audit) and Phase 2 (hard-block check) of
`forever-clean`.

## Size and complexity by language

| Language | File soft/hard (lines) | Function soft (lines) | Cyclomatic complexity | Params | Nesting | Source of default |
|---|---|---|---|---|---|---|
| TypeScript/JavaScript | 300 / 500 | 50 | 10 | 4 | 3 | ESLint `complexity`, `max-lines-per-function` |
| Python | 300 / 500 | 50 | 10 | 4 | 3 | `mccabe` C901 default 10; pylint `too-many-lines` tightened from 1000 |
| Go | 300 / 500 | 40 | 10 | 4 | 3 | gocyclo default 10; golangci-lint `funlen` default 60/40 |
| Rust | 300 / 500 | 50 | 10 | 4 | 3 | clippy `cognitive_complexity` default 25 |
| Java/Kotlin | 300 / 500 | 40 | 10 | 4 | 3 | detekt `ComplexMethod` tightened to 10; Checkstyle `FileLength` tightened from 2000 |
| Swift | 300 / 500 | 40 | 10 | 4 | 3 | SwiftLint `file_length`/`cyclomatic_complexity` tightened defaults |
| C#/.NET | 300 / 500 | 50 | 10 | 4 | 3 | SonarQube `S138` (method length) / `S1541` (complexity) |
| SQL (per script/migration) | 200 / 400 | n/a | n/a | n/a | n/a | convention: one migration = one concern |

If the project rule `020-code-shape-limits.mdc` is loaded, its table
overrides this generic one for that project.

## Hard-block naming patterns (never create without explicit user request)

- `*_v2`, `*_new`, `*_old`, `*_fixed`, `*_final`, `*_copy`
- `enhanced_*`, `improved_*`, `better_*`
- `*.bak`, `*.backup`, `*.orig`
- Unsolicited `SUMMARY.md`, `NOTES.md`, `CHANGES.md`, `REPORT.md`, or any ad
  hoc markdown recap of work performed - put it in the chat response.
- A shallow wrapper file whose entire body just forwards calls/re-exports
  with no added behavior.

## Net new file budget

- Default: 2 net new files per task.
- Each file beyond 2 needs a one-line justification stated before writing
  it (what secret it owns that the first 2 don't).
- "Net" means created minus deleted - consolidating 3 files into 1 is -2,
  not a violation.
