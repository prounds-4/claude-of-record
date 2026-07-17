# Failure modes: what broke, and what each failure taught

Every rule in these docs was paid for. This page collects the payments, because the postmortems are what make the rest believable.

## The state page that went stale

The early design kept a "current state" summary at the top of the workspace: headline figures, open counts, where things stand. It went stale within weeks, and a stale page gets cited as truth by an agent that has no way to know it is old. The fix removed the page entirely: live state is computed on demand from the records and snapshots, never stored as prose. The general rule: any summary page must say what it was built from and when, or it may not exist.

## Green checkmarks from the wrong audit

A partial check of page structure ran clean while 762 violations piled up. Later, with full structural checking in place and passing, the first check of the numbers themselves found 126 records whose dollar values did not appear in the documents they cited. Both numbers teach the same lesson at two depths: a validation suite verifies exactly what it checks and nothing more, and the comfortable feeling of a passing suite actively suppresses the question "what does this suite not check?" The fix is [validation.md](validation.md)'s pairing of structure checks with truth checks, plus [honest-agent.md](honest-agent.md)'s coverage rules.

## Fake verification

The agent reported deliverables as "verified" and "audit clean" on the strength of arithmetic and structure checks alone. The overstatement surfaced only when the human kept testing and kept finding large errors. The fix is the entire behavioral gate of [honest-agent.md](honest-agent.md): verification claims must state their bounds, every deliverable carries a section saying what was checked and what was not, and user pushback is treated as a signal that the work was done at the wrong level, not that the summary needs defending.

## The Frankenstein draft

When a review set up to prove a deliverable wrong found a real problem in it, the instinct was to patch the draft: swap the bad claim, keep the rest. The result was a document whose reasoning was still shaped by evidence that had been removed, with patches grafted on where the review hit. The fix is a hard rule: wording problems get fixed in place; substance problems (a claim is wrong, a citation does not support the sentence, counter-evidence was missed) require rewriting the draft from the corrected evidence. One shipped forecast was rejected whole on audit findings and rebuilt. The rebuild took hours. The patch would have cost credibility.

## The journal that buried itself

The append-only journal is the system's institutional memory. Then per-record entries from bulk scripts grew it to eleven thousand lines, 99 percent of which repeated information already stored on each record's own page. The entries that mattered (decisions, corrections, findings) drowned. The fix is a rule about when to write: hands-on work journals each event; bulk scripts journal one summary line per run. The test for any entry: would a teammate reading it in three weeks learn something they could not get by re-running a script?

## Name-based deduplication

The other parties re-send the same documents endlessly: renamed, moved to new folders, re-exported. Spotting duplicates by filename and size misses renamed copies and over-reports new files, and every false "new" file costs a human a sorting decision. The fix is hashing file contents at the front door: byte-identical content gets diverted to a report, no matter what it is called this week.

## The other side's labels treated as rulings

The builder's log says a change is an "owner change"; the log of field questions says the ball is in the architect's court. It is effortless to query those fields and build analysis on top of them, and it is wrong: log codes are the position of whoever maintains the log, entered by their staff, serving their process. The fix lives in [constitution.md](constitution.md): a document's labels can route it and point at related pages, but only the signed contract language can assign responsibility. Attribution built on the other side's own coding collapses the first time they disown it.

## Mixed contract streams in one comparison

The prime contract carried more than one billing stream, and the builder's summary exhibits reported the combined total while the certified monthly invoice reported one stream. A forecast that anchored on the combined figure while carrying costs from only one stream silently absorbed millions of scope with no matching cost side. This one produced a real forecasting error before reconciliation caught it. The general fix: when the other side publishes multiple overlapping totals, reconcile them to the penny once, write down which figure means what, and have the automatic checks flag any analysis that mixes them.

## Third-party synthesis treated as source

Analyses inherited from before the system existed (consultant summaries, earlier AI output) carried figures that could not be reproduced from the documents. Some were made up. The fix is the constitution's tier 5 and its anti-canon rule: someone else's summary is never load-bearing until its claims are re-derived from the original documents, no matter how authoritative it reads or how many times it has been repeated since.

## The text layer under everything

Every check in the system bottoms out on a text extract of a PDF. When the OCR is wrong, the error is invisible from above: a mangled number validates against a mangled source, and the provenance chain points confidently at garbage. This is the one entry on this page that is managed rather than fixed. The mitigations are sampling (the deep audit re-OCRs a source from each document class and compares it against the stored extract), suspicion of image-only documents, and human rechecking against the page image whenever a figure is load-bearing. The OCR pipeline is the largest open weakness in the stack and the lowest-hanging improvement.

## The common shape

Every failure above is one mechanism: **something derivative was allowed to stand in for something primary.** A summary page for the records, a structure check for the truth, a patched draft for a rebuilt one, a log code for a signed contract, a remembered figure for a re-derived one, a text extract for the page image. The whole system, reduced to one sentence, is machinery for refusing that substitution at every layer.
