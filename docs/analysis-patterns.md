# Analysis patterns: the techniques on top of the wiki

The wiki holds the facts. These five techniques turn the facts into work that ships. On the real project they lived as habits and prompt structures, not packaged features; writing them down is the first step toward making them formal, for this repo and for the production system both.

Each one says what it is for, how it runs, and the mistake it exists to prevent.

## Review by a panel of critics

**For:** any document whose conclusion someone will fight.

**How:** before shipping, several separate agent sessions each review the draft while playing a specific critic, like the subcontractor's lawyer. (These roles are called personas.) Pick them for their stake in breaking the draft, not their sympathy. A memo on whether a subcontractor owns a scope of work gets the subcontractor's advocate, the owner's lawyer, and an engineer in the relevant field. A board-facing deck got a nine-panelist review against the deck and its source workbooks, producing fourteen corrections applied before shipping. Each critic reviews on its own, against the sources, and reports what it found. A human decides which corrections to make.

**Prevents:** shipping a position the other side takes apart in one reading. If the fake lawyer can beat the memo, the real one will.

## Blindspot analysis

**For:** the moment a piece of work feels complete.

**How:** a dedicated pass that asks only "what is missing?" A search not run. A claim not checked. A document not opened. A scenario not priced. The other side's best argument, stated as strongly as they would state it. Whatever the pass finds becomes the next round of work, or an explicit "not verified" entry in the verification scope ([honest-agent.md](honest-agent.md)). It pairs with the coverage rule: any analysis that stopped somewhere says where it stopped, because stopping silently reads as completeness.

**Prevents:** the failure where every check you ran passed, and the fatal gap was in the checks nobody ran.

## Splitting big jobs across many agents

**For:** work too large for one session, or work where one session would talk itself into its own early guesses: rebuilding a full project budget from scratch, an exhaustive audit, a sweep across hundreds of documents.

**How:** one agent plans the pieces and assembles the results (the orchestrator), and worker agents each take one narrow question with a fresh start and no view of each other's answers (the executors). Checking is a separate stage, done by agents told to disprove the results, not confirm them. The real project's independent budget rebuild ran as five scripted fan-outs totaling forty-seven subagents, with a disprove-it check on every section. The separation is the point: a worker that cannot see the running total cannot nudge its section toward it.

**Prevents:** self-agreement. One long session doing everything slowly bends toward its own first guesses.

**The rejection rule that goes with it:** when the checking stage finds a problem the conclusion rests on, do not patch the draft. Throw it out and rebuild from the corrected evidence. One forecast document's first version was rejected on audit findings and rebuilt whole. Patching stitches new evidence onto reasoning shaped by the old evidence, and the seams always show. That is the Frankenstein draft. Fix wording problems in place; rebuild for anything structural.

## Email-thread reconstruction

**For:** long multi-party email threads that carry positions someone may need to prove later.

**How:** the thread becomes one wiki page with each message as a dated entry: who sent it, who got it, what position it took, each tagged to its party under the evidence rules. The result is a who-said-what-when timeline where an offer, a concession, or the first mention of a dollar figure is a citable event instead of a memory of a long scroll. The thread page links to the things it discusses, so a change order's page shows the email trail next to the pricing trail.

**Prevents:** positions dissolving into paraphrase. "They agreed to it in an email somewhere" is worthless. "Their project manager conditionally offered X on this date, in this message" is a lever.

## Document, or recommend: choosing the tone

**For:** any deliverable that could read as either analysis or advice.

**How:** decide before drafting which one the audience asked for. A documenting piece lists the candidates with objective signals (how long an item has sat open, missing quotes, the other side's own flags) and leaves the decision blank for the owner. A recommending piece states an opinion and says what evidence would change it. On the real project, a triage list shipped as recommendations was pulled back and re-shipped as a neutral candidate list at the owner's direction. The analysis was identical. The tone was wrong.

**Prevents:** the analyst quietly making the owner's call, and the owner quietly handing off a judgment that was theirs to make.

## Packaging these as skills

Each technique above is a candidate for promotion from habit to a named, versioned procedure the agent invokes instead of improvises. The test for promotion: it has run enough times to have a stable shape, its failure modes are known, and writing it down makes the tenth run cheaper than the third. That work is on the roadmap for this repo and the production system it documents.
