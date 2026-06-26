# SA02 — Microservices vs Monolith — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** Split-screen tease — left one giant block "MONOLITH", right a grid of small connected boxes "MICROSERVICES", a "VS" glowing in the middle. Katixo KhojLab logo top-left.
- **Text overlay:** "Microservices vs Monolith"
- **Style:** Bold title, neon "VS", monospace subtitle "Interview Special".
---
## Slide 2 — What is a Monolith
- **Visual:** One large box containing stacked modules — Login, Payment, Orders, Notifications — wired to a single database cylinder.
- **Text overlay:** "Ek hi app, ek hi database"
- **Style:** Single bordered block, internal module lines, one DB icon.
---
## Slide 3 — What are Microservices
- **Visual:** Several small service boxes (Auth, Payment, Order) each with its own small DB, connected by REST/messaging arrows over a network.
- **Text overlay:** "Chhote independent services"
- **Style:** Distributed boxes-and-arrows, each service its own colour.
---
## Slide 4 — Analogy: Restaurant vs Food court
- **Visual:** Left a single big restaurant with one kitchen; right a food court with separate stalls each with its own kitchen.
- **Text overlay:** "Single kitchen vs food court"
- **Style:** Two illustrated panels, fire/closed icon on one stall to show isolation.
---
## Slide 5 — Monolith: Pros
- **Visual:** Checklist card — Simple dev, Easy testing, Fast (no network hop), Single deploy.
- **Text overlay:** "Simple, fast, cheap to start"
- **Style:** Green checkmark list, calm dark card.
---
## Slide 6 — Monolith: Cons
- **Visual:** A bloated block with a tiny change forcing a full redeploy; one red bug bringing the whole box down; scaling the entire block.
- **Text overlay:** "Bada hone par dard"
- **Style:** Warning red accents, "redeploy all" arrow, oversized scale icon.
---
## Slide 7 — Microservices: Pros
- **Visual:** Icons — independent deploy, scale-one-service, fault isolation shield, multi-language/db freedom, parallel teams.
- **Text overlay:** "Deploy + scale independently"
- **Style:** Icon grid, neon outlines, positive tone.
---
## Slide 8 — Microservices: Cons / cost
- **Visual:** A tangled web of service calls, a broken network link, distributed-tracing/log icons, Docker + Kubernetes badges.
- **Text overlay:** "Distributed = complexity"
- **Style:** Caution palette, tangled arrows, infra logos as footnote icons.
---
## Slide 9 — Example: Diwali sale scaling
- **Visual:** Left monolith scaling the whole app on big servers; right only Cart + Payment services scaled, rest normal.
- **Text overlay:** "Scale all vs scale one"
- **Style:** Side-by-side e-commerce diagram, highlighted scaled boxes.
---
## Slide 10 — When to choose what
- **Visual:** Decision panel — "Monolith if": small team, new product, fast launch. "Microservices if": huge scale, many teams, varied scaling.
- **Text overlay:** "Start monolith → split later"
- **Style:** Two-column decision card, golden-rule banner at bottom.
---
## Slide 11 — Modular Monolith (middle ground)
- **Visual:** A single deploy box but cleanly partitioned into modules with dashed seams hinting at future extraction into services.
- **Text overlay:** "Best of both: Modular Monolith"
- **Style:** Single box with dashed module seams, "future split" ghost arrows.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Monolith = simple/unified, 2) Microservices = independent but complex, 3) Choice = team + scale + maturity.
- **Text overlay:** "Recap: trade-offs, not absolutes"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, tiny monolith+services icons.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
