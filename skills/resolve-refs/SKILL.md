---
name: resolve-refs
description: Walk records/ and topics/, parse outbound markdown links, populate referenced_by[] on every target, write broken-links report. Use after ingestions or when cross-references seem stale.
---

# /resolve-refs

Build the inbound reference graph. Every Record and topic page declares its outbound links inline (markdown relative paths) and in frontmatter `references[]`; this skill writes the inverse onto every target's `referenced_by[]`.

## Procedure

1. **Pass 1: collect outbound edges.** For every `records/**/*.md` and `topics/*.md`:
   - Parse the body for markdown links pointing at `records/{class}/{ID}.md` or `topics/{slug}.md`.
   - Parse the frontmatter `references[]` for explicit declared edges.
   - Each edge: `{source_path, target_path, relationship}`. Relationship comes from frontmatter (`corrects`, `funds`, `bundled-into`, `references`, etc.) or defaults to `mentions` for body-only links.

2. **Pass 2: populate inbound.** For every Record or topic page that is the target of at least one edge:
   - Read its current frontmatter.
   - Replace `referenced_by:` with the deduplicated list of `{source: <path>, relationship: <rel>}` entries pointing at it.
   - Sort entries by source path for stability.
   - Write back.

3. **Pass 3: report broken outbound links.** For every link in step 1 whose target file doesn't exist:
   - Add to `.claude/health/broken-refs.md` (overwrite the file each run).
   - Pending-target references (frontmatter `status: pending-target`: target Record doesn't exist yet) go to a separate `.claude/health/pending-refs.md` and don't count as broken.

   Format:
   ```markdown
   # Broken outbound references

   _Regenerated {YYYY-MM-DD HH:MM} by /resolve-refs._

   ## records/{class}/{ID}.md
   - → `records/contracts/Amendment-GC-99.md` (does not exist)
   - → `records/asis/ASI-99.md` (does not exist)

   ## topics/asi-09-canopy.md
   - → `records/changes/Change-9999.md` (does not exist)
   ```

4. **Append to `log.md`:** `## [YYYY-MM-DD] system | resolve-refs | {N edges, M broken}` (counts in the log are fine).

## Conventions

- A Record pointing at itself is silently dropped (self-references are no-ops in `referenced_by`).
- Frontmatter `references[]` declarations and body links can both contribute to the same edge. Dedupe on `(source, target, relationship)`.
- If a link points outside `records/` or `topics/` (e.g., into `Originals/` or `outputs/`), it's a source citation, not a cross-reference. Don't include it in `referenced_by[]`. Validate it exists; flag in broken-refs if not.
- Don't modify a file's body during resolve-refs. Only frontmatter `referenced_by[]`.

## When the user asks to "rebuild the graph"

That's this skill. Run it.
