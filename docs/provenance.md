# Provenance: the paper trail behind every claim

Provenance is the paper trail from a claim back to its source. The rule here is one sentence: every dollar amount, count, attribution, or quoted statement, anywhere in the wiki or in anything that ships, must trace to a document in the read-only source tier. This page is the set of working habits that make that sentence true in practice.

## Open the source before citing it

Wiki pages are summaries, not evidence. Every claim a conclusion rests on must trace to an exact line in a source text file or PDF that the agent opened **in the current working turn**. Quoting a page's summary, its header fields, or the link graph does not count.

This is the anti-skimming rule, and it targets the specific way AI systems fail: the model writes fluently from its own earlier notes, several steps removed from the source, and the result sounds exactly as confident as a real citation. The fix is mechanical: if the agent has written several claims without opening a source, it stops and goes back to the documents before continuing.

## Do not recall. Re-derive.

The agent's memory files, prior conversations, and the wiki's own summary pages are for orientation, never for citation. A figure remembered from last week's session gets looked up in the signed document again before it ships again. This costs compute and is worth every bit of it. The alternative is a system that slowly replaces its evidence with its recollection of its evidence.

## How citations work

- Every figure carries an inline link to the `.txt` text extract of the source (preferred) or to the PDF, with the line number written out in prose when the link cannot carry one.
- Text extracts are generated once from the source (`pdftotext -layout`; OCR first for scanned documents) and refreshed only if the source is re-OCR'd. An automatic check compares extract and PDF timestamps to catch stale extracts.
- Each source file carries a type tag that says how to cite it: prose documents need line citations; spreadsheets are cited by row and section description, never by line number; drawings are only checked to exist, because their text extract is geometry noise, not readable prose.

## A citation is necessary, not sufficient

The paper trail proves a claim traces to a source. The constitution ([constitution.md](constitution.md)) decides how much that source is worth once found. The two rules work together: a perfectly cited claim from a tier 5 source is still not a fact, and an uncited claim from a tier 1 source still fails the lint. A report ships only when every figure passes both.

## The ship gate

Before anything goes into the frozen output tier, a verification pass walks every number, attributed statement, and quote back to its source. A figure that cannot trace does not ship. On the real project this gate is a script-assisted procedure invoked by name, and it is the single most-used quality control in the system: cheap enough to run on every shipping, strict enough that passing it is the definition of ready.
