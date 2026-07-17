---
type: topic
slug: canopy-c7-change-trail
title: Canopy Grid C-7 conflict, from RFI to executed amendment
status: resolved
source_records:
  - records/rfis/RFI-1204.md
  - records/pcos/PCO-217.md
  - records/contracts/Amendment-GC-02.md
last_synthesized: 2025-09-02
synthesized_by: example
---

# Canopy Grid C-7 conflict, from RFI to executed amendment

This topic walks one change through the full lifecycle the wiki models:
a design conflict raised as an RFI, a directed fix, a priced change, and
execution by amendment. It exists to demonstrate the cross-reference graph
and the epistemic-class tagging discipline.

## The trail

The GC raised the conflict on 2025-05-12: the canopy edge beam and the roof
drain leader occupy the same location at Grid C-7 and cannot both be built as
drawn {rec-est} ([RFI letter](../Originals/rfis/RFI-1204-2025-05-12.txt), lines 14-20; record: [RFI-1204](../records/rfis/RFI-1204.md)).

The architect of record directed the leader rerouted with a reinforcing angle
at the revised penetration and flagged anticipated cost impact {rec-est}
([RFI letter](../Originals/rfis/RFI-1204-2025-05-12.txt), lines 26-31).

The GC priced the change at $48,500 on a Summit Steel subtotal of $43,000
{party:GC} ([PCO pricing](../Originals/change-orders/PCO-217-2025-06-20.txt), lines 13-24; record: [PCO-217](../records/pcos/PCO-217.md)). The pricing is
the GC's assertion until executed; the markup line is stated as "per Contract
Exhibit C" and has not been independently recomputed here {infer}.

Amendment No. 2 executed the change on 2025-08-15 inside a $1,250,000 GMP
increase bundling four PCOs {rec-est}
([amendment](../Originals/contracts/Amendment-GC-02-2025-08-15.txt), lines 10-18; record: [Amendment-GC-02](../records/contracts/Amendment-GC-02.md)).

## What the graph shows

Attribution of the added cost is a design-coordination question: the conflict
was between two design drawings, and the fix was architect-directed. On these
records the cost consequence of the design conflict flowed to the owner via
the GMP increase {infer}. A real deployment would test that inference against
the design contract's standard-of-care terms before it went into any
deliverable; the anti-canon rule forbids promoting it to fact by repetition.

## Open items

CE 455 is referenced by the pricing but not yet ingested; the reference is
pre-wired as pending-target on [PCO-217](../records/pcos/PCO-217.md) and will
resolve when the change-event log arrives.
