# Verification Scope template

This template MUST appear in every deliverable README (frozen `outputs/` deliverables, workbook sidecars, memos, docx).

The "Not verified" subsection is the most important. It's the section that, when omitted or hand-waved, lets sycophancy and overstatement slip through.

Per the wiki's Behavioral Definition of Done (CLAUDE.md).

---

## Copy this into the deliverable README

```markdown
## Verification scope

### Contextually verified
- [Item 1: what was opened, sample size (e.g., "9 of 59 bid-comp scopes"), method (e.g., "opened source PDF, located Subcontract/Purchase Agreement Amount line on bottom-of-document page, confirmed against CSV row")]
- [Item 2: ...]
- [Item 3: ...]

### Trusted upstream
- [Item 1: what was relied on without independent re-check, the verification chain (e.g., "wiki PCCO Record → wiki audit_semantic.py → PCCO source PDF"), and whether the trust is acceptable for the deliverable's purpose]
- [Item 2: ...]

### Not verified
- [Item 1: explicit content NOT checked (e.g., "50 of 59 bid-comp scopes were not independently spot-checked against source PDFs"). Why not. What would close the gap.]
- [Item 2: ...]
- [Item 3: ...]
```

---

## Rules for filling it out

1. **The "Not verified" section must exist and be honest.** If you didn't check something, say so. If you sampled, give the sample bounds.
2. **No hedge words.** "Largely verified", "mostly checked", "approximately": these hide what's actually been done. Be exact: "9 of 59" not "most".
3. **Sample size always.** Don't say "key bid-comp scopes verified". Say "9 of 59 verified at the source-PDF Subcontract/Purchase Agreement Amount line; 50 not verified at source".
4. **The verification chain is part of trust.** Don't say "trusted upstream" alone. Say "trusted upstream via X → Y → Z; X's audit script is internal-consistency only and does not check Y against Originals/".
5. **No "comprehensive" or "exhaustive" claims** unless literally exhaustive (every item in the universe checked individually).

## Anchor invariant

> Number of "verified" claims in the body == number of items in "Contextually verified" subsection.

If a body claim doesn't appear in the Verification scope, either qualify the body or expand the scope.

## When to write this

- BEFORE the deliverable ships, not after
- The "Not verified" enumeration is the gate; if you can't fill it in honestly, the deliverable isn't ready

## Why this exists

Deliverables have shipped through multiple iterations each claiming verification levels that exceeded what was actually checked. This template makes the gap between claimed and actual verification impossible to hide.
