---
name: lint-wiki
description: Enforce the wiki's 9 consistency invariants across records/, topics/, outputs/, and root brain files. Writes a report to .claude/health/lint-report.md. Use after ingestions, before shipping deliverables, or on demand.
---

# /lint-wiki

Audit the wiki against the 9 invariants documented in CLAUDE.md.

## Procedure: preferred path

**Run the canonical script:**

```bash
python3 .claude/scripts/audit.py
```

This is the schema-validating audit. It checks required-field presence, enum values, source-path resolution, sidecar existence, id-vs-filename match, type-vs-directory match, date sanity, index integrity, body-link resolution, and consults `.claude/scripts/whitelist.yaml` for known non-violations.

For a one-line summary: `python3 .claude/scripts/audit.py --terse`.

For the full session-completion gate (audit + idempotency + index + resolve-refs):

```bash
.claude/scripts/validate-all.sh
```

The validation suite must pass (exit 0) before claiming any phase or session complete. Pre-completion validation is automatic, not user-prompted.

## Bug history (read this before reimplementing the rules manually)

An earlier regex-based partial reimplementation of the rules below missed hundreds of real violations because:
- It checked field *presence* but never enum values (a large class of enum violations slipped through)
- It used a regex-based source-path extractor that didn't unescape YAML doubled-apostrophes (a dedup bug that broke handler idempotency)
- It didn't YAML-round-trip parse, so silent `#`-comment truncations in source paths went unnoticed
- It missed required `events: list` / `issuing_party` fields on several Record types

Don't reimplement. Use `audit.py`. If audit.py is missing a check, extend it there.

## Rules reference (the audit script implements all of these)

Run all 9 rules. For each violation, capture: rule number, severity (`error` | `warning`), file path, and a one-line description. Group results by rule in the output report.

### Rule 1: Frontmatter completeness

For every `records/**/*.md`, `topics/*.md`, `outputs/*.md`:
- Read the YAML frontmatter.
- Look up `.claude/skills/_schemas/{type}.yaml` for required fields (`Amendment.yaml`, `topic.yaml`, `Deliverable.yaml`, etc.).
- Flag any missing required field as `error`.
- Flag any unknown extra field as `warning` (helps catch typos like `referenced_bys`).
- For deliverables: also verify the `corpus_state:` block has its required sub-fields.

### Rule 2: Link integrity

For every `records/**/*.md`, `topics/*.md`, `index.md`, `outputs/**/*.md`:
- Parse every markdown link `[text](path)`.
- For relative paths, resolve them and check existence.
- Flag unresolved links as `error`, **except** when the corresponding frontmatter `references[]` entry has `status: pending-target`. Those are forward-looking declarations expected to resolve as the corpus grows. Pending refs go to `.claude/health/pending-refs.md` (warning, not error).
- Flag links into `Originals/` separately. These are source citations and matter most for provenance.

### Rule 3: Source-citation discipline

For every `records/**/*.md` body and every `topics/*.md` body (skip frontmatter):
- Identify lines containing dollar amounts (`$NNN`, `$NN.NM`), percentages, dates, or attributed quotes (`"…"`).
- For each such line, verify there's an inline markdown link within ~80 characters of the figure.
- Flag uncited figures as `error`.
- Whitelist exceptions: bullet headers like "**Status:** open" don't need citations; the inline narrative does.

### Rule 4: Index integrity

Compare `index.md` entries against the actual `records/**/*.md` set:
- Every Record must appear in `index.md`. Missing Record → `error`.
- Every `index.md` Record entry must point at an existing file. Stale entry → `error`.
- Same check for `topics/*.md` (excluding `README.md`).

### Rule 5: Naming convention

