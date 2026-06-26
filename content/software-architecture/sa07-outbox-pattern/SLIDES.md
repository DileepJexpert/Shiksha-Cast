# SA07 — Outbox Pattern — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** Service saves order to DB (green) then crashes (red) before publishing to Kafka; broken arrow to broker, "event lost". Katixo KhojLab logo top-left.
- **Text overlay:** "Outbox Pattern — Reliable Messaging"
- **Style:** Bold title, neon red accent on "Outbox", crash-before-publish motif.
---
## Slide 2 — The dual write problem
- **Visual:** Service writing to two separate systems — DB and Kafka — with a crossed-out "one atomic transaction" arrow spanning both.
- **Text overlay:** "Dual write problem"
- **Style:** Two-target write diagram, no-atomic-span warning, monospace `DB | Kafka`.
---
## Slide 3 — Two failure cases
- **Visual:** Case A: DB saved, event missing → "lost message". Case B: event sent, DB rolled back → "phantom event".
- **Text overlay:** "Lost message vs phantom event"
- **Style:** Two-panel failure cards, red markers, ghost icon for phantom.
---
## Slide 4 — Core idea
- **Visual:** Single DB transaction writing BOTH the business row AND an outbox row; broker removed from the critical moment. Atomic lock around both.
- **Text overlay:** "DB + event = ek transaction"
- **Style:** One-transaction box wrapping two table writes, atomic badge, outbox table icon.
---
## Slide 5 — Analogy: office outbox tray
- **Visual:** Worker drops a letter in an outbox tray while doing the task (one motion); a peon later picks letters and posts them.
- **Text overlay:** "Outbox tray + peon = relay"
- **Style:** Illustrated desk + tray, peon pickup arrow, "letter safe if peon late" caption.
---
## Slide 6 — Message relay / publisher
- **Visual:** Separate relay process reading outbox table → publishing to Kafka → marking rows sent/deleted.
- **Text overlay:** "Relay: outbox → broker"
- **Style:** Pipeline diagram, read→publish→mark-sent steps, monospace `status: sent`.
---
## Slide 7 — Polling vs CDC
- **Visual:** Left: relay polling outbox table on a timer (query load). Right: Debezium reading DB transaction log (real-time CDC).
- **Text overlay:** "Polling vs CDC (Debezium)"
- **Style:** Two-column compare, timer icon vs txn-log icon, efficiency badge on CDC.
---
## Slide 8 — At-least-once delivery
- **Visual:** Relay publishes event then crashes before marking sent → republishes same event; consumer with idempotency shield dedupes.
- **Text overlay:** "At-least-once → consumer idempotent"
- **Style:** Duplicate-event arrows, crash marker, idempotency shield on consumer.
---
## Slide 9 — End-to-end example
- **Visual:** Order placed → one txn writes orders + OrderPlaced to outbox → relay publishes to Kafka → Inventory & Notification consume.
- **Text overlay:** "OrderPlaced — saved, then published"
- **Style:** Numbered flow, single-txn highlight, downstream consumers, "event never lost" badge.
---
## Slide 10 — Benefits
- **Visual:** Four benefit chips — Atomicity, No lost events, Reliability (survives crashes), Works with any broker (Kafka/RabbitMQ).
- **Text overlay:** "Atomic, reliable, no lost events"
- **Style:** Four-chip grid, neon icons, monospace labels.
---
## Slide 11 — Trade-offs & interview points
- **Visual:** Latency clock (not instant); growing outbox table needing cleanup; caption "solves dual write by one txn"; pairs with Saga badge.
- **Text overlay:** "Trade-offs: latency + cleanup"
- **Style:** Cost chips, cleanup broom icon, Saga-combo note.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Solves dual write, 2) Data + event in one txn (outbox table), 3) Relay (polling/CDC) + at-least-once.
- **Text overlay:** "Recap: 3 points"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, small outbox-tray icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
