# {{PROJECT_NAME}} Wiki: Operating Rules

<!--
This is the operating-rules template for a Claude of Record wiki: the standing
instructions an agent reads at the start of every session. Fill every
{{placeholder}}, delete the sections that do not apply to your project, and keep
the rest. The companion document is constitution.template.md (evidentiary
doctrine). Operating rules govern how the system runs; the constitution governs
how evidence is weighed. They do not overlap by design.
-->

Owner-side analysis on {{PROJECT_NAME}}. This is the primary wiki workspace, an agent-maintained wiki. Read once, then act.

## Posture

{{One paragraph: the strategic posture of the analysis. Examples: "No formal claims have been filed; all analytical work is privileged, internal, and preparatory." State who may see wiki content and deliverables.}}

## Project identity

- **Project:** {{project name and scope packages}}
- **Location:** {{address}}
- **Owner:** {{owner entity}}
- **GC / CM:** {{contractor}} under {{contract form, e.g. AIA A102 + A201, as modified}}
- **Architect:** {{design architect}} under {{e.g. AIA B101}}; {{architect of record, if separate}}
- **Delivery:** {{delivery method and GMP/lump-sum structure; note anything unusual about how scope has been added (amendments, phases)}}

## Through-line

{{One sentence: the purpose every piece of work serves. Example: "Reduce the owner's cost exposure by attributing cost events to the responsible party, documenting evidence, and executing the contract levers that turn analysis into recovery."}}

---

## Glossary

### Parties

{{One line per party: canonical name, short form, role. The full authority weighting lives in constitution.md §3; this glossary is orientation only.}}

### Change-event lifecycle

<!-- Default reflects a common CM-at-Risk lifecycle; edit to match your GC's process. -->
- **CE**: Change Event. Earliest stage of a change in the Work. May or may not progress.
- **PCO**: Potential Change Order. A CE that has been priced.
- **PCCO**: A PCO (usually several, bundled) executed into the contract.
- CE and PCO are stages in the lifecycle of a single change. Model each stage that carries its own data as its own entity type.

### Contract instruments

