# {{PROJECT_NAME}} Wiki: Constitution

<!--
Evidentiary-weighting doctrine template. This governs how the agent weighs
evidence, attributes claims, and resolves conflicts between sources. The
operating rules (CLAUDE.md) govern how the system runs; the two do not overlap
by design. Fill the {{placeholders}}, especially the §3 roster. Most of the
doctrine itself should survive contact with your project unchanged.
-->

This is doctrine, not operating rules. Read after `CLAUDE.md` and before `index.md`.

## §1 Standing and scope

- **Citation form.** Any record, topic, or deliverable may cite this document as `constitution.md §N`.
- **Precedence.** For operating-rule questions, `CLAUDE.md` is authoritative. For evidentiary weight, attribution, and conflict handling, this document is authoritative. Neither overrides the provenance rules; this document refines how provenance is weighed once established.
- **Mandatory reading.** Every agent reads this file at step 1 of the reading order.
- **This file is live doctrine.** Revised only by explicit `decision` entry in `log.md`. Never frozen.

## §2 Document-type authority tiers

When two sources speak to the same fact, the higher tier controls. Tier 1 is highest.

**Tier 1: Executed contract instruments.** The binding agreements and the instruments that modify them, in executed form: the prime contract, the architect agreement, executed amendments, executed change orders, executed subcontracts and their change orders. For any given term, the controlling instrument is the latest executed one that amends that term.

**Tier 2: Formal contract-administration instruments.** Issued on the record but not themselves the agreement: architect's supplemental instructions, formal RFI responses, formal notices, counsel correspondence asserting a legal position, formal transmittals. These establish what was instructed, requested, or asserted on the record. They do not by themselves establish the final contractual outcome.

**Tier 3: Party-maintained registers and logs.** Records kept by a party in the ordinary course: change-order logs, RFI snapshots, submittal logs, pay applications, schedule updates, budget snapshots. Authoritative for the data they track as of their snapshot date; subordinate to Tiers 1 and 2 where they conflict, because they are administrative summaries.

**Tier 4: Contemporaneous communications and observations.** Meeting minutes, field and daily reports, quality reports, informal correspondence, internal memos. Third-party independent observation (testing labs, inspectors, the authority having jurisdiction) sits in Tier 4 but carries elevated weight for the specific physical or regulatory fact observed, because the observer has no stake in the cost outcome.

**Tier 5: Derived or external synthesis.** Prior consultant analyses, prior AI output, reference material, and this wiki's own topic synthesis when read as a source rather than re-derived. Never the basis for a factual claim in a deliverable without re-derivation from a higher tier.

### Tie-breakers (apply in order)

1. Executed beats draft or unsigned, always.
2. Later controlling instrument beats earlier for the same term.
3. A specific instrument beats a general log entry for the same fact.
4. Within a tier, third-party independent observation beats an interested party's characterization of the same physical condition.
5. Signed and dated beats undated.
6. The operative instrument beats a summary or transcription of it. Cover sheets are summaries; trace every sum to the executed instrument.

### Tier 4 is not flat: medium floor, content elevation

A communication's authority is the higher of its medium floor and the elevation its content warrants.

1. **Medium floor.** An email, letter, or memo is Tier 4 by default.
2. **Counsel-interpretation elevation.** A communication from the owner's legal counsel that interprets the contract or characterizes legal rights, duties, or remedies is elevated: ranked immediately below the executed instruments it construes, above all Tier 3 registers and all Tier 4 lay correspondence. It is the controlling working interpretation until a court, arbitrator, or executed amendment displaces it. This elevation is owner-counsel only; counterparty counsel is never elevated.
3. **Owner-intent elevation.** A communication from the owner's principals or advisor layer about owner intent, decision, or direction carries owner-position weight, above any counterparty's characterization of owner intent.
4. **The guardrail.** Elevation attaches to content, not senders. Opinion, characterization, or fault attribution by anyone stays at the Tier 4 floor and is class `party:<X>` regardless of formality. Owner counsel reciting a disputed fact is a party assertion as to that fact. Counsel interpretation is authoritative for interpretation, never silently promoted to recorded fact (§5, §7).

## §3 Party and individual weighting

This ranks whose assertion carries what weight **as a position**. It is not a fault ranking. Attribution of fault is the output of forensic analysis, never an input read off a party's seniority.

Weight runs on two axes. Do not collapse them.

**Axis A: Owner decision and intent.** Who speaks for what the owner wants, decided, or directed. Top-down:

1. {{ultimate owner / principal}}
2. {{owner-advisor layer, if any}}
3. {{contracting owner entity and its officers}}

