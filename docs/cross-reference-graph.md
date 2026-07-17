# The cross-reference graph: how the pages link together

The wiki's value comes from the links between pages, and it compounds as the links get denser. A change order (the paperwork that changes the contract price or scope) links to the RFIs that caused it (an RFI is a formal question from the builder to the architect), the amendment that paid for it, and the pay application (the builder's monthly invoice) where it first shows up as a charge. The links are plain markdown relative paths inside the pages, so the graph travels with the content: no database, no plugin, nothing that breaks when the folder moves.

## Mechanics

Every record (one wiki page per RFI, change order, amendment, or invoice) carries two lists in its header:

- `references[]`: outbound links, each labeled with what the link means (`funds`, `corrects`, `triggered-pco`, `supersedes-snapshot`, and so on).
- `referenced_by[]`: inbound links. A script walks every page, reads every outbound link, and writes the reverse link here. No one maintains this list by hand.

In the body of a record, every document name or numbered reference is a markdown link, never plain text. When a document is taken in, every ID it mentions ("PCO 217 prices CE 455 per RFI 1204") is parsed into a structured link. Pay-application records are the densest source: one monthly pay app can carry thirty-plus links, one to every amendment and change order it bills against.

## Pending targets: the graph wires itself ahead

Documents never arrive in a tidy order. An amendment that mentions twelve change orders lands before ten of them have pages. The rule: create the link anyway and mark it `pending-target`. The checker warns about pending links but never fails on them, and when the missing document finally arrives and gets a page, the link connects on its own.

So the wiki grows toward complete with every document, and never has to start over. Each new page snaps into links that were waiting for it. You never rebuild the graph; you fill it in.

## What density buys

- **Questions that span many pages, answered without starting over.** "Every change order related to this design instruction" is a walk through the links: from the instruction's page, to its topic page, to the change pages, to the amendment that paid for them. No searching across 30,000 files.
- **Patterns no single document shows.** A change request sitting open for fourteen months while its parent amendment paid for everything around it does not show up in the change log or in the amendment. It shows up in the graph.
- **Cheap checking.** Any figure that cannot be walked back through the links to a source file gets flagged automatically.

The operating default: when in doubt, more links beat fewer. Link density is the system's main asset when it is time to build a case.

## Two hygiene rules that keep the graph honest

**If a script can generate it, a script generates it.** The catalog of pages (`index.md`) and every `referenced_by[]` list are rebuilt by script from record headers. Hand-maintained lists drift; regenerated ones cannot.

**No numbers in navigation pages.** Counts, totals, and dollar figures never appear in the index or in topic section headers. A number goes stale the moment a new document arrives. Numbers live in records, cited from sources, or in reports a script can regenerate. This sounds cosmetic and is not: every hand-typed number in a navigation page is a future contradiction the agent will one day cite.
