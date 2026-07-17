---
name: blindspot-analysis
description: A dedicated what-is-missing pass over a piece of work that feels complete. Use before declaring any analysis, audit, or deliverable done, or when the user asks what has not been checked.
---

# Blindspot analysis

A pass that asks only one question: what is missing? It runs when the work feels complete, because that feeling is exactly when unexamined gaps are least visible.

## When to run

- Before any deliverable ships.
- Before declaring any phase or audit complete.
- On request: "what are we missing", "blindspot check".

## Procedure

Work through the checklist. For each item, either name the gap or state concretely why there is none. "N/A" without a reason is not an answer.

1. **Search modalities not run.** The corpus was searched one way (by ID, by folder, by date). What would a different axis surface: by dollar amount, by party, by time window, by document type never opened?
2. **Claims not verified.** List every load-bearing claim in the work. Which were checked against a source in this session, which were trusted from an earlier record or synthesis, and which were never checked at all?
3. **Sources not opened.** Which documents does the analysis implicitly rely on without anyone having opened them? Which known-to-exist upstream documents (check the external index) were never pulled?
4. **Scenarios not priced.** For any forecast or exposure number: what assumption, if wrong, moves the answer most, and was the other branch computed?
5. **The counterparty's best argument.** State the strongest case against the conclusion, steelmanned. If the work never engages it, that is the gap.
6. **Silent truncations.** Anywhere the work bounded itself (top N, sampled M, skipped a class), is the bound stated in the output, or does the result read as exhaustive?

## Disposition

Everything found goes to exactly one of two places:

- **The next round of work**, if it is worth closing now.
- **The "not verified" subsection of the verification scope**, stated plainly, if it is not.

A blindspot may never be silently dropped. The pass fails if its output is empty; there is always at least one honest entry for the not-verified list.

## Failure mode this prevents

The unknown-unknowns failure: every check that ran passed, and the fatal gap was in the checks nobody ran.
