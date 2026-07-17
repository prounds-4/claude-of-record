---
name: verify-output
description: Provenance audit on a deliverable in outputs/. Trace every numerical claim, attributed statement, and quoted figure back to a Record or Originals/ source. Use before shipping any deliverable to a client.
---

# /verify-output

Audit a deliverable for citation traceability. The contract: every dollar amount, count, attribution, or admission quote must trace to a document under `Originals/` (or to a Record that itself traces).

## Argument

A path to a file OR a stream-iteration folder in `outputs/`. Examples:
- Single file: `outputs/owner-health-report/2025-06-15.md`
- Bundle folder: `outputs/change-order-analysis/v2-2025-06-10-post-review/`
- A `.docx` or `.pptx` filename: for these, ask the user to extract text first or read with the appropriate skill.

When given a folder, recurse through every `.md`/`.docx`/`.xlsx` inside, run the per-file procedure on each, and aggregate findings into one summary report. The bundle's `README.md` (if present) is verified first because it carries the bundle-level frontmatter and `corpus_state:`.

## Procedure

1. **Read the deliverable.** Identify every:
   - Dollar amount (`$NNN`, `$NN.NM`)
   - Count or percentage
   - Attributed quote (`"…": Source`)
   - Attributed claim (`the GC said …`, `the AOR issued …`, `the architect responded …`)
   - Specific date with a factual claim attached

2. **For each claim, find its citation.** A valid citation is one of:
   - An inline markdown link to a Record under `records/`
   - An inline markdown link to a `.txt` sidecar under `Originals/` (with optional line number)
   - A footnote / appendix reference that ultimately resolves to either of the above

3. **For each cited link, follow it.**
   - If it points to a Record: open the Record, find the corresponding cited claim there, follow that to its `Originals/` source.
   - If it points to a `.txt` sidecar: confirm the cited line in the sidecar contains the claim.
   - Two-hop traceability is required: deliverable → Record → Originals/ source.

4. **For uncited or unverifiable claims**, capture them in a finding:
   - Claim verbatim from the deliverable
   - Why it failed: no citation / link doesn't resolve / Record cites the claim but no `Originals/` source / sidecar line doesn't contain the claim

5. **Report** in chat (and optionally to `.claude/health/verify-{deliverable-name}.md` if the user asks for a written report):

```markdown
# Verification report: {deliverable}

_Generated {YYYY-MM-DD} by /verify-output._

## Summary
- Claims audited: {N}
- Verified: {M}
- Failed: {K}

## Failed claims

### "$12,500,000" (line 42 of deliverable)
- Citation: [Amendment-GC-07](records/contracts/Amendment-GC-07.md)
- Record cites: cover sheet line 120
- Sidecar line 120 reads: "$12,500,000"
- **VERIFIED**

### "The GC holds the RFI log in its project management system" (line 67 of deliverable)
- Citation: none
- **FAILED**: no inline citation

[ … etc … ]
```

6. **Attribution-tag check (constitution §5, the ship-time gate for outputs).** The attribution lint hard-gates topic pages but treats non-frozen `outputs/` as advisory. `/verify-output` is the gate for deliverables. Run `python3 .claude/scripts/audit_attribution.py` and inspect `.claude/health/attribution-report.md` for this deliverable's path. Every claim in the deliverable's working `.md` must carry exactly one epistemic-class tag (`{rec-est}` / `{party:<ID>}` / `{infer}` / `{3p}`) per the style guide before shipping. A deliverable frozen before the attribution rules took effect is exempt. Before the deliverable ships, run it through `python3 .claude/scripts/render_output.py <file>` so the shipped artifact carries clean footnote-style attribution plus the exhibit index, and the raw tags never reach the client.

7. **Recommend.** Ship-ready only if every claim is both cited (steps 1-5) AND tagged (step 6). If any claim is uncited, "do not ship; fix the {N} failed citations first." If any claim is untagged or mistagged, "do not ship; tag the {N} untyped claims per constitution §5 first." Otherwise, "this deliverable is ship-ready; render it before sending."

## What this skill does NOT do

- Doesn't fact-check the *correctness* of the underlying source. If a Record cites a sidecar line that says "$X" and the deliverable says "$X", that's verified, even if the figure itself is wrong.
- Doesn't validate cross-source consistency (that's lint territory in some cases, or human analyst judgment).
- Doesn't audit non-claim prose (transitions, framing), only auditable claims.
