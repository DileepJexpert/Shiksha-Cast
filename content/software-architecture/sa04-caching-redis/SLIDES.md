# SA04 — Caching Aur Redis Basics — Slide Design Brief
**Format:** 1920×1080 PNG | **Export:** `slides/slide_001.png` to `slide_013.png`
**Brand:** Katixo KhojLab | **Style:** Developer/architecture diagrams, dark, boxes-and-arrows, monospace accents
---
## Slide 1 — HOOK / Title
- **Visual:** A panting database cylinder under repeated identical queries; then a small fast "cache" chip shielding it. Katixo KhojLab logo top-left.
- **Text overlay:** "Caching aur Redis Basics"
- **Style:** Bold title, neon red accent on "Redis", speed/lightning motif.
---
## Slide 2 — What is caching
- **Visual:** Data path: App → fast RAM cache (hit) vs App → slow disk DB; a stopwatch showing big time difference.
- **Text overlay:** "Bar-bar data → paas rakho"
- **Style:** Two-path diagram, RAM-vs-disk speed contrast, monospace timings.
---
## Slide 3 — Analogy: Kitchen vs market
- **Visual:** A kitchen jar of sugar (cache) next to a far-away market (database); arrows showing rare trips to the market.
- **Text overlay:** "Cache = rasoi ka dabba"
- **Style:** Illustrated jar + market, short vs long trip arrows.
---
## Slide 4 — Meet Redis
- **Visual:** Redis logo-style cube, "in-memory" RAM chip icon, a dictionary key→value pair, "microseconds" speed badge.
- **Text overlay:** "Redis = in-memory key-value store"
- **Style:** Clean card, monospace `key : value`, RAM glow.
---
## Slide 5 — Redis data structures
- **Visual:** Five labelled chips — Strings, Hashes, Lists, Sets, Sorted Sets — each with a tiny example (profile, queue, leaderboard).
- **Text overlay:** "Sirf text nahi — kai structures"
- **Style:** Icon/chip row, monospace examples, neon outlines.
---
## Slide 6 — Cache-aside pattern
- **Visual:** Flow — App checks cache → HIT returns fast / MISS goes to DB, fills cache, returns. Two branches clearly labelled.
- **Text overlay:** "Cache Hit vs Cache Miss"
- **Style:** Branching flowchart, green HIT / amber MISS, fill-cache arrow.
---
## Slide 7 — TTL (Time To Live)
- **Visual:** A cache entry with a countdown timer (60s / 1h) auto-expiring and vanishing after time runs out.
- **Text overlay:** "TTL = auto expiry, fresh data"
- **Style:** Timer/clock icon, fading entry, monospace `TTL=60s`.
---
## Slide 8 — Cache invalidation
- **Visual:** DB updated (new name) but cache still holds old name → red mismatch; fix shown as delete/update the cache key.
- **Text overlay:** "Stale data se bacho"
- **Style:** Mismatch warning, "delete or update" branches, famous-quote caption.
---
## Slide 9 — End-to-end example
- **Visual:** Steps for `user:123` — first MISS (DB → cache with 5m TTL), repeat HITs from Redis, edit → key deleted.
- **Text overlay:** "user:123 — miss, then hits"
- **Style:** Numbered timeline, monospace key, DB-untouched highlight.
---
## Slide 10 — Caution: memory & eviction
- **Visual:** A full RAM bar; Redis evicting least-recently-used entries (LRU); a small disk icon for persistence.
- **Text overlay:** "Sab cache mat karo — LRU evicts"
- **Style:** Memory-full meter, eviction arrows, persistence footnote.
---
## Slide 11 — Beyond cache + Redis vs Memcached
- **Visual:** Use-case chips — sessions, rate-limit counters, leaderboards, pub/sub; side compare card Redis vs Memcached.
- **Text overlay:** "Redis: more than just cache"
- **Style:** Use-case grid + two-column compare, monospace labels.
---
## Slide 12 — 3-point recap
- **Visual:** Three numbered cards — 1) Cache = fast copy, less DB load, 2) Redis = in-memory KV + structures + TTL, 3) Cache-aside + invalidation.
- **Text overlay:** "Recap: 3 points"
- **Style:** Numbered cards, monospace keywords, neon dividers.
---
## Slide 13 — CTA / Outro
- **Visual:** Katixo KhojLab logo centre, subscribe glow, "System Design Series" banner, small cache/Redis chip icon.
- **Text overlay:** "Subscribe — Katixo KhojLab"
- **Style:** Bold outro, neon subscribe CTA, dark canvas.
