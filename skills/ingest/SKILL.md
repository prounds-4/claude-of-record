---
name: ingest
description: Read a source document from Originals/ and produce or update an entity Record in records/{class}/. Use when the user asks to ingest, add, refresh, or process a specific PDF, sidecar, xlsx, or bundle into the wiki. Argument is the path to the source.
---

# /ingest

Read a single source document (or bundle) under `Originals/` and produce or update one entity Record under `records/{class}/{ID}.md`.

Re-running `/ingest` against a source whose Record already exists is **idempotent and additive**. It appends to `events[]`, swaps the most-recent snapshot pointer, and refreshes content fields. It never overwrites history.

## Argument

A path (relative to workspace root) to a source PDF, `.xlsx`, or bundle directory under `Originals/`. Examples:
- `Originals/contracts/GC-Prime-Contract/Amendments/Amendment-GC-07-2025-03-15.pdf`
- `Originals/oac-minutes/2025/OAC-042-2025-06-10.pdf`
- `Originals/asis/individual/ASI-04-issue-bundle/`
- `Originals/budget/2025/Budget-Snapshot-2025-10-01.pdf`
- `Originals/_inbox/some-mystery-document.pdf` (single-file triage; see Step 0)
- `Originals/_inbox/` (batch mode, triages every PDF in the inbox via clickable `AskUserQuestion` rounds; see Step 0)

## Procedure

### 0. Triage (only when source is under `Originals/_inbox/`)

Skip this step entirely when the source path is anywhere outside `Originals/_inbox/`. The rest of the procedure assumes the file is already in the right class folder.

**Dispatch by source kind:**
- **Directory** (`Originals/_inbox/` itself, or any subdirectory of it): dispatch to **Batch mode** at the end of this section.
- **Single file** (a PDF directly under `_inbox/`): proceed with the **Single-file flow** below.

#### Single-file flow

1. Ensure a `.txt` sidecar exists for the file (run `pdftotext -layout`; OCR with `ocrmypdf --force-ocr --invalidate-digital-signatures` first if image-only).
2. Read filename + first ~100 lines of the sidecar. Look for class signals:
   - **Amendment**: "AMENDMENT NO.", AIA G802 form code, "GMP" amount, GC or architect signature blocks
   - **BaseContract**: AIA A102/A201/B101 form codes in cover, "Standard Form of Agreement"
   - **ASI**: "Architect's Supplemental Instruction", ASI numbering in title block, architect letterhead
   - **OAC**: "Owner-Architect-Contractor Meeting", "OAC #NNN", action items table
   - **Change**: "Change Event", "Potential Change Order", CE# / PCO# in cover
   - **RFI**: "Request for Information", RFI# in cover, question/response structure
   - **PayApp**: AIA G702 / G703 form codes, "Application and Certificate for Payment"
   - **Budget**: "Cost Summary", per-Bid-Package table, analyst initials
   - **PCCO**: "Project Change Order", PCCO# (no PCO# alongside)
   - **Schedule**: Gantt / CPM artifact, milestone list, "Baseline Schedule" / "Update"
   - **Submittal**: "Submittal Transmittal", spec section header, sub product data
   - **Inspection**: "WRITTEN REPORT" / "Welding inspector" / "Ultrasonic Testing", AWS D1.1 acceptance standard, testing-lab letterhead (TrueTest Labs, etc.), a lab report ID pattern like `X25-NNNN-NNNN`, fabricator references (Summit Steel, etc.), per-piece status tables (fabricator piece IDs)
   - **Permit**: "CERTIFICATE OF" / "Permit Application", e-permitting portal header, municipal letterhead, permit number patterns like `NN-NNNNN-NN`, "revocable permit" / "right-of-way encroachment"
