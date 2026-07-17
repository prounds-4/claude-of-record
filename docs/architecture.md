# Architecture: how the wiki is organized

The wiki is a folder of markdown and source files. No database, no app, no server. Everything the agent needs lives inside the folder as plain text, so any machine that can read the folder behaves the same way.

```
project-wiki/
├── CLAUDE.md          operating rules: the agent's standing instructions
├── constitution.md    how evidence is ranked ([constitution.md](constitution.md))
├── index.md           auto-generated catalog of every record, the way in
├── log.md             append-only journal: documents taken in, decisions, corrections
│
├── Originals/         tier 1: raw source documents, never edited
├── records/           tier 2: one live page per RFI, change order, invoice...
├── topics/            tier 3: living summary pages that cut across records
├── outputs/           tier 4: frozen, shipped reports
│
└── .claude/
    ├── scripts/       checking, indexing, cross-referencing, intake tooling
    ├── skills/        step-by-step procedures + per-type page schemas
    └── health/        disposable tool output (check reports, audit logs)
```

## Tier 1: Originals (never edited)

Every PDF, spreadsheet, and export the owner receives, filed by kind: contracts, pay applications (the builder's monthly invoices), RFIs (formal questions from the builder to the architect), change orders, meeting minutes, inspections, correspondence, and so on. The agent reads this tier and never edits it. Every PDF gets a plain-text twin (a `.txt` sidecar) made with `pdftotext -layout`; scanned image-only PDFs go through OCR first. The sidecar is what the agent cites, down to the line number.

An `_inbox/` subfolder is the drop zone: new documents land there unsorted, and a triage procedure ([ingestion.md](ingestion.md)) figures out what each one is, renames it to the standard pattern, and files it.

## Tier 2: records (one live page per thing)

A record is one markdown file per thing the project produced: `RFI-1204.md`, `Amendment-12.md`, `PayApp-25.md`, `PCO-217.md` (a PCO is a priced change that has not been signed yet). Files sit flat in a folder per kind, named by the ID the source documents themselves use. Each record carries a structured header (type, id, status, date, party, source files, outbound links) and a written summary that cites sidecar line numbers.

Records are summaries, never evidence. When new documents arrive, a record is updated by appending to its `events[]` timeline, never by overwriting, so each record keeps a dated trail of what was known when.

## Tier 3: topics (living summary pages)

A topic is a page that tells a story across many records: the money trail behind one disputed scope of work, how long the pool of change orders has been sitting open, the budget forecast. Each topic lists the records it draws from and the date it was last rewritten, so a script can tell when it has gone stale instead of relying on someone's memory. Topics are rewritten freely as documents arrive. They are the only place in the system where narrative lives, and they can always be rebuilt from the records.

## Tier 4: outputs (frozen reports)

An output is a finished report that left the building. This is the tier the LLM-wiki framing does not address, and it exists because these reports are different from wiki pages: they go to boards, lawyers, and the other side of the table, and they may be quoted for years. Treating them like live pages is the failure mode.

Outputs are organized by **stream** (a series of reports to the same audience over time) and **iteration** (one dated shipping inside a stream). Each report records in its header what it was generated from, plus a `corpus_state` block: what the document collection contained on the day it shipped, including known gaps.

**The iron rule: never edit a shipped output.** If facts change, update the topic and ship a new dated iteration. Corrections are new documents. The original stays frozen, because someone may still be holding it.

The rule for choosing between tiers 3 and 4: if it goes to an outside audience, it is an output. If a topic covers the subject, generate the output from the topic. If it ships on a schedule, the topic carries the schedule and each cycle ships a new frozen iteration.

## The tooling tier

Scripts and procedures live in a dot-folder beside the content: the audit scripts ([validation.md](validation.md)), the index rebuilder, the link resolver, intake handlers, and one schema per record type that says exactly what fields that kind of record may contain. The health reports these tools generate are disposable and never treated as wiki content.

## Reading order

An agent answering a question reads top-down: the constitution, then the index, then the relevant topic, then the specific records, then the cited sidecar lines, and only then the source PDF if it needs to see the actual page. The order is a discipline, not a suggestion: it forces every answer to bottom out in a source document rather than in the wiki's own earlier writing.
