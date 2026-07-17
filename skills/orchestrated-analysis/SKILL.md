---
name: orchestrated-analysis
description: Run a large analysis as an orchestrator with independent executor agents and a separate adversarial verification stage. Use for work too large or too self-influencing for one context, such as a bottom-up budget rebuild, an exhaustive audit, or a many-document sweep.
---

# Orchestrated analysis

Decompose a large analysis across independent agents so no single context can anchor on its own early guesses. The orchestrator plans and synthesizes; executors each own one scoped question; verifiers try to break the results.

## When to run

- Rebuilding a figure independently of the book it will be checked against.
- Exhaustive audits and sweeps across more documents than one context can hold honestly.
- On request: "rebuild this from scratch", "audit this exhaustively".

## Structure

1. **Decompose.** The orchestrator splits the work into sections, each answerable from a bounded set of sources. Write the decomposition down before launching anything; the section list is the coverage claim.
2. **Isolate the executors.** Each executor gets one section, the source list for it, and no view of any other executor's conclusions or of any running total. Independence is the point: an executor that can see the total steers toward it.
3. **Quarantine the answer key.** If the analysis checks an existing book (a budget, a forecast), executors never see it. Reconciliation against it happens only after the independent build is complete.
4. **Verify adversarially, separately.** Verification is its own executor stage, staffed by agents prompted to refute, not confirm. Every section gets at least one refuter; contested or high-dollar sections get several with distinct lenses (arithmetic, source-support, contract reading).
5. **Synthesize with bounds.** The orchestrator assembles sections, reconciles overlaps, and writes the verification scope: which sections were refuted-and-survived, which were spot-checked, which were assembled untested.
6. **Reject, do not patch.** If verification finds a load-bearing problem in a section, regenerate that section from the corrected evidence. If the problem contaminates the decomposition itself, reject the build and re-plan. Never graft fixes onto conclusions shaped by the bad input.

## Sizing

Match the fan-out to the stakes. A quick check is a handful of executors and single-vote verification. An independent rebuild that leadership will rely on justifies dozens of executors and multi-lens refutation per section. State the sizing in the output; a small panel presented as exhaustive is a verification-scope violation.

## Failure modes this prevents

- Anchoring: one long context converging on its own early estimates.
- Self-agreement: the same context both producing and checking a number.
- Coverage theater: an "exhaustive" sweep whose actual section list was never written down.
