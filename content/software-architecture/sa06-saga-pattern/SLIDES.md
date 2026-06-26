# SA06 — Saga Pattern — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** Travel booking with three service boxes — Flight (done), Hotel (done), Cab (red FAIL); a broken "rollback" magic button. Katixo KhojLab logo top-left.
- **Text overlay:** "Saga Pattern — Distributed Transactions"
- **Style:** Bold title, neon red accent on "Saga", failed-step warning motif.
---
## Slide 2 — The problem
- **Visual:** Left: monolith with one DB and an ACID lock (all-or-nothing). Right: microservices each with its own DB, one transaction can't span them.
- **Text overlay:** "Har service ka apna DB"
- **Style:** Two-panel compare, ACID badge vs scattered DBs, cross over single-transaction arrow.
---
## Slide 3 — What is Saga
- **Visual:** A chain of small local transactions T1→T2→T3, each committing its own DB, passing a signal to the next.
- **Text overlay:** "Bada transaction → chhote local steps"
- **Style:** Chain/links diagram, monospace `T1 T2 T3`, per-step DB icons.
---
## Slide 4 — Compensating transactions
- **Visual:** Forward steps with paired undo actions — Charge↔Refund, Book Hotel↔Cancel Hotel. "No rollback, only compensate."
- **Text overlay:** "Undo = compensating action"
- **Style:** Paired forward/undo arrows, refund/cancel icons, "already committed" note.
---
## Slide 5 — Analogy: 3 shops gift set
- **Visual:** Three shops shipping gift parts; one out of stock; user sending separate return requests to the other two.
- **Text overlay:** "Fail → har shop ko return bhejo"
- **Style:** Illustrated shops, return arrows, no-magic-button caption.
---
## Slide 6 — Two approaches
- **Visual:** Split screen — Choreography (services + events, no boss) vs Orchestration (central coordinator giving orders).
- **Text overlay:** "Choreography vs Orchestration"
- **Style:** Two-column intro, events cloud vs central box, monospace labels.
---
## Slide 7 — Choreography
- **Visual:** Order→OrderCreated event → Payment→PaymentDone event → Shipping; each service listens and reacts, no central control.
- **Text overlay:** "Events se baat, no central boss"
- **Style:** Event-chain diagram, pros (loose coupling) / cons (hard to debug) chips.
---
## Slide 8 — Orchestration
- **Visual:** Central orchestrator box issuing commands to Payment, Inventory, Shipping; on failure it triggers compensations in order.
- **Text overlay:** "Central orchestrator controls flow"
- **Style:** Hub-and-spoke diagram, command arrows, pros (clear) / cons (bottleneck) chips.
---
## Slide 9 — End-to-end example
- **Visual:** Travel saga — Flight OK → Hotel OK → Cab FAIL → compensate: Cancel Hotel → Cancel Flight → booking failed but consistent.
- **Text overlay:** "Cab fail → undo hotel & flight"
- **Style:** Forward-then-reverse timeline, red fail marker, "system consistent" badge.
---
## Slide 10 — Eventual consistency, idempotency
- **Visual:** Clock showing temporary mismatch → settling to consistent; an idempotent step running twice with same result; reliable-undo shield.
- **Text overlay:** "Eventual consistency + idempotent"
- **Style:** Timeline + retry loop icon, monospace `idempotent`, reliable-compensation shield.
---
## Slide 11 — When to use & Saga vs 2PC
- **Visual:** Use-when checklist (multi-service, own DBs); compare card — 2PC (locks, slow) vs Saga (no locks, scalable).
- **Text overlay:** "Saga vs Two-Phase Commit"
- **Style:** Checklist + two-column compare, lock icon vs no-lock, scalable badge.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Big txn → chain of local txns, 2) Fail → compensating undo, 3) Choreography/Orchestration + eventual consistency.
- **Text overlay:** "Recap: 3 points"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, small saga-chain icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
