---
name: multi-persona-review
description: Adversarial pre-ship review of a deliverable by independent personas chosen for their stake in breaking it. Use before shipping any analysis whose conclusion someone will contest, or when the user asks for a red-team, panel, or persona review of a draft.
---

# Multi-persona review

Review a draft deliverable through several independent adversarial personas before it ships. The purpose is to find the argument that dismantles the draft while it is still cheap to fix.

## When to run

- Any deliverable going to an audience with a stake in rejecting it (a counterparty, counsel, a board).
- Any memo that attributes responsibility or money to a named party.
- On request: "red-team this", "review this as X would".

## Procedure

1. **Cast the panel.** Choose 3 to 9 personas by stake, not sympathy. The test for a good persona: they win if the draft is wrong. For a scope-responsibility memo: the counterparty's advocate, the owner's counsel, a licensed engineer in the discipline. For a budget deliverable: a skeptical CFO, an estimator who priced the original work, an auditor who only checks arithmetic. Always include one persona whose only job is the sources (does each citation support the sentence it anchors?).
2. **Isolate the reviews.** Each persona reviews independently against the draft and its cited sources. No persona sees another's findings. Run them as separate subagents where the harness allows; otherwise run them sequentially in fresh contexts.
3. **Demand findings, not impressions.** Each persona returns: the claim attacked, the evidence or reasoning that breaks or weakens it, and a severity (fatal / material / cosmetic). "Reads fine" is not a finding.
4. **Consolidate.** Merge duplicate findings; keep the strongest phrasing of each attack. Rank fatal first.
5. **The human decides which corrections apply.** Present the consolidated findings with a recommended disposition per finding. Apply what is accepted.
6. **Route the fix by kind.** Cosmetic and prose findings: fix inline. Structural findings (a claim is wrong, a citation does not support the sentence, counter-evidence was missed): regenerate the affected analysis from the corrected evidence. Never graft patches onto reasoning shaped by evidence that has been removed.

## Failure modes this prevents

- Shipping a position the counterparty's actual advocate takes apart in one reading.
- Reviewer personas that agree with the draft because they were cast as friendly.
- The Frankenstein draft: original synthesis with patches grafted where review hit.

## Output

The consolidated findings table, the dispositions, and (if structural findings were accepted) a regenerated draft. Record the panel composition in the deliverable's verification-scope section.
