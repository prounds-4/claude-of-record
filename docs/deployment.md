# Deployment: run it local first

The wiki is a folder of plain text files. That gives you two ways to run it, and the right one comes down to a single question: does anyone besides the operator need to live inside the wiki?

## One operator: run it local

If one person runs the system, keep the whole workspace on a local disk. This is the recommended default, and it is the better setup, not a fallback:

- No sync delay between writing a file and seeing it.
- No locking rules, because there is exactly one writer.
- No risk of a sync conflict corrupting the links between pages.
- Git (version control) works properly, which beats file-sync versioning: one commit can change many files at once, every page gets a real history, and you can try a restructuring on a branch.

Everything else in these docs works the same. A local setup gives up nothing except access from more than one machine, and if only the operator needs that, a private git remote handles it more cleanly than a sync folder.

## The shared folder, and the only reason to use it

The real project ran on Dropbox for one reason: the owner's team is not technical, and the goal was to put them **inside the same wiki** the analyst works in, using Cowork (the desktop agent app) as their interface, on their own devices. A shared folder means every file lives on every machine, readable offline by a local agent, with nobody logging into anything when they want an answer. The operating rules travel with the folder, so an agent session on any machine behaves identically with no per-machine setup.

That is the whole case. It was a deliberate trade for a group of non-technical users, not a preference. If your collaborators only need the reports, send them the reports and stay local.

## What the shared folder costs you

The wiki's pages change constantly, and running that on top of file sync brings real failure modes. Each needs a fix:

- **Two machines writing at once corrupt the links.** If two machines change the journal, the index, or the inbound-link lists at nearly the same time, the sync service makes a conflicted copy and the link structure quietly splits in two. Fix: a lock file, honored by convention. Any operation that changes the link structure (adding a document, rebuilding the index, resolving links, bulk jobs) first writes a lock file naming who holds it, and deletes it when done. Any agent checks for the lock before writing and refuses if someone else holds it. Locks go stale after thirty minutes, so a crashed session cannot jam the system.
- **The journal becomes the choke point.** The fix here is also a writing rule: operations a person runs by hand log one entry per event; bulk jobs log one summary line per run. Beyond easing the contention, this keeps the journal readable. The real project's journal hit eleven thousand lines, 99 percent of it bulk-job noise repeating what was already on each page, before the rule existed and the noise was archived.
- **Agent memory does not travel.** Each user's agent memory stays on their own machine; the sync folder does not carry it. The rule: anything everyone needs to know goes in the wiki (the journal, the index, the topic pages), never into any one agent's memory. Memory is a private notebook for its owner, nothing more.
- **Tool clutter stays out of the sync folder.** Download caches, manifests, and logs live in local per-machine folders, so collaborators are not syncing gigabytes of staging files to read a two-page summary.

## Choosing

| Situation | Deployment |
|---|---|
| One analyst, one or more machines | Local, with a private git remote if multi-machine |
| Analyst plus non-technical collaborators who need to query the wiki | Shared folder, lock files, the journal rule |
| Analyst plus technical collaborators | Git remote; treat the wiki as a repository |

The choice is reversible: the folder is the system, and moving it between deployments is a copy.
