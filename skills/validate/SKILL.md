---
name: validate
description: Run the full pre-completion validation suite (schema audit, idempotency, index rebuild, resolve-refs). This is the Definition of Done. Use before claiming any phase/session is complete.
---

# /validate

Run the full validation suite. Must pass before claiming any phase or session complete.

## Procedure

```bash
.claude/scripts/validate-all.sh
```

For a one-line summary: `.claude/scripts/validate-all.sh --terse`.

The script wraps:

1. `.claude/scripts/rebuild_index.py`: regenerates `index.md`
2. `.claude/scripts/resolve_refs.py`: recomputes the inbound cross-reference graph
3. `.claude/scripts/audit.py`: schema-validating audit (required-field presence, enum values, source-path + sidecar existence, id-vs-filename, type-vs-dir, date sanity, body-link resolution; consults `whitelist.yaml`)
4. Idempotency loop: re-runs the bulk-ingest handlers (bulk extraction tooling lives outside the wiki workspace) and asserts 0 new Records produced

Exit 0 = pass. Exit 1 = real violations found; fix before claiming done.

## When to run

- **Always** before declaring a phase, session, or task "complete"
- After any bulk-ingest run
- After any handler or schema change
- Before shipping a deliverable

## Don't reimplement

The script IS the lint. Don't write a markdown rules list and try to follow it manually. The rules drift from the code, the regex misses cases the YAML parser catches, and the dedup logic gets subtly wrong (a manual reimplementation once missed hundreds of real violations this way).

If a check is missing, extend `.claude/scripts/audit.py`. If a known non-violation is flagged repeatedly, add it to `.claude/scripts/whitelist.yaml`.
