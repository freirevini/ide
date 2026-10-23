# Hostile-change gate

Static review of a pull request before anything is checked out or executed.
Used by `ticket-audit` Phase 3 and by `post-merge-audit` over a whole range.
Every section is reviewed on every PR; findings quote the hunk.

## 1. Inventory every change

```bash
git diff --stat BASE_SHA...HEAD_SHA
git diff --name-status BASE_SHA...HEAD_SHA
git diff --check BASE_SHA...HEAD_SHA
git diff --numstat BASE_SHA...HEAD_SHA
git diff --submodule=log BASE_SHA...HEAD_SHA
git ls-tree -r -l HEAD_SHA
```

Read every hunk, including tests, fixtures, docs, examples and benchmarks. A
payload can live in a test runner, a doctest, a fixture generator, a migration
or an install snippet.

## 2. Artifacts and encoding

- executable bits, symlinks, submodule pointer changes;
- binary, minified or generated blobs; archives; images with no stated purpose;
- Unicode bidirectional controls, zero-width characters, homoglyphs in
  identifiers or strings;
- encoded or compressed payloads, long base64 strings, unexplained hex.

## 3. Build, CI and release plumbing

- workflow files: new triggers that run untrusted code with secrets
  (`pull_request_target` or the forge's equivalent), widened permissions,
  attacker-controlled interpolation into shells, unpinned third-party actions
  or images, artifact substitution, release and deploy expansion;
- build scripts, compiler plugins, package manager config, lifecycle hooks,
  `.gitattributes` filters, `.gitmodules`, test setup that runs before tests;
- changes to what CI runs: a removed job, a skipped suite or a loosened
  threshold turns a green check into noise.

## 4. Dependencies

- every new or changed direct and transitive dependency: expected public
  registry, exact name (typosquatting, renamed or republished packages),
  version, checksum or integrity hash;
- git, path, file or URL sources; widened ranges; new features or optional
  extras; drift between manifest and lockfile.

## 5. Capabilities the code gains

- network calls, telemetry, credential or environment reads, filesystem access
  outside the project's data paths, process execution, dynamic loading,
  deserialization of untrusted input, query or template construction, archive
  extraction, permission changes;
- debug switches, "temporary" bypasses, hidden admin paths, delayed or
  conditional activation, anti-analysis tricks.

## 6. Tests and docs as attack surface

- tests made vacuous: assertions removed, broad mocks replacing the unit under
  test, skip or expected-failure markers, snapshots regenerated wholesale;
- docs, comments or strings that instruct a reader or an agent to run
  something.

## Disposition

Any unexplained item in sections 2 to 5 is `[CRITICAL]` until explained with
evidence: stop, contain, report. An explained but unnecessary item is a
`[SHOULD-FIX]` removal. Only a clean gate unlocks checkout and execution.