- **Change Order**: formal instrument that executes a change in the Work.
- **Construction Change Directive**: unilateral owner directive to proceed without agreement on cost or time (A201 §7.3 or your contract's equivalent).
- **Amendment**: modification of the prime agreement itself. On many projects this, not the Change Order, is the instrument of sweeping change.

### Other project terms

{{Define every acronym and register your project uses: RFI, ASI, OAC, pay-app form numbers, snapshot sources, named budget workbooks. If leadership cites a recurring number ("the $X budget"), record here exactly which file and cell it resolves to, so the agent never re-derives it.}}

---

## Architecture

Four content tiers plus a tooling tier. Read top-down.

```
{{workspace}}/
├── CLAUDE.md          operating rules (this file)
├── constitution.md    evidentiary doctrine
├── index.md           auto-generated entity catalog
├── log.md             append-only journal
│
├── Originals/         raw sources; immutable; the agent reads, never edits
├── records/           live entity pages, flat by class
├── topics/            live synthesis pages
├── outputs/           frozen-shipped deliverables, by stream/iteration
│
└── .claude/
    ├── scripts/           audit / index / cross-reference / ingest tooling
    ├── skills/            wiki procedures + _schemas/ (one yaml per type)
    ├── project-invariants.yaml   fixed facts the semantic audit enforces
    └── health/            regenerable tool output; never wiki content
```

**Originals/**: every source document, filed by class ({{list your class folders: contracts/, pay-applications/, rfis/, change-orders/, minutes/, correspondence/, ...}}). Includes `_inbox/` as the drop zone for unsorted arrivals. Every PDF gets a sibling `.txt` sidecar (`pdftotext -layout`; OCR image-only PDFs first). Before staging any bulk pull into `_inbox/`, run the content-hash gate so renamed re-sends of known documents never reach triage.

**records/**: one markdown file per entity, named by the entity's canonical ID from the source documents. Live: updated as new corpus arrives. Re-ingestion of a refreshed register snapshot appends to the record's `events[]` and swaps the newest snapshot into `source_files[]`; history is never overwritten.

**topics/**: narrative synthesis pages. Each declares `source_records[]` and `last_synthesized`. The only narrative surface; always regenerable from records.

**outputs/**: frozen-shipped deliverables only, organized by stream (a thread shipping to one audience over time) and iteration (one dated shipping). Immutable after `shipped_date`. Corrections ship as a new iteration; the original is never edited.

### Topics vs outputs (decision rule)

1. Going to an external audience? If no, it is a topic update or a record.
2. If yes and a covering topic exists, generate from it, freeze, date, ship. If no topic exists and the need is recurring, create the topic first. A genuine one-off may ship ad hoc from records, still carrying `corpus_state:` and still passing the ship-time verification.
3. Produced on a cadence? The topic carries `snapshot_cadence:`; each cycle ships a new dated immutable iteration.

---

## Cross-referencing is the spine

- Every entity name or numbered reference in a record body is a markdown relative-path link, never plain text.
- `references[]` carries outbound links with relationship labels; `referenced_by[]` is populated by the resolver script, never by hand.
- Forward references to entities not yet ingested carry `status: pending-target`. They warn, never fail, and resolve themselves when the target arrives.
- When in doubt, more cross-references beat fewer. Graph density is the primary asset.

## Provenance (non-negotiable)

- Every dollar amount, count, attribution, or quote in any record, topic, or deliverable traces to a document under `Originals/`, cited inline with a relative-path link to the sidecar (line number quoted in prose).
- **Open the source before citing it.** Records are summaries, not evidence. Every load-bearing claim in a deliverable traces to a verbatim line in a sidecar opened in the current turn.
- **Do not recall; re-derive.** Memory and prior synthesis are orientation, never source.
- The constitution governs how a found source is weighed. Provenance and weighting compose; both must pass before anything ships.

## How to answer questions (reading order)

1. `constitution.md`: doctrine.
2. `index.md`: find the entity class or topic.
3. The relevant topic page (cross-cutting questions) or record (entity questions).
4. The record's cited sidecar lines, verbatim.
5. The source PDF only when page images matter.

For live-state questions, the wiki degrades gracefully: report from the latest snapshot with its date. For previously shipped deliverables, never update them; read their `corpus_state:` and answer from the live topic.

---

## Conventions

- **Record filenames:** match the canonical ID pattern per type ({{examples for your project: Amendment-07.md, RFI-1204.md, PayApp-GC-12.md}}).
- **Topics:** kebab-case slugs.
- **Outputs:** `outputs/<stream-slug>/<iteration>.<ext>` or `.../<iteration>/README.md` for bundles. Iteration is `[v|r]N-YYYY-MM-DD[-note]` or bare date.
- **Cross-references:** markdown relative paths only. No wikilinks.
- **Dollars:** `$1,250,000` or `$1.25M`. **Dates:** ISO in filenames, local convention in prose.
- **No numerical content in `index.md`** or topic section headers. Numbers drift; they live in records (cited) or regenerable reports.

### Source-file `type:` classification

| `type:` | Meaning | Lint behavior |
|---|---|---|
| `prose-primary` | main prose document | line citations expected |
| `prose-metadata` | cover sheets, TOCs | citations supported, not required |
| `prose-snapshot` | point-in-time capture of a moving register | snapshot date required |
| `structured-canonical` | source xlsx / tabular file | existence-checked; cite by row description, never line |
| `image-drawing` | drawing or sketch | existence-checked only; never line-cited |

---

## Behavioral definition of done (honesty discipline)

1. No "verified" without sample bounds: state what was checked and what was not.
2. Every deliverable carries a Verification Scope section: contextually verified / trusted upstream / not verified.
3. Audit scripts emit coverage statements; report them alongside results.
4. Before claiming done, enumerate in writing: what was opened this session, what was trusted upstream, what was not checked, whether any bounded-verification language is unbounded.
5. Sample bounds are the sample bounds. Unsampled items keep their full risk profile.
6. User pushback means a rule above was violated. Re-do the work at the level it deserved; do not defend the summary.

## Technical definition of done

Before claiming any phase or task complete, run the validation suite and confirm it exits clean:

```bash
.claude/scripts/validate.sh
```

Index rebuild, cross-reference resolution, structural audit, and semantic audit all must pass. "Structurally valid" (fields exist, paths resolve) is not "semantically correct" (values match sources, invariants hold). Never conflate them. When a new entity type is added, extend both the structural schema and the semantic invariants before extending any ingestion handler. Anything unfixable in-session goes on `.claude/health/known-bad-records.md` with a reason and a target for cleanup.

---

## Ingestion workflow

1. Read the sidecar (generate it if missing; OCR first if image-only).
2. Check filename canonicality; propose a rename before proceeding.
3. Identify the entity class.
4. Draft the record: full frontmatter, body citing specific lines.
5. Ask clarifying questions; never fabricate an uncertain ID or status.
6. Write the record; append one line to `log.md`.
7. Rebuild the index; resolve references; lint.

### Triage (files in `_inbox/`)

| Outcome | Action |
|---|---|
| Confident match to an established type | propose canonical name and destination; on confirmation, move and ingest |
| Known future type, pattern not yet built | park in `_inbox/_pending-pattern/` with a triage note; journal the deferral |
| No match | park in `_inbox/_unclassified/` with a triage note and a recommendation |

**Never silently invent a new entity type.** A new class is an architectural decision (schema, ingestion pattern, lint invariants) and requires an explicit human decision journaled in `log.md`.

Bulk arrivals get class-specific batch handlers, never per-file interactive ingestion. Handlers are idempotent: re-run on the same input, they create and change nothing.

---

## Operating cautions

- Do not express false certainty. Claims are what the record supports, or contingent on further evidence.
- Do not re-introduce calcified prose. No stored "current state" page, ever. Live state is computed on demand.
- Do not rely on pre-existing third-party synthesis without re-derivation from primary sources.
- Do not patch a draft after review exposes a load-bearing problem; regenerate from the corrected evidence. Prose problems are fixed inline; structural problems get a new draft.
- Do not modify a frozen deliverable. Ship a correction as a new iteration.
- {{If multi-machine on a sync folder:}} do not mutate the graph while another process holds the write lock. Graph-mutating operations acquire `.claude/scripts/writelock.sh acquire "<holder>"` first and release after. Locks age-stale after 30 minutes.
- Durable cross-user knowledge goes in the wiki (`log.md`, `index.md`, topics), never into any one agent's per-user memory.

## Log

Append to `log.md` for: ingest, topic-update, correction, decision, deferred, system change, shipped, finding. Format: `## [YYYY-MM-DD] {kind} | {summary}`.

**Emit rule:** interactive operations journal per event; bulk operations journal one summary line per run, and only when something changed. Litmus test for any entry: would a teammate reading it in three weeks learn something they could not get by re-running a script?
