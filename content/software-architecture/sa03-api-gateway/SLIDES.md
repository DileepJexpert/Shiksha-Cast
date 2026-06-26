# SA03 — API Gateway Kya Hai — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** A confused mobile app with 20 tangled arrows reaching to 20 scattered service boxes; the mess resolving into one clean funnel. Katixo KhojLab logo top-left.
- **Text overlay:** "API Gateway Kya Hai?"
- **Style:** Bold title, neon accent on "Gateway", chaos-to-order motif.
---
## Slide 2 — What is an API Gateway
- **Visual:** Clients (mobile, web, service) on the left all pointing to one Gateway box, which then routes to backend services on the right.
- **Text overlay:** "Single entry point for backend"
- **Style:** Funnel diagram, one central Gateway node, clean arrows.
---
## Slide 3 — Analogy: Office reception
- **Visual:** An office building with HR/Finance/Sales floors; a receptionist desk at the entrance checking a visitor's ID and guiding them.
- **Text overlay:** "Backend ka darbaan / reception"
- **Style:** Illustrated building + reception desk, guidance arrows.
---
## Slide 4 — Life without a Gateway
- **Visual:** Every client wired directly to every service, each service repeating auth/rate-limit/log badges; tangled, fragile mesh.
- **Text overlay:** "Without gateway = chaos"
- **Style:** Messy mesh, duplicated red badges, "tightly coupled" caption.
---
## Slide 5 — Job 1: Routing
- **Visual:** Gateway reading URL paths — `/orders` → Order Service, `/users` → User Service — with directional arrows.
- **Text overlay:** "Path dekho, sahi service bhejo"
- **Style:** Monospace path labels, routing arrows, single client address.
---
## Slide 6 — Job 2: Auth / AuthZ
- **Visual:** A request carrying a JWT token hitting the Gateway; a valid token passes through, an invalid one is blocked with a stop icon.
- **Text overlay:** "Token verify — ek hi jagah"
- **Style:** Token chip icon, green pass / red block branches, lock motif.
---
## Slide 7 — Cross-cutting concerns
- **Visual:** Icon row inside the Gateway — Rate Limiting, Load Balancing, Logging/Monitoring, Caching.
- **Text overlay:** "Rate limit, load balance, log, cache"
- **Style:** Icon strip, neon outlines, "handled once" caption.
---
## Slide 8 — End-to-end flow example
- **Visual:** Food app → Gateway (verify token → rate-limit → route) → Restaurant Service → response back to app.
- **Text overlay:** "1 request, sab handle"
- **Style:** Left-to-right pipeline with numbered steps, return arrow.
---
## Slide 9 — Request aggregation
- **Visual:** One client request to the Gateway, which fans out to User, Orders, Rewards services and merges three responses into one.
- **Text overlay:** "Many services → one response"
- **Style:** Fan-out + merge diagram, single combined payload card.
---
## Slide 10 — Caution: single point of failure
- **Visual:** Gateway crossed out and all clients blocked; then shown fixed as multiple Gateway replicas behind a load balancer.
- **Text overlay:** "Keep it highly available"
- **Style:** Red failure state vs green HA state, extra-hop latency note.
---
## Slide 11 — Gateway vs Load Balancer + BFF
- **Visual:** Comparison card — Load Balancer (network-level traffic split) vs API Gateway (app-level routing/auth); side note "BFF: per-client gateway".
- **Text overlay:** "Gateway ≠ Load Balancer"
- **Style:** Two-column compare, monospace labels, BFF footnote box.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Single entry point, 2) Centralizes routing/auth/rate-limit/log, 3) Powerful but must be HA.
- **Text overlay:** "Recap: 3 points"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, small gateway/funnel icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
