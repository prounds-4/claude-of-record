# Fennmore Commerce Center Wiki: Operating Rules (example instance)

This is a miniature filled-in instance of
[templates/CLAUDE.template.md](../templates/CLAUDE.template.md), kept just
large enough for the validation suite to run end to end. A real deployment
fills in the full template.

## Project identity

- **Project:** Fennmore Commerce Center (fictional)
- **Owner:** Ridgeline Ventures LLC
- **GC / CM:** Thornmere Builders, AIA A102 + A201 as modified
- **Architect:** Atelier North (design); Crestview Architects (of record)
- **Structural:** Baseline Structural

## Rules in force

The architecture, provenance, cross-referencing, and validation rules of the
template apply unchanged: sources under `Originals/` are immutable and cited
by sidecar line; records are summaries, never evidence; every figure in a
record or topic traces to a source; `referenced_by[]` is machine-maintained;
`index.md` is generated, never hand-edited.

## Validate

From the repository root:

```bash
scripts/validate.sh --root example --schemas schemas
```
