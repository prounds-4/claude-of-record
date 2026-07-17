# The 60-second version

Big construction projects run on paperwork. Tens of thousands of documents: contracts, invoices, change orders, questions from the field, meeting notes. The owner pays for everything but the systems holding those documents belong to the builder and the architects. So the owner's side ends up watching a nine-figure project through memory and spreadsheets.

This repo documents a fix. Give an AI agent a copy of every document the owner receives, and it builds and maintains a wiki: one page for every contract change, every invoice, every question and answer, all linked together. Ask it anything and the answer comes with the receipts. Want to know how a $48,500 charge came to exist? The wiki walks you from the question raised in the field, to the architect's answer, to the price, to the signed contract change, each step pointing at the actual document.

The hard part is trust. Nobody should stake a negotiation on an AI's memory. So most of this system is rules that keep the agent honest:

1. Every number links to the exact line of the original document it came from. No source, no claim.
2. What a party says is never treated as fact. The builder saying "the owner asked for this" gets recorded as the builder's position, nothing more.
3. Anything sent to a real audience is frozen forever. Corrections go out as new documents, because someone may still be holding the old one.
4. The agent has to say what it checked and what it did not. "Looks good" is banned.
5. A program re-checks the whole wiki on every change: are the pages complete, and do the numbers actually appear in the documents they point to?

Does it work? On the real project this comes from: the system rebuilt the entire budget from the signed contracts alone and landed within one percent of the number the owner's own expert keeps. It found tens of millions of dollars sitting unused inside the builder's contracts. And when a projection of six months of cash needs was headed up the chain, the owner used it to correct the number by tens of millions of dollars against the closed books before the money moved.

Try it yourself. This runs the whole system on a small made-up project:

```bash
scripts/validate.sh --root example --schemas schemas
```

## The full docs

Read in any order; this sequence builds bottom-up.

1. [the-pattern.md](the-pattern.md): why the owner's seat is the right place for this, and why the contract is the rulebook.
2. [architecture.md](architecture.md): how the wiki is organized, from raw documents to finished reports.
3. [cross-reference-graph.md](cross-reference-graph.md): how the pages link together, including links that fill themselves in later.
4. [constitution.md](constitution.md): how evidence is ranked and whose word counts for what.
5. [provenance.md](provenance.md): every figure traces to a source line, or it does not ship.
6. [validation.md](validation.md): the automatic checks, and why "well formed" is not the same as "true."
7. [honest-agent.md](honest-agent.md): the rules that stop an AI from overstating what it checked.
8. [ingestion.md](ingestion.md): how a new document becomes a wiki page.
9. [extraction.md](extraction.md): getting documents out of other people's systems.
10. [analysis-patterns.md](analysis-patterns.md): the review techniques used before anything ships.
11. [deployment.md](deployment.md): run it on your own machine; share a folder only if teammates need to live in it too.
12. [results.md](results.md): what the system found on the real project.
13. [failure-modes.md](failure-modes.md): everything that broke, and what each failure taught.