Owner-side characterizations are owner-position. Seniority on this axis does not convert opinion into fact.

**Axis B: Legal and contract interpretation.** Who authoritatively says what the contract means.

- {{primary owner counsel: firm, lead attorney}}
- {{supplemental owner counsel, if any, and the precedence rule between them}}

A legal interpretation by owner counsel is elevated per §2. Domain-specific: it governs contract meaning and legal characterization, not project decisions (Axis A).

**Counterparties.** Their attributions of cause are advocacy.

- {{design team: architects, engineers of record; authoritative for design intent and the instruments they issue}}
- {{GC/CM: authoritative for means and methods, its own cost position, and the lifecycle data it maintains}}
- {{counterparty counsel: advocacy weight, never elevated}}
- {{subcontractors and vendors: authoritative for their own scope and cost assertions; lowest weight on project-wide facts}}

**Third-party independent.**

- {{testing labs, inspectors, the authority having jurisdiction}}: high weight for the specific fact observed or certified.

**Governing principle.** A party's statement about its own conduct or cost is reliable evidence of that party's position. A party's statement attributing cause or fault to another party is advocacy, tagged as assertion under §5, never recorded as fact. The one exception is Axis B: owner counsel's legal interpretation controls the working reading of contract meaning per §2 while remaining classed `party:<counsel>` (§7).

## §4 Metadata trust register

Structured metadata is a navigation and triage aid. It is trusted for routing and as a pointer. It is never the evidentiary basis for a forensic attribution; attribution rests on instrument text, tier-ranked per §2.

- **"Responsible party" / "ball in court" fields**: workflow routing, not adjudication of fault.
- **Change "status"**: the maintaining party's administrative lifecycle state, not entitlement.
- **Bundling and grouping identifiers**: administrative convenience; no causal meaning.
- **Cover-sheet dollar figures**: transcriptions; authoritative only in the executed operative instrument.
- **Dates**: distinguish issued, received, effective, executed. A log-row date is often the entry date, not the event date; prefer the instrument's own date.
- **Pay-app scheduled values and percent complete**: the applicant's assertion, subject to certification and later adjustment.
- **Author / created-by fields in exports**: the system user who made the row, not necessarily the substantive author.
- **Titles and filenames**: descriptive convenience, not legal characterization.

## §5 The four epistemic classes

Every synthesized claim in a topic or deliverable belongs to exactly one class, and the class travels with the claim wherever it is copied.

| Class | Meaning | Source basis | Truth value |
|---|---|---|---|
| `rec-est` | a Tier 1 or 2 instrument states it | §2 Tier 1-2 | recorded as fact |
| `party:<X>` | a named party's position | any tier, attributed | true only as "X asserts Y" |
| `infer` | analyst synthesis across records | multiple, cited | argument; never stated as fact |
| `3p` | pre-existing summary from outside the corpus | §2 Tier 5 | lowest; never load-bearing without re-derivation |

Binding rule: any claim carrying a dollar figure, count, date assertion, attribution, or quote must be assignable to exactly one class, and its class must be discernible to the reader. Tag format: one brace token (`{rec-est}`, `{party:<ID>}`, `{infer}`, `{3p}`) immediately before the claim's first source link.

## §6 Conflict-resolution procedure

A conflict is two or more sources asserting the same fact with materially different content.

1. **Detect.** Name the disputed fact and the disagreeing sources.
2. **Rank.** Order by §2 tier, then §3 party weight, then the §2 tie-breakers.
3. **Adopt.** Take the higher-authority value for the working claim; tag and cite it.
4. **Register.** Never silently discard the lower source. Record the conflict as a Discrepancy record capturing the disputed fact, each source with its tier, the resolution rule applied, and the residual risk.
5. **Escalate, do not invent.** Never resolve by averaging, guessing, or convenience. If §2 and §3 do not break the tie, escalate to the human.

A detected conflict is a forensic asset. The discrepancy register is itself evidence.

## §7 Anti-canon rule

Subjective content does not become fact by repetition, by age, or by being copied into a more formal document.

- An `infer` or `3p` claim is never promoted to `rec-est` by restatement without its class.
- A deliverable carries a topic's inferences forward only as labeled inferences. No shipped finding may rest on a support chain that bottoms out only in `infer` or `3p` content.
- A party's characterization stays `party:<X>` in the record, in the topic that cites the record, and in the deliverable that cites the topic. The class is not shed at any boundary.

---

*Doctrine status: live. Revised only by explicit `decision` entry in `log.md`.*
