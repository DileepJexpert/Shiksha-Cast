# SA01 — Apache Kafka 10 Minute Me — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** Dark canvas, a flood of glowing order/payment/notification icons rushing toward a central pipe; "Big Billion Day" style chaos turning into a clean ordered stream. Katixo KhojLab logo top-left.
- **Text overlay:** "Apache Kafka 10 Min Me"
- **Style:** Big bold title, neon orange accent on "Kafka", monospace tagline below.
---
## Slide 2 — What is Kafka
- **Visual:** A stylised post office box receiving letters on one side and dispatching on the other; tags "Distributed", "Event Streaming", "Async".
- **Text overlay:** "Super-fast reliable post office"
- **Style:** Clean dark cards, neon glow, one-line label.
---
## Slide 3 — Analogy: Conveyor belt
- **Visual:** Restaurant scene — chefs (producers) placing orders on a conveyor belt, kitchen (consumers) picking them up at their own pace.
- **Text overlay:** "Producers ⟶ belt ⟶ Consumers"
- **Style:** Illustrated belt, decouple arrows, soft motion blur.
---
## Slide 4 — Core components: Broker & Topic
- **Visual:** A cluster of 3 server boxes labelled "Broker" inside a "Cluster" outline; channels labelled "orders", "payments" as Topics.
- **Text overlay:** "Broker = server | Topic = channel"
- **Style:** Boxes-and-arrows, monospace labels, neon outlines.
---
## Slide 5 — Partitions & offsets
- **Visual:** One Topic splitting into 3 horizontal append-only logs (partitions), each cell numbered 0,1,2,3 (offsets), spread across brokers.
- **Text overlay:** "Topic → Partitions → Offsets"
- **Style:** Log-cell diagram, growing arrow to the right, monospace numbers.
---
## Slide 6 — Producers & Consumers
- **Visual:** Left: app icon "Order Service" writing into a topic. Right: app icon "Email Service" reading from it. Key-based arrow into a specific partition.
- **Text overlay:** "Producer writes, Consumer reads"
- **Style:** Two-sided flow diagram, glowing write/read arrows.
---
## Slide 7 — Consumer groups
- **Visual:** A topic with 4 partitions, a "Group A" box with 4 consumers each mapped 1:1 to a partition; a second "Group B" reading the same partitions independently.
- **Text overlay:** "1 partition → 1 consumer per group"
- **Style:** Mapping lines, two coloured group boxes, parallel/scaling vibe.
---
## Slide 8 — End-to-end data flow example
- **Visual:** "Order placed" event entering orders topic, then fanning out to 3 groups: Payment, Inventory/Warehouse, SMS — each with its own icon.
- **Text overlay:** "1 event → 3 independent jobs"
- **Style:** Central event node with fan-out arrows, distinct service colours.
---
## Slide 9 — Retention & replay
- **Visual:** A log timeline with a "7 days" retention window; a crashed consumer icon restarting and resuming from its saved offset arrow.
- **Text overlay:** "Read ≠ delete — replay possible"
- **Style:** Timeline with retention shading, resume-from-offset marker.
---
## Slide 10 — Replication & fault tolerance
- **Visual:** A partition shown as Leader + 2 Follower copies on different brokers; leader broker crossed out, a follower promoted to new leader.
- **Text overlay:** "Leader fails → follower takes over"
- **Style:** Copy/sync arrows, failover highlight, small "KRaft / ZooKeeper" footnote.
---
## Slide 11 — When to use Kafka (interview)
- **Visual:** Split panel — left "Use Kafka": high-throughput, streaming, log aggregation; right "Maybe not": simple queue, request-reply (RabbitMQ / API icons).
- **Text overlay:** "Strong: throughput + durability"
- **Style:** Pros/cons split, checkmark vs caution icons.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Decoupled async, 2) Topics/Partitions/Offsets/Groups, 3) Best for high-throughput & replay.
- **Text overlay:** "Recap: 3 points"
- **Style:** Clean numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe button glow, "System Design Series" banner, small Kafka log icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
