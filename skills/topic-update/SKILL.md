---
name: topic-update
description: Re-synthesize a topic page from its declared source_records[]. Use when the user asks to update, refresh, or rebuild a topic page, or when /lint-wiki flags a topic as stale. Argument is the topic slug.
---

# /topic-update

Re-read every Record in `topics/{slug}.md`'s `source_records[]` frontmatter, rewrite the narrative body, and stamp `last_synthesized` to today.

## Argument

The topic slug: kebab-case, no `.md` extension. Example: `asi-09-canopy`.

## Procedure

1. **Read** `topics/{slug}.md`. If it doesn't exist, ask the user to author the frontmatter first (slug, title, status, source_records[]) before running this skill.

2. **Read every Record** in `source_records[]`. If any path doesn't resolve, stop and report the broken link.

3. **Synthesize the body** in this structure:
   - **Opening** (1-3 sentences): what the thread is and why it matters.
   - **Chronology** (bulleted or short paragraphs): events in date order, each with at least one inline citation to a `source_records[]` entry. Format: `On 2025-03-15, Amendment 7 funded the canopy scope ([Amendment-GC-07](../records/contracts/Amendment-GC-07.md))`.
   - **Open questions / contradictions**: anything where the sources disagree or leave ambiguity. This is where forensic value compounds.
   - **Status**: current resolution state, with citation.

4. **Provenance discipline.** Every numerical claim, attributed statement, or date must carry an inline citation. Use markdown relative paths from `topics/` (one `..` to escape into the workspace, then `records/{class}/{ID}.md`).

5. **Update frontmatter:**
   - `last_synthesized: YYYY-MM-DD` (today)
   - `synthesized_by: <current user>` (ask if unknown)
   - Optionally adjust `status` if the underlying records show resolution.

6. **Append to `log.md`:** `## [YYYY-MM-DD] topic-update | {slug}`.

7. **Run `/lint-wiki`** to verify the freshness contract is now satisfied and no claims are uncited.

## Constitution §6: register conflicts found in synthesis

When the `source_records[]` disagree on the same fact, the "Open questions / contradictions" bullet is enough for a soft ambiguity. A **material** conflict (same dollar value, date, attribution, or status asserted differently by two sources) requires more, per `constitution.md` §6:

1. Rank the conflicting sources by §2 tier, then §3 party axis, then the §2 tie-breakers. Adopt the higher-authority value in the narrative and tag it with its §5 epistemic class.
2. Create or update a Discrepancy Record at `records/discrepancies/Discrepancy-NNNN.md` (schema `_schemas/Discrepancy.yaml`), then cite it from the topic body where the conflict surfaces.
3. If the tie does not break on §2/§3, set the Discrepancy `status: escalated` and raise it with the user. Do not resolve it by choosing the more convenient reading.

Every synthesized claim in the rewritten body carries exactly one epistemic-class tag per §5 and the style guide (Attribution tags). The attribution audit script reports untagged claims.

## When to skip vs. proceed

- If `last_synthesized` already equals the most recent `ingested_at` among source records, the topic is already fresh. Confirm with the user before regenerating (you may be wasting their time).
- If a `source_records[]` entry was deleted, do not silently drop it from the list. Stop and ask the user how to handle it.
