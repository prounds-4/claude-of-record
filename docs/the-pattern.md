# The pattern: a project brain for the owner's side

## The seat

Construction projects run on information, and the people with the least of it sit on the owner's side. The owner's representative does not do the work and does not own the systems that track it. The log of RFIs (an RFI is a formal question from the builder to the architect) lives in the builder's Procore account. The history of change orders (the paperwork that changes the contract price or scope) lives in the builder's spreadsheets. The design record lives with the architects. The owner's rep is supposed to see the project clearly while holding read-only access to almost everything, and sometimes not even that: on the real project behind this repo, the owner saw the builder's RFI system only as weekly PDF snapshots.

Before AI agents, the job was pure reaction. Nothing built in that seat compounded, because the day went to consuming everyone else's paperwork in everyone else's formats.

## The insight

An AI agent changes the seat. If you can reliably capture every document as it arrives, you can build a working model of the whole project without a seat in anyone else's system. OCR each document (OCR turns a scanned image into searchable text), then have the agent build a wiki from the pile. A wiki here means a folder of linked pages the AI writes and maintains: it reads each source once, writes a page, and links it to the others, instead of re-searching the raw pile on every question. The idea comes from [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Do that, and the owner's side can connect dots across the project better than anyone inside it.

The surprise is that the counterparties' systems turn out not to matter. Procore, SharePoint, the scheduling software, the accounting packages: they are mutually incompatible, and the wiki never has to reconcile them, because it is a layer of meaning built on top of their exports. Each party's system is deep in one lane. The builder's knows the builder's log, the architects' knows the design record, and none of them spans the others, because nobody's job is to join them. The owner's secondhand pile is the only place everything lands, and once it is cross-linked, the wiki holds a broader picture of the project than the systems the documents came from: a dollar walks from a field question to a meeting minute to an executed change order, and from the owner's ledger down through the monthly pay application to the change orders and budget lines beneath it.

The real project made the case concrete: tens of thousands of documents in a SharePoint library, more arriving daily, thousands of RFIs, a long run of serial contract amendments with no consolidated master. At that scale, human-maintained spreadsheets are not oversight. They are theater.

## The constitution move

A wiki alone is just a search index with better manners. What turns it into a tool for building a case is giving it a point of view. And on a construction project, a point of view nobody can argue with already exists: the construction contract itself.

A standard general-contracting agreement spells out how the project's information is supposed to flow. RFIs, change orders, pay applications (the builder's monthly invoices), notices: each has a defined owner and a deadline. The budget and schedule are attached as exhibits. Running a project strictly by the contract is the state of the art, tested over decades, and hard for any counterparty to argue against. An AI agent is, by design, very good at following written rules. So the contract becomes the system's constitution: the rulebook for how evidence is weighed, whose statements count as fact and whose count only as one party's position, and what happens when sources disagree. [constitution.md](constitution.md) spells out the full doctrine.

The combination is the pattern this whole repository documents:

1. **A document collection**: every document the owner receives, kept unchanged, OCR'd, machine-readable.
2. **A graph**: one wiki page per thing the project produces (each RFI, each change order, each amendment, each pay application), densely linked to the others.
3. **A constitution**: contract-grounded rules for how much weight each source gets and who gets credited with saying what.
4. **An enforcement layer**: automated checks that every figure traces to a source. This layer is as large as the content itself.

## What it is not

The system is only as good as its inputs. Documents the owner never receives do not exist in it. It works from snapshots, not a live feed. It has no read on personal dynamics, and those decide a lot on a big job. And it does not assign blame: the pages establish what happened and when, and a human decides who is responsible.

That last point carries weight and comes up throughout these docs. The system's product is a memory no one on the project can out-argue. What to do about it stays with the owner.