3. Branch on classification:

   **(a) Confident match to a known-pattern type** (Amendment, BaseContract, ASI, OAC, Change, RFI, PayApp, Budget):
   - Determine the canonical ID per Step 4 of this skill.
   - Determine the target subfolder per Step 3.
   - Use AskUserQuestion to confirm the proposed `{old-path} → {new-path}` move.
   - On confirm: `mv` the PDF and any existing sidecars (`.txt`, `.ocr.pdf`) to the target. Regenerate the `.txt` sidecar at the new path if the move would orphan it.
   - Continue with Step 1 (Resolve the source) using the new path. Steps 2-10 then run normally.

   **(b) Match to a pre-wired future type without an ingestion pattern yet** (PCCO, Schedule, Submittal):
   - `mkdir -p Originals/_inbox/_pending-pattern/{type}/` and `mv` the file (+ sidecars) into it.
   - Write `{filename}.triage.md` next to the file with the structure below.
   - Append `## [YYYY-MM-DD] deferred | {filename}: {type} ingestion pattern not yet developed` to `log.md`.
   - Tell the user in chat: one sentence on what was found and that ingestion is deferred until the pattern is built. Do NOT produce a Record. Stop.

   **(c) No confident match to any known type** (genuinely new entity class, or too ambiguous):
   - First, before parking: if the evidence narrows to two or three candidate types, use AskUserQuestion to let the user pick or confirm "none of these." Don't park files the user could have routed in one click.
   - If still unclassified after asking (or evidence is too thin to even ask): `mkdir -p Originals/_inbox/_unclassified/` and `mv` the file (+ sidecars) into it.
   - Write `{filename}.triage.md` next to the file with the structure below.
   - Append `## [YYYY-MM-DD] deferred | {filename}: unclassified; needs taxonomy decision` to `log.md`.
   - Tell the user in chat: one sentence on what was observed, plus a recommendation (extend an existing type, add a new type, or treat as `reference/`). Do NOT produce a Record. Do NOT invent a new entity type unilaterally. That is an architectural decision requiring a `decision` log entry. Stop.

**`triage.md` sidecar format** (plain markdown, no frontmatter):

```markdown
# Triage note: {original-filename}

## Observed
- Filename: {original-filename}
- First-page evidence: {3-5 bullets: letterhead, title block, dates, identifiers}

## Classification attempt
- Candidate types considered: {list}
- Why none fit (or why ambiguous): {reasoning}

## Suggested next step
{one paragraph: e.g., "Add Permit entity type", "Extend ASI schema to cover field-issued sketches", "File as reference/"}
```

These notes survive across sessions so a later re-triage picks up where the prior one left off.

#### Batch mode (directory arg under `_inbox/`)

For triaging multiple inbox files in one session. Two-pass design: it minimizes wasted extraction on declines and replaces long markdown reports with clickable `AskUserQuestion` rounds.

**Pass 1: Cheap classify + batched user decisions:**

1. Enumerate PDFs directly under the directory. **Skip** `_unclassified/` and `_pending-pattern/` subdirectories. Those have already been triaged and are awaiting separate user action.
2. For each PDF:
   - Ensure `.txt` sidecar exists via `pdftotext -layout`. **Do NOT run OCR yet.** Skip to a "needs OCR / Hold by default" outcome if the sidecar comes back near-empty (image-only). OCR is expensive; defer until after the user has accepted the file for ingest.
   - Read filename + first ~50 lines of the sidecar. Compute candidate type using the same class signals listed in the single-file flow above.
3. Build batched `AskUserQuestion` calls. **Max 4 questions per call**, so for N inbox files you'll do `ceil(N/4)` rounds.
   - One question per file. Format:
     - `question`: `"{filename}: {one-line summary of contents}. How to route?"`
     - `header`: short type chip, max 12 chars (e.g. `"Inspection?"`, `"Permit?"`, `"Decline?"`)
     - `options` (max 4):
       1. `Route to {recommended-type}`: first option, suffixed `(Recommended)`
       2. `Route to {alternate-type}`: only if a credible second candidate exists; otherwise omit
       3. `Decline → reference/{subfolder}/`: file is real but not Record-worthy; subfolder defaulted from type signals (insurance certificate → `reference/insurance/{party}/`, certified payroll → `reference/certified-payrolls/{sub}/`, loose drawing → `reference/loose-drawings/`, etc.)
       4. `Hold for clarification`: defer; file stays in `_inbox/` for the next round
     - The auto-provided "Other" option lets the user supply free-text override (e.g. specifying a different type or subfolder).
4. **Collect ALL answers across all rounds before taking any irreversible action.** Do not partially execute. That defeats the purpose of letting the user see and confirm the full routing plan.

**Pass 2: Selective execution (per-file, in order):**

For each file according to its routing-plan answer:

- **Route to {type}** → run the single-file ingest pipeline:
  1. Move PDF + sidecars to `Originals/{class}/{canonical-filename}.{pdf|txt}` (canonical filename per Step 4).
  2. OCR if needed (image-only original).
  3. Build the Record per Steps 5-7.
  4. **For genuinely uncertain fields (lab name, accept/reject status, parent transmittal, etc.): use inline `AskUserQuestion` BEFORE writing the Record.** Never produce a Record carrying a placeholder that would need correction afterward. One more clarifying question up front beats a post-hoc correction pass.
  5. Append `## [YYYY-MM-DD] ingest | {ID}: {short title}` to `log.md`.
- **Decline → reference/{subfolder}/** →
  1. `mv` PDF + sidecars to `Originals/reference/{subfolder}/`.
  2. Append entry to `Originals/reference/INDEX.md` with the format `**[filename](path)**: {what it is}. {forensic relevance: typically "Low forensic value."}`.
  3. Append `## [YYYY-MM-DD] deferred | {filename}: declined to reference/{subfolder}/` to `log.md`.
- **Hold for clarification** → leave in place; user re-invokes when ready. No log entry needed (the file's continued presence in `_inbox/` is its own marker).

**End of round:**

- Run `/rebuild-index`, `/resolve-refs`, and `/lint-wiki` once after the entire round completes (not per-file).
- Final report to user (~10 lines): files routed (with target Record IDs), files declined (with target subfolders), files held, any new pending-target refs surfaced. **No long markdown table.**

**Why two-pass:** It separates *decision* from *execution*, lets the user see the full plan before any move, and prevents known antipatterns: long unread reports, OCR cycles burned on declined types, and post-hoc corrections to Records that should have asked one more clarifying question first.

### 1. Resolve the source

- If the path is a directory (ASI bundle, architect pay-app bundle, etc.), classify each PDF in the bundle by filename pattern:
  - Contains `NARRATIVE` → `prose-primary`
  - Contains `COVER SHEET`, `TOC`, or a documents-list marker → `prose-metadata`
  - Filename starts with CSI section number (`NN NN NN -`) → `prose-spec`
  - Drawing prefix (`SK-`, `A1.`, `A2.`, etc.) or main drawing PDF → `image-drawing`
  - Otherwise → ask user.
- For each PDF: ensure `.txt` sidecar exists. If missing: `pdftotext -layout <path>.pdf`. If image-only: `ocrmypdf --force-ocr --invalidate-digital-signatures <path>.pdf <path>.ocr.pdf`, then `pdftotext` against the `.ocr.pdf`.
- Read every `prose-*` sidecar in full. **Do not paraphrase from the PDF directly.** Verbatim language must come from the sidecar.
- Never read content from `image-drawing` sidecars. They're geometry tokens. Reference the source PDF for visual content.

### 2. Filename canonicalization (for messy inputs)

- Compare the file's basename against the canonical pattern for its likely type (see step 4).
- If the filename doesn't match: **propose a rename** with reasoning. Ask user to confirm via AskUserQuestion.
- If user confirms: `mv` the PDF in place, regenerate the `.txt` sidecar at the new path, update the `.ocr.pdf` sibling.
- If user declines: ingest the Record but note the non-canonical filename and the rejected rename.
- Never overwrite an existing canonical-named file.

### 3. Identify the entity class

Use the source path + content:

| Source path | type |
|---|---|
| `Originals/contracts/...Amendments/...` | `Amendment` |
| `Originals/contracts/...` prime contract or architect agreement (root, not Amendments) | `BaseContract` |
| `Originals/oac-minutes/...` | `OAC` |
| `Originals/asis/...` | `ASI` |
| `Originals/change-orders/...` (specific CE row) | `Change` |
| `Originals/rfis/individual/...` (specific RFI letter) | `RFI` |
| `Originals/rfis/snapshots/...` (when ingesting a specific RFI from snapshot) | `RFI` |
| `Originals/pay-applications/...` | `PayApp` |
| `Originals/budget/...` | `Budget` |
| `Originals/inspections/...` | `Inspection` |
| `Originals/permits/{permit-no}/...` | `Permit` |
| `Originals/schedules/...` | `Schedule` (future; pattern not yet developed) |
| `Originals/submittals/...` | `Submittal` (future; pattern not yet developed) |

### 4. Determine the canonical ID

| type | pattern |
|---|---|
| `Amendment` | `Amendment-{GC\|ARCH}-NN` (zero-padded, 2-3 digits; revision in body) |
| `BaseContract` | `BaseContract-{GC-A102\|GC-A201\|ARCH-B101}` (one entry per executed base agreement) |
| `OAC` | `OAC-NNN` (3-digit) |
| `ASI` | `ASI-NN` (2-digit, or `NN-NN` for compound) |
| `Change` | `Change-NNNN` (4-digit; suffix `.N` for revisions) |
| `RFI` | `RFI-NNNN` (4-digit; suffix `.N` for revisions) |
| `PayApp` | `PayApp-{GC-Main\|GC-Site\|ARCH}-NN[-variant]` (one prefix per billing stream) |
| `Budget` | `Budget-Snapshot-YYYY-MM-DD` (annotator initials → `notes_author:` field, not filename) |
| `Inspection` | `Inspection-YYYY-MM-DD-{lab-shortcode}-{descriptor}` (e.g. `Inspection-2025-06-10-TrueTest-Evening`); lab report ID like `X25-1234-0001` goes in `lab_report_id:` field, not filename |
| `Permit` | `Permit-{permit-no}`: preserve permit number formatting as issued (e.g. `Permit-24-00123-01`) |
| `PCCO` | `PCCO-NNN` (3-digit): future type |
| `Schedule` | `Schedule-YYYY-MM-DD[-version]`: future type |
| `Submittal` | `SUB-NNNN`: future type |
| `Discrepancy` | `Discrepancy-NNNN` (4-digit, zero-padded; next free number) |

### 5. Draft frontmatter per `_schemas/{type}.yaml`

All Records require: `type`, `id`, `title`, `status`, `date`, `source_files[]`, `references[]`, `referenced_by` (start `[]`), `ingested_at`, `ingested_by`.

Records with lifecycle progression also require `events[]` (start with the ingestion observation): **Change, RFI, PayApp, Submittal, Permit**.

Each `source_files[]` entry MUST have a `type:` tag. See the source-file `type:` classification table in CLAUDE.md.

Each `references[]` entry MUST have a `relationship:` enum value (per the schema for that type). For forward-looking refs to entities not yet ingested: add `status: pending-target`.

### 6. Write the body: extraction depth by type

| type | What goes in the body |
|---|---|
| **Amendment** | Cover-sheet date, NTE amount, scope summary, retroactive corrections (when present), e-signature envelope ID. Cite each fact. |
| **BaseContract** | Article structure as navigation aid (no full text). Modifications-from-standard pointer (don't extract; defer to topic page). |
| **OAC** | Action items table (numbered with origin meeting, title, assignment, due date, status), Owner Requested Changes per upcoming ASI, cross-refs to RFIs/PCOs/ASIs/schedules discussed. **Skip narrative discussion prose.** |
| **ASI** | **Narrative table verbatim** (per-drawing changes). Affected drawings list (sheet numbers). Affected spec sections list (CSI numbers). Cross-refs to pre-bid RFIs, other ASIs, downstream PCOs (when known). |
| **Change** | Cover-sheet fields (CE#, PCO#, PCCO#, ROM, etc.). Lifecycle event log (cited). Title-parsed cross-refs (every ASI/RFI/PCO embedded in the title becomes a structured ref). |
| **RFI** | If letter available: question text + response text (verbatim). If snapshot only: metadata. `response_status: awaiting` when no response yet. Cross-refs to drawings (text only), other RFIs, ASIs, PCOs. |
| **PayApp** | G702 nine-line summary. **Per-Amendment billing breakdown verbatim** (the table). G703 high-level category rollup (GCs, Insurance, Materials, Fee). Cross-refs to every Amendment + every PCCO drawn down (often 30+ references). Skip per-trade SOV detail. |
| **Budget** | Top-line rollup (forecast/contracted/allowances/contingency/balance). Per-Bid-Package summary. Analyst notes verbatim. Cross-refs to Amendments funding each BP. **Skip per-line-item bid detail.** |
| **Inspection** | Inspection date + type, lab + inspector cert, fabricator + location, acceptance standard. Per-piece findings (piece IDs + accept/repair status) when present. Findings summary (2-3 sentences). Cross-refs to RFIs / NCRs / drawings cited in the report. Don't extract inspector signature blocks or photo captions. |
| **Permit** | Permit number + issuing authority + status. **One Record per permit number; submissions accumulate as `events[]`.** Each submission is a `submission` event with date, scope summary, and source-file pointer. Conditions and grants captured in body. Cross-refs to drawings, RFIs, ASIs that triggered or were submitted under it. |

### 7. Re-ingestion semantics (idempotent)

If a Record already exists at the canonical path:
- **Append** to `events[]`. Never overwrite. Add an event capturing this observation.
- **Swap** the most-recent `prose-snapshot` in `source_files[]` (for Change/RFI/PayApp); preserve old snapshot citations inline within `events[]` entries.
- **Refresh** content fields driven by the new source (e.g., RFI status from latest snapshot).
- **Do not** modify body sections sourced from a previous `prose-primary` ingestion unless that primary source has been reissued.
- Show the user a diff before writing if the changes are substantive.

### 8. Cross-references: the spine

The dense cross-reference graph is the wiki's primary forensic asset. Be aggressive:
- Every entity name, ID, or numbered reference in body prose uses a markdown relative-path link, not plain text.
- Every numbered ID embedded in a source's title becomes a structured `references[]` entry.
- Forward-looking refs to entities not yet ingested: use `status: pending-target`. They warn but never fail lint, and auto-resolve when their target arrives.

### 9. Ask clarifying questions

When uncertain, use AskUserQuestion:
- The entity class or ID is ambiguous
- A factual field has conflicting values across pages of the source
- A reference is implied but not explicit
- The source has unusual structure not covered by the schema

**Don't fabricate.** Mark `status: unknown` and flag in Notes when the source doesn't tell you.

### 10. Wrap up

1. Write the Record to `records/{class}/{ID}.md`.
2. Append to `log.md`: `## [YYYY-MM-DD] ingest | {ID}: {short title}`.
3. Run `/rebuild-index` to refresh `index.md`.
4. Run `/resolve-refs` to populate `referenced_by[]` on linked Records and produce broken-refs + pending-refs reports.
5. Run `/lint-wiki`; report any new violations.

## Provenance discipline (non-negotiable)

- Every dollar amount, count, attribution, or quoted statement in the Record body must carry an inline source citation (relative-path link). Bare figures fail lint rule 3.
- Cite the `.txt` sidecar (preferred) or the source PDF. For OCR'd primes, cite the sidecar that came from the OCR pass.
- Never cite a line number from an `image-drawing` sidecar. Those are geometry tokens, not prose. Lint rule 7 fails on this.
- Quote sparingly. Paraphrase by default; quote verbatim only when exact wording matters (contract clauses, admissions, contradictions, narrative tables).

## Constitution §6: register source conflicts

If the source being ingested materially conflicts with an existing Record or instrument on the same fact (the same dollar value, date, attribution, or status), do not silently overwrite the field and do not pick one source by feel. Per `constitution.md` §6:

1. Rank the conflicting sources by §2 document-type tier, then §3 party axis, then the §2 tie-breakers.
2. Adopt the higher-authority value for the working field. Tag it with the correct epistemic class per §5 when it surfaces in a topic or deliverable.
3. Create a Discrepancy Record at `records/discrepancies/Discrepancy-NNNN.md` (schema: `_schemas/Discrepancy.yaml`). Capture `disputed_fact`, `conflicting_sources[]` (each with `source`, `tier`, `value`, and `party` when party-asserted), `resolution` + `resolved_authority`, `residual_risk`, and `status`. Link both conflicting Records via `references[]` with `relationship: conflicts-with`.
4. If §2 and §3 do not break the tie, set `status: escalated`, write the unresolved state into `resolution`, and ask the user. Never average, guess, or adopt the more convenient figure.

A detected conflict is a forensic asset. Registering it is mandatory, not optional. The attribution audit script independently surfaces same-source figure divergences as Discrepancy candidates.

## What this skill does NOT do

- Does not bulk-ingest arbitrary corpus directories. The directory-arg shortcut is reserved for `Originals/_inbox/` batch triage (Step 0) and for ASI / architect pay-app bundles (which are themselves a single logical entity). Bulk operations across corpus subdirectories use dedicated batch handlers (bulk extraction tooling lives outside the wiki workspace).
- Does not parse change-log xlsx tables into many Records. For the curated subset, the user identifies specific CE/PCO numbers to ingest as individual Records.
- Does not develop ingestion patterns for Schedule or Submittal types. Those are deferred until actual content arrives.
- Does not infer status when not stated explicitly. Mark `status: unknown` and flag.
