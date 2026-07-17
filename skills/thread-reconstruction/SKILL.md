---
name: thread-reconstruction
description: Convert a multi-party email thread into a correspondence record with each message as a dated event and each position tagged to its party. Use when ingesting forensically significant email threads, or when the user asks who said what and when across a thread.
---

# Thread reconstruction

Turn a long multi-party email thread into a citable who-asserted-what-when timeline. The product is a correspondence record in which an offer, a concession, or a first mention of a dollar figure is a dated, attributable event rather than a memory of a long scroll.

## When to run

- Ingesting any email thread that carries positions, offers, admissions, or dollar figures.
- On request: "reconstruct this thread", "who committed to what here".

## Procedure

1. **Fix the artifact.** Export the thread to a file under `Originals/correspondence/` and generate its sidecar. The reconstruction cites the export, never a mail client.
2. **Split into messages.** Identify every message: sender, recipients, cc, timestamp. Quoted-reply blocks repeat earlier messages; attribute content to the message where it first appeared, not where it was re-quoted.
3. **One record per thread.** Create `records/correspondence/Correspondence-YYYY-MM-DD-{slug}.md` (date of the first message). Each message becomes an entry in `events[]`: date, sender, one-line substance, and the sidecar line range.
4. **Extract positions.** For each message, capture any assertion that matters forensically: a position on responsibility, a dollar figure, a commitment, a refusal, a deadline, a threat. Tag each per the constitution: a party's statement is `party:<X>`; a statement only becomes `rec-est` if an executed instrument establishes it.
5. **Watch the language edges.** "Conditionally offered" is not "agreed". "Will review" is not "accepted". Record the verbatim verb in quotes when the strength of the commitment matters; paraphrase drifts strong.
6. **Cross-link.** Link every entity the thread discusses (change orders, RFIs, amendments, pay apps) in both directions, so the entity's record shows the correspondence trail beside its pricing trail. Forward-reference entities not yet ingested as `pending-target`.
7. **Attachments are sources.** Any attachment with forensic weight is filed under `Originals/` and either ingested as its own record or listed in `source_files[]`.

## Failure modes this prevents

- Positions dissolving into paraphrase: "they agreed to it in an email somewhere" is worthless; "their PM conditionally offered X on this date, in this message" is a lever.
- Attribution drift from quoted replies, where a claim gets credited to the person who re-quoted it.
- Threads that were read once, summarized from memory, and never citable again.
