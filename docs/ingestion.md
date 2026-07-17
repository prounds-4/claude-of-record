# Ingestion: from inbox to record

Ingestion is how a new document becomes a wiki page. There is one interactive front door, a set of bulk handlers for the high-volume document types, and a triage procedure for anything unrecognized.

## The interactive path

For a single document, the steps are always the same ten: read the sidecar (the plain-text copy of a PDF that the agent reads and cites; generate it if missing, run OCR first if the PDF is only images), check the filename against the standard pattern for its type and propose a rename if needed, work out what kind of document it is, draft the page with structured fields and a body that cites specific lines, ask the human anything unclear, write the page, add one line to the journal, rebuild the index, connect the cross-references, run the checks.

Two details carry most of the value. **Name pages by the ID in the documents.** A change order the builder numbers 84 gets a page named for change order 84, so the wiki and the other parties speak the same language. **Ask, do not guess.** When the type is clear but the exact ID is not (a revision suffix, an ambiguous date), the procedure asks the human. A wrong guess written into a page spreads through every page that links to it.

## Triage: the inbox and the unknown

New files land in an inbox folder. Triage reads the filename and the first hundred or so lines of the sidecar for clues (letterhead, form numbers, document numbering patterns) and routes each file to one of three outcomes:

| Outcome | Action |
|---|---|
| Clear match to a type the system already handles | Propose the standard name and destination; on confirmation, move and ingest normally |
| Match to a planned future type the system cannot handle yet | Park in a pending folder with a triage note beside it; journal the deferral; no page produced |
| No match to any known type | Park in an unclassified folder with a triage note saying what was seen and why nothing fit; surface with a recommendation |

**Never silently invent a new record type.** Adding a type is a design decision: a new schema, a new ingestion procedure, new checks. It happens only on an explicit human decision, recorded in the journal. The triage notes stay on disk, so a later re-triage picks up where the last one stopped.

## Bulk handlers and batch mode

Anything arriving in volume (log exports, pay-application sets, RFI snapshots) gets its own batch handler, never one-file-at-a-time ingestion. Every handler must be safe to re-run: run it twice on the same input and the second run creates and changes nothing. The validation suite tests exactly that ([validation.md](validation.md)). Batch triage of a full inbox runs in two passes: first a cheap classify pass where the human accepts or declines routings in batches, then execution of only the confirmed ones, with clarifying questions asked before any page is written rather than corrections made after.

## Bundle-aware routing

Converting file by file is the wrong unit for a real document set. A vendor's change-order folder with forty attachments is one thing, not forty. Routing works at the folder level: one folder becomes one page with many source files. On the real project this single decision cut the projected record count by nearly three-quarters, which is the difference between a set of pages a human can audit and one they cannot.

## Snapshots and the two-tier source model

Logs that change over time (change-order logs, RFI trackers) are captured as dated snapshots. When a fresh snapshot arrives, the page gets a new timeline entry and the newest snapshot replaces the old one in its source list, but nothing is erased: the page shows what the log said on every date it was captured, and an old snapshot can still be cited.

Some record types need two kinds of source with different jobs. For an RFI (a question sent from the construction site to the architect), the periodic log export owns the status and dates, while the individual response letter owns the actual question and answer. Writing down which source owns which fields prevents a quiet failure: a stale log entry overwriting the richer letter content, or the reverse.

## The hash gate

The other parties re-send the same documents constantly, renamed and moved into new folders. Checking names and file sizes flags too much as new. So a fingerprint check sits in front of the inbox: every incoming file is hashed (SHA-256, a fingerprint of its exact bytes) and compared against everything already stored. Byte-identical re-sends go to a report instead of the triage queue. Only genuinely new content reaches a human decision.

## Schemas as a closed world

Every record type has a schema file: the one place that says what fields a page of that type may carry. To change it, edit the file, bump its version, and journal the decision. The structural audit flags any field a page carries that its schema does not declare. This is what keeps thirty record types consistent across months of sessions that have no memory of each other.
