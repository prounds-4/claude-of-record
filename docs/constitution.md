# The constitution: how evidence is weighed

The operating rules tell the agent how the system runs: filenames, pipelines, checks. The constitution tells it how to weigh what it reads: which document wins when two disagree, and whose word counts for what. The two documents never overlap, and the constitution is read first, before any question is answered. It is also the most portable piece of the whole system: almost none of it is construction-specific once you swap the document types.

## Five tiers of documents

A tier is just a rank. When two sources speak to the same fact, the higher tier wins. Tier 1 is highest.

1. **Signed contract documents** (the word for these in contract law is "instruments"). The agreements themselves and everything that changes them: the prime contract, executed amendments, executed change orders. For any given term, the document that controls is the latest signed one that changes that term.
2. **Formal on-the-record documents that are not the agreement itself.** Architect's instructions, formal answers to field questions (RFI responses), formal notices, letters from counsel stating a position. These prove what was instructed or claimed, not what the contract finally says.
3. **Logs and trackers kept by one party.** Change-order logs, RFI trackers, submittal logs, pay applications, schedule updates. Reliable for what they track as of their snapshot date, but they are one party's administrative summaries, so tiers 1 and 2 beat them.
4. **Day-to-day communications and observations.** Meeting minutes, field reports, informal email. Reports from independent third parties (testing labs, inspectors) sit here too, but they count for more on the specific physical fact they observed, because the observer has no money riding on the answer.
5. **Someone else's summary.** Prior consultant analyses, prior AI output, and the wiki's own summary pages when read as a source instead of rebuilt from the documents. Never the basis for a factual claim in anything that ships without going back up to a higher tier.

Tie-breakers, in order: signed beats draft; later beats earlier; a specific document beats a general log entry; an independent observation beats an interested party's story; signed and dated beats undated; and the operative document beats any summary or copy of it. That last one earned its place. On the real project, an amendment's cover sheet transposed digits of an eight-figure sum, and only the signed document inside carried the right number. Trace every figure to the document itself, never to its cover sheet.

## Whose word counts: two separate questions

**Question A: what did the owner want and direct?** The people who can answer this are ranked from principal, to advisors, to the contracting entity itself. Rank on this question never turns opinion into fact: when someone on the owner's side characterizes the other party, that is still one side's position, however senior the speaker.

**Question B: what does the contract mean?** Here the owner's own lawyers get special treatment: their reading of the contract becomes the working interpretation the analysis runs on, second only to the signed documents themselves. Three guardrails stop this from swallowing the system. First, the elevation covers interpretation only, not facts: a lawyer repeating a disputed fact is just another party statement. Second, it applies to owner-side counsel only: the other party's lawyer is arguing their client's side and is never elevated. Third, the label never comes off: even while counsel's reading controls the analysis, it stays marked as counsel's position, not as truth.

**The other parties** (contractor, architects, engineers, subcontractors) are the best source on their own scope, their own documents, and their own prices. But when one of them blames someone else, that is a party arguing its own side. It gets recorded as their position, never as fact.

## Metadata: trust it for filing, never for blame

Structured metadata (status fields, assignments, filenames) is trusted for routing documents around, never for deciding who is responsible for a cost. An RFI's "ball in court" field says whose desk the question sits on, not whose fault the problem is. A change order's "status" is the contractor's bookkeeping, not proof the owner owes the money. A file named "claim" is not evidence a claim was filed. Responsibility rests on the text of the documents, weighed by tier. This rule exists because log metadata is the easiest thing to query, which makes it the easiest thing to over-trust.

## Four claim classes

Every claim the agent writes carries exactly one label saying what kind of knowledge it is, and the label travels with the claim wherever it is copied:

| Class | Meaning | Truth value |
|---|---|---|
| `rec-est` | A tier 1 or 2 document states it | Recorded as fact |
| `party:<X>` | A named party's position | True only as "X asserts Y" |
| `infer` | The analyst's own conclusion drawn across records | An argument, defensible from the cited evidence, never stated as fact |
| `3p` | A pre-existing summary from outside the document set | Lowest; flagged to be rebuilt from real sources |

The binding rule: any claim carrying a dollar figure, count, date, attribution, or quote must fit exactly one class, and the class must be visible to the reader. In the reference system the tags are literal inline tokens checked by the automated lint.

## When sources disagree

A conflict is two sources stating the same fact with materially different content. The procedure: spot it, rank the sources by tier and party weight, adopt the higher-ranked value with its class and citation, and record the conflict as its own first-class discrepancy page capturing both sources, the rule applied, and the remaining risk. Never resolve a conflict by averaging, guessing, or picking the convenient figure. If the rules above do not break the tie, hand it to the human.

A detected conflict is an asset, not an inconvenience. The list of discrepancies is itself evidence.

## The anti-canon rule

An opinion never hardens into fact by being repeated, getting old, or getting copied into a more formal document. An inference in a wiki summary page carries into a shipped report only as a labeled inference. A party's story stays a party's story in the record, in the page that cites the record, and in the report that cites the page. No finding may ship whose support chain bottoms out only in inference or someone else's summary. This is the rule that stops an AI system from laundering its own earlier output into evidence.
