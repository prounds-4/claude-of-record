# Claude of Record

**An agent-maintained wiki for construction owner's representatives. The party who answers for what the project knows.**

Construction already names who answers for the design: the Architect of Record, the Engineer of Record. This is the third seat. Point an agent at every document the owner receives and it builds and maintains a cross-referenced, provenance-disciplined wiki it can ship forensic analysis from: change-order triage, allowance forensics, independent budget rebuilds. Documented from a production system running on a nine-figure project, operated by one analyst. On the real project it rebuilt the budget bottom-up to within 0.8 percent of the owner's book, surfaced an eight-figure pool of unspent allowances sitting inside trade contracts, and corrected a six-month cash projection by tens of millions of dollars against the closed books before the number went up the chain. If you hold a large document corpus and a read-only seat, this is for you.

## The method in five lines

1. Sources are immutable and OCR'd; every figure in the wiki traces to a source line, or it does not ship.
2. One record per project entity (RFI, change order, amendment, pay app), densely cross-linked; links to entities that do not exist yet resolve themselves when the document arrives.
3. The contract is the constitution: evidence is tier-ranked, and a party's assertion never becomes a fact by repetition.
4. Deliverables freeze the moment they ship; corrections are new artifacts, never edits.
5. Validation is structural and semantic, and the agent must state what it verified, what it trusted, and what it did not check.

## Quickstart

```bash
git clone https://github.com/prounds-4/claude-of-record
cd claude-of-record
scripts/validate.sh --root example --schemas schemas
```

That runs the four-check validation suite (index, cross-references, structural audit, semantic audit) against a tiny fictional project and passes. Change a dollar figure in `example/records/pcos/PCO-217.md` to something not in its cited source and it fails. Python 3 and pyyaml are the only dependencies.

Scope, stated plainly: the shipped suite verifies structure and that dollar figures extracted into records appear in the text of the sources they cite. It does not read line-number citations, does not check figures in topic pages, and does not compare a sidecar against its original PDF. On the production system those gaps are covered by deep-audit and ship-time checks described in [validation.md](docs/validation.md) and [honest-agent.md](docs/honest-agent.md); the rule that verification claims state their own bounds applies to this suite too.

## What is in here

| Directory | Contents |
|---|---|
| `docs/` | The method, in 13 short docs: the pattern, the architecture, the graph, the constitution, provenance, validation, the honesty rules, ingestion, extraction, analysis patterns, deployment, results, and failure modes. Start with [the 60-second version](docs/README.md). |
| `templates/` | Fill-in-the-blanks operating rules, constitution, and the invariants config that keeps project facts out of code. |
| `schemas/` | 30 record types with closed-world frontmatter definitions. |
| `skills/` | The seven wiki procedures plus four analysis patterns (multi-persona review, blindspot analysis, thread reconstruction, orchestrated analysis). |
| `scripts/` | The enforcement layer: structural and semantic audits, index rebuilder, reference resolver, content-hash gate, write lock, `validate.sh`. |
| `example/` | The runnable fictional corpus the quickstart uses. |

If you are skeptical, start with [failure-modes.md](docs/failure-modes.md): everything that broke, and what each failure taught.

To deploy on a real project: copy the templates into a new workspace as `CLAUDE.md` and `constitution.md`, fill them in, put `schemas/` at `.claude/skills/_schemas/`, `skills/` at `.claude/skills/`, `scripts/` at `.claude/scripts/`, and the invariants file at `.claude/project-invariants.yaml`. The example shows what a conforming record looks like.

## What is not here

The real project's documents. Every name in the docs, schemas, skills, and example (Ridgeline Ventures, Thornmere Builders, Summit Steel, and the rest) is invented, and every record ID and dollar figure in an example is fictional. Any resemblance to a real firm or person is coincidental.

## Lineage

The core pattern is Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): the LLM reads sources once and maintains a persistent, interlinked wiki instead of re-searching documents on every question. This repo is that idea after contact with a construction dispute: an immutable source tier, an evidentiary constitution, frozen deliverables, semantic validation, and a behavioral honesty gate.

## License

Code and configuration: MIT. Documentation: CC BY 4.0. See [LICENSE](LICENSE).
