# The honest agent: saying only what was checked

[validation.md](validation.md) is the technical gate: the wiki's pages are complete and the numbers match their sources. This page is the behavioral gate: what the agent is allowed to **say** about the work it did. It exists because AI agents share a failure no audit script catches: overstating what was checked. "All figures check out" when three of sixty documents were opened. "Audit clean" when the audit checks page structure, not truth. The rules below were written after exactly those failures, and they are the part of this system most worth stealing for any domain.

## The six rules

**1. No "verified" without saying how much was checked.** Any claim like "verified," "audit clean," "all resolve," or "checks out" must state what was checked and what was not. Not "the workbook is verified" but "49 of 62 source citations checked against their sources, 13 derived aggregates, 0 failed." Acceptable forms: "passed audit X," followed by what X does not check; "N of M checked by method Y"; "taken on trust via [named chain]."

**2. Every deliverable carries a Verification Scope section.** Three required parts: **checked directly** (what was opened, how many, how), **taken on trust** (what was relied on without re-checking, with the chain written down), and **not checked** (the explicit list of everything unsampled). The third part is what stops the agent from telling you what you want to hear, and it is the part an agent will quietly drop if the template does not force it.

**3. Audit scripts state what they do not check.** Every audit writes, next to its list of problems found, a statement of what it looks at and what it ignores. When the agent reports an audit result, it reports that coverage too. "Issues: 0" alone claims nothing.

**4. List it all before saying "done."** Before claiming anything finished, the agent writes out: what it actually opened this session, what it took on trust, what it did not check at all, whether every "verified" phrase states its bounds, and whether each claim carries its evidence tag. If any answer is unknown, the work is not done.

**5. A sample is only a sample.** "5 of 59 checked" means five of fifty-nine. It does not mean "5 of 59, and the rest are probably fine." The 54 unchecked items are exactly as risky as they were before checking started.

**6. Pushback from the human means a rule was broken.** When the human says "this feels perfunctory" or "you are lying by omission," the right response is not a defense or a re-summary. One of rules 1 through 5 was just violated. Redo the work at the level it should have been done the first time.

## Why this has to be written down

None of these rules are exotic. Any good analyst does this without thinking. They must be written down for an AI because the model's writing quality has nothing to do with how carefully it worked: a claim built on three opened documents and a claim built on sixty read identically. Humans signal doubt without meaning to; models do not. So the system makes the bounds mandatory and structural, and treats confident language without bounds as a defect, the same as any other bug.

The rules also survive across sessions by design: they live in the operating rules file and in the agent's persistent memory, so a fresh session inherits the discipline instead of rediscovering it after the next failure.
