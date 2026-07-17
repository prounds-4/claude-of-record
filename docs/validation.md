# Validation: well formed is not the same as true

The checking layer is as large as the content layer, because a document wiki you cannot trust is worthless. The design principle: **never confuse "well formed" with "true."**

- **Structurally valid** means the page is well formed: the header fields parse, required fields exist, file paths resolve, IDs match filenames. Cheap to check. Catches broken pages, not wrong ones.
- **Semantically correct** means the page is true: the extracted values actually appear in the source documents, obey the project's fixed facts, and agree across pages. The harder check, and the one that matters for anything that ships.

The difference was paid for twice on the real project. A partial structural check used in early sessions let 762 violations pile up before a full audit caught them. Then, after the structural audit ran clean end to end, the first-ever semantic audit (does every extracted dollar value actually appear in the cited source text?) found 126 more violations that had accumulated silently behind the green checkmarks. Both audits now run automatically, and a pass means both passed.

## The validation suite

One wrapper script is the definition of done: no phase, session, or deliverable is claimed complete until it exits clean. What it runs:

1. **Index rebuild.** Regenerate the master catalog from the pages on disk. No stale entries, no missing pages.
2. **Cross-reference resolution.** Recompute the incoming-link graph; report broken links and counts of links waiting on pages that do not exist yet.
3. **Structural audit.** Per page type: required fields, allowed values, source file and text extract exist, ID matches filename, dates make sense, body links resolve, plus a check that flags any header field the page type does not declare.
4. **Semantic audit.** Extracted values appear word for word in the cited source text; the project's fixed facts hold (an invariant, a fact that must be the same everywhere it appears, like a base contract sum, is stated once and checked everywhere); pages agree with each other; outliers and vendor names get sanity checks.
5. **Deep audit.** Re-OCR a sample source from each document class and compare it against the stored text extract, to catch extracts that have drifted from their PDFs.
6. **Attribution gate.** Every claim on a summary page carries exactly one claim-class tag, and no shipped finding rests only on inference-class support ([constitution.md](constitution.md)).
7. **Self-test.** A regression harness for the audit tools themselves: the extractors and audit logic run against known-good and known-bad test files, so the auditors get audited.
8. **Idempotency.** The word means: running it twice changes nothing. Every bulk import handler re-runs against the current wiki and must create zero pages. If re-running the pipeline on unchanged input changes anything, that is a bug by definition, and this check catches a whole class of quiet corruption.
9. **Randomized sampling audit.** A random sample (fixed seed, so it repeats) of pages checked field by field against the source exports, for page classes too large to verify one by one.

Non-blocking reports (stale text extracts, schema drift) run alongside and land in a health folder for review without blocking anything.

## Rules that keep the suite honest

- **If any check fails, fix the cause before declaring complete.** No partial success, no "structural passed but." Anything genuinely unfixable in the session goes on a known-bad list with an explicit reason and a target for cleanup.
- **New page type, new checks.** When a page type is added, both its structural schema and its semantic fixed-fact checks are written before its import handler is. An unaudited page type is a place where errors accumulate unobserved.
- **Audit scripts report their own coverage.** Every audit states what it checks and what it does not. "Zero issues" from a script means nothing until you know what the script cannot see. That rule becomes a behavioral one in [honest-agent.md](honest-agent.md).
