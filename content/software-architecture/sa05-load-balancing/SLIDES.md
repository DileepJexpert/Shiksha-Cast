# SA05 — Load Balancing Kya Hai — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** One overloaded server cracking under a flood of user icons on sale day; then a load balancer fanning the flood across multiple servers. Katixo KhojLab logo top-left.
- **Text overlay:** "Load Balancing Kya Hai?"
- **Style:** Bold title, neon red accent on "Load Balancing", traffic-flood motif.
---
## Slide 2 — What is load balancing
- **Visual:** Users → single Load Balancer box → 3-4 backend servers; arrows splitting evenly. LB labelled as the gatekeeper.
- **Text overlay:** "Requests ko servers me baanto"
- **Style:** Central LB box, fan-out arrows, even-distribution highlight.
---
## Slide 3 — Analogy: Bank counters
- **Visual:** A bank with a manager directing customers to free counters; one jammed counter vs balanced counters.
- **Text overlay:** "LB = bank ka manager"
- **Style:** Illustrated counters, manager pointing, queue arrows.
---
## Slide 4 — How it works
- **Visual:** Flow — single LB address → backend pool → pick healthy server → forward → response back. User sees only one address.
- **Text overlay:** "Ek address, peeche kai servers"
- **Style:** Linear flow diagram, "backend pool" cluster, hidden-servers note.
---
## Slide 5 — Algorithms
- **Visual:** Four labelled cards — Round Robin (1-2-3 cycle), Least Connections (count badges), Weighted (big/small servers), IP Hash (IP→server map).
- **Text overlay:** "Algorithms: kaun sa server?"
- **Style:** Four-card grid, monospace algorithm names, mini diagrams each.
---
## Slide 6 — Health checks
- **Visual:** LB pinging each server "alive?"; one server red/dead removed from pool, others green and active.
- **Text overlay:** "Health check — sirf healthy servers"
- **Style:** Heartbeat icons, green/red status, removed-server cross.
---
## Slide 7 — Sticky sessions vs shared state
- **Visual:** Left: user pinned to one server (sticky). Right: all servers reading session from shared Redis box.
- **Text overlay:** "Session: sticky vs shared (Redis)"
- **Style:** Two-panel compare, stateless-servers highlight, Redis box.
---
## Slide 8 — Layer 4 vs Layer 7
- **Visual:** L4 box reading IP:port (fast badge) vs L7 box reading URL/headers/cookies (smart routing /api split).
- **Text overlay:** "L4 fast vs L7 smart"
- **Style:** Two-column compare, monospace `IP:port` vs `HTTP /api`, speed/smart badges.
---
## Slide 9 — End-to-end example
- **Visual:** Sale day timeline — req1→S1, req2→S2, req3→S3, req4→S1; then S2 crashes, traffic continues on S1 & S3, zero downtime.
- **Text overlay:** "Server crash → no downtime"
- **Style:** Numbered timeline, crash X on S2, "users unaffected" badge.
---
## Slide 10 — Benefits
- **Visual:** Four benefit chips — Scalability (add servers), High Availability, Performance, Zero-downtime deploys.
- **Text overlay:** "Scale, uptime, speed"
- **Style:** Four-chip grid, neon icons, monospace labels.
---
## Slide 11 — Cautions & interview points
- **Visual:** LB as single point of failure → two LBs active/standby; side note "LB vs reverse proxy"; cloud LB badge (AWS ELB).
- **Text overlay:** "SPOF? → 2 load balancers"
- **Style:** Redundant-pair diagram, compare caption, cloud LB chip.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Split traffic across servers, 2) Algorithms + health checks, 3) L4/L7 + shared session state.
- **Text overlay:** "Recap: 3 points"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, small load-balancer fan-out icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
