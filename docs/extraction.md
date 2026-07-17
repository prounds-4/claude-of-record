# Extraction: getting documents out of other people's systems

This is the least portable page in the docs, and it is included for exactly that reason. The wiki's structure, evidence rules, and checks travel to any project unchanged. Extraction does not: it depends on which systems the other parties run, what access the owner negotiated, and what license tier someone pays for. Here is how three real extractions worked, and the pattern that carries over.

## The general problem

The owner's side holds, at best, a read-only seat in systems the other parties own. Three consequences drive everything:

- **Prefer the machine channel over the screen.** Every web app sits on a REST API, the machine channel its own apps use. Pulling through it is faster, complete, and repeatable. Driving a browser is the fallback; exporting by hand is the floor.
- **Archive early, because the access is not yours.** The builder's document system belongs to the builder. If the relationship sours, access can be cut the same week you need the documents most. Pull the actual attachments, not just the index entries, on a schedule, while you can.
- **Everything lands as a dated snapshot.** No pull is live state. Each is a capture of one moment, filed and cited that way.

## SharePoint: the bulk channel

The project's shared document library ran on SharePoint. Extraction went through its REST API, signed in with the browser's session cookies, no special setup required. One tool, four modes: **inventory** (walk the whole library and write a list, downloading nothing), **download** (pull the text documents from that list, with folder and date filters, safe to resume if interrupted), **sync** (re-walk and download only what changed, the repeat-pull mode), and **fetch** (pull one named file on demand).

Scale on the real project: over a hundred gigabytes and tens of thousands of files came down in a day.

Two policies made that volume workable:

- **Skip the heavy files, keep a stub.** 3D building models, videos, CAD files, and photo folders are not worth the disk, but knowing they exist matters. Each skipped file gets a small placeholder page holding its upstream location and the command to fetch it later, and each photo folder gets one summary page. Thousands of stubs on the real project. The rule they serve: before concluding "no such document exists," the agent must check the stub index, because missing from the archive is not the same as missing upstream.
- **Keep raw downloads outside the shared folder.** Downloaded bytes land in a local staging area, not in the wiki, so teammates sharing the wiki folder do not sync 150 GB of staging. Only chosen files move into the wiki's source tier, and the hash gate ([ingestion.md](ingestion.md)) sits between staging and inbox.

## Procore: the counterparty's system

The builder ran RFIs (questions from the construction site to the architect), submittals, and punch lists in Procore, and the owner had no API access. What the owner did have: weekly status-report PDFs (captured as the snapshot trail, the closest thing to live RFI state), occasional CSV log exports, and a web login to view individual items.

The hard-won rule: **index entries alone are useless. Pull the actual questions and answers.** An RFI page built only from a log export knows the dates and the status and nothing about what was asked or answered. The response letters and attachments were pulled out of Procore deliberately and early, because it is the builder's system and the window to archive is a courtesy, not a right.

## Smartsheet: when there is no machine channel

The live change-order negotiation tracker ran in Smartsheet, shared with the owner as a comment-only collaborator. The API requires a paid tier the account did not have, and a comment-only collaborator cannot create an access token, so there was no machine channel at any price the situation justified. The working mechanism: an agent drives the logged-in browser through File, Export, Excel, and a dated copy lands in the source tier. Free, nothing lost in the export, entirely in the owner's control, and impossible to run unattended. That trade-off was accepted and written down rather than fought.

Each pull is read in two layers: one snapshot page holding the whole-log totals, replacing the prior snapshot, plus a live-state block copied onto each individual change-order page and replaced in full on every pull, so it always shows the latest capture. Safe to re-run: run it twice on the same export and the second run changes nothing.

## The pattern, portable

For each upstream system, answer four questions in order. Is there a machine channel I can reach with the access I already have? Which files are worth bytes on disk, and which just need a stub? How often should I pull, given how fast the source changes? And what happens to my archive if my access ends tomorrow? The answers give you one tool per system, a trail of dated snapshots, and no illusions.