For every `records/**/*.md`:
- Verify the filename matches the canonical pattern for its declared `type`:
  - `Amendment` → `Amendment-(GC|ARCH)-\d{2,3}\.md`
  - `BaseContract` → `BaseContract-.+\.md`
  - `Change` → `Change-\d{4}(\.\d+)?\.md`
  - `RFI` → `RFI-\d{4}(\.\d+)?\.md`
  - `ASI` → `ASI-\d{2}(-\d{2})?\.md`
  - `OAC` → `OAC-\d{3}\.md`
  - `PayApp` → `PayApp-(GC-Main|GC-Site|ARCH)-\d{2,3}(-.+)?\.md` (one prefix per billing stream)
  - `Budget` → `Budget-Snapshot-\d{4}-\d{2}-\d{2}(-.+)?\.md`
  - `Inspection` → `Inspection-\d{4}-\d{2}-\d{2}-.+\.md`
  - `Permit` → `Permit-.+\.md` (loose; permit number formatting varies by issuing authority)
  - `PCCO` → `PCCO-\d{3}\.md`
  - `Schedule` → `Schedule-\d{4}-\d{2}-\d{2}(-.+)?\.md`
  - `Submittal` → `SUB-\d{4}(\.\d+)?\.md`
  - `FieldReport` → `FieldReport-\d{4}-\d{2}-\d{2}(-.+)?\.md`
  - `QualityReport` → `QualityReport-\d{4}-\d{2}-\d{2}-\d{2}\.md`
  - `NCR` → `NCR-.+\.md` (loose; NCR logs use date-based naming `NCR-YYYY-MM-DD-NN`; individual NCR letters use `NCR-\d{4}` when ingested separately)
  - `DesignChange` → `DesignChange-\d{4}-\d{2}-\d{2}-\d{2}\.md`
  - `BidPackage` → `BidPackage-.+\.md` (loose; bid-package IDs follow the project's buyout-log conventions and may carry decimal or letter suffixes; not strict 2-digit)
  - `Invoice` → `Invoice-.+\.md` (loose; vendor invoice numbering varies)
  - `Subcontract` → `Subcontract-.+\.md` (loose; vendor names vary)
  - `SubcontractCO` → `SubcontractCO-.+\.md` (loose; vendor + CO# combination varies)
  - `PrimeCO` → `PrimeCO-(GC|ARCH|AOR)-\d{2}-\d{4}-\d{2}-\d{2}\.md`
  - `CityAgreement` → `CityAgreement-.+\.md` (loose; multiple variants including amendments)
- Verify the file lives under the right `records/{class}/` subdirectory.

For every `outputs/*.md` (or `.pptx`/`.docx`/`.pdf`):
- Verify filename matches `outputs/YYYY-MM-DD-<slug>.<ext>` (date prefix is the shipped date).

Mismatch → `error`.

### Rule 6: Topic-page freshness

For every `topics/*.md` (excluding `README.md`):
- Read frontmatter `last_synthesized` and `source_records[]`.
- For each `source_records[]` entry, read its `ingested_at`.
- If any source's `ingested_at` is later than `last_synthesized`, flag as `warning` (topic is stale; run `/topic-update <slug>`).

### Rule 7: Provenance

For every `records/**/*.md`:
- For each `source_files[].path`, verify the file exists.
- For each declared `sidecar`, verify the sidecar exists (only required for `prose-*` types).
- Behavior by `type:` tag:
  - `prose-primary`, `prose-metadata`, `prose-spec`, `prose-snapshot` → both PDF and sidecar must exist; line-citation expected in body
  - `structured-canonical` → file must exist; sidecar not required; body cites by row/section description, not line number
  - `image-drawing` → file must exist; sidecar not required; **flag any line-number citation into an image-tagged sidecar as `error`** (drawing sidecars are geometry tokens, not prose)
- Missing source → `error`. Missing required sidecar → `warning`.

### Rule 8: No-numbers-in-prose

For `index.md` and section headers (`##`, `###`) of any topic page:
- Flag any line containing a dollar amount, count, or percentage as `error`.
- Whitelist:
  - Numbers in identifiers (`AIA Document A102-2017`, `RFI #1204`, `Amendment 7`, dates `2025-06-10`, AIA section references like `§15.1.7`, line references like `line 120`).
  - **Auto-regenerated entity-class counts in `index.md`**: section headers like `## Contracts (26)` and the top-of-document Record-count summary line. These are deterministic outputs of `/rebuild-index` and don't decay if the index is kept current; the rule's purpose (preventing calcified narrative figures) doesn't apply to regenerable index counts.

### Rule 9: Deliverable immutability

For every `outputs/*.md` (or `.pptx`, `.docx`, `.pdf`):
- Read frontmatter `status` and `shipped_date`.
- If `status: shipped-frozen`, check the file's mtime against `shipped_date`. Any mtime later than `shipped_date` → `error` (deliverable was modified after shipping).
- Verify the filename's date prefix matches `shipped_date`. Mismatch → `error`.
- Verify the `corpus_state:` block exists and has required sub-fields per `_schemas/Deliverable.yaml`. Missing → `error`.
- Corrections to a frozen deliverable must ship as a NEW dated file. The original is never edited.

## Inbox status (informational, not a rule)

Walk `Originals/_inbox/`. For the report's "Inbox" section, enumerate:
- **Pending triage**: files at the top level of `_inbox/` (excluding `_unclassified/` and `_pending-pattern/`). One line per file: path + age in days from mtime. These are sources the user has dropped but not yet run `/ingest` against.
- **Awaiting pattern development**: every file under `_inbox/_pending-pattern/{type}/`. Group by type. One line per file: path + age + pointer to its `.triage.md` if present.
- **Unclassified**: every file under `_inbox/_unclassified/`. One line per file: path + age + pointer to its `.triage.md` if present.

These are not violations. They are work surfaces. The lint summary header should include the three counts so the user sees them at a glance (e.g., `Inbox: 3 pending, 1 pending-pattern, 0 unclassified`).

For any non-PDF/xlsx/triage.md file under `_inbox/` (stray `.DS_Store`, etc.), report at the bottom of the Inbox section under "Junk to remove". These are noise that the user (not the agent) should decide about.

## Output

Write `.claude/health/lint-report.md` (overwrite each run):

```markdown
# Lint report

_Generated {YYYY-MM-DD HH:MM} by /lint-wiki._

## Summary
- Errors: {N}
- Warnings: {M}
- Files scanned: {records: X, topics: Y, root: Z, outputs: W}
- Inbox: {P pending, Q pending-pattern, R unclassified}

## Rule 1: Frontmatter completeness
{violations or "no violations"}

## Rule 2: Link integrity
{violations or "no violations"}

[ … through Rule 9 … ]

## Inbox

### Pending triage
{file list with ages, or "inbox empty"}

### Awaiting pattern development
{file list grouped by type with ages + triage-note pointers, or "none"}

### Unclassified
{file list with ages + triage-note pointers, or "none"}

### Junk to remove
{stray non-content files like .DS_Store, or omit section entirely}
```

Append to `log.md`: `## [YYYY-MM-DD] lint | {N errors, M warnings}` if non-zero, or `## [YYYY-MM-DD] lint | clean` if zero.

## Behavior on violations

- Lint failures **don't block** other operations. They go to the report; the user decides how to triage.
- For zero-violation runs, optionally print "wiki is clean" to chat instead of dumping the empty report.
