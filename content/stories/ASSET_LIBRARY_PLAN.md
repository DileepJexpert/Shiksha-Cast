# Story-Universe Asset Library Plan

A reusable 2D semi-realistic cast + background + prop library for a general Indian
story channel: **moral stories, funny stories, normal slice-of-life stories**, for
**both kids and adults**. Style reference: semi-realistic 2D illustration (more
detailed faces than the Kinnu cartoon cast — NOT photoreal, NOT 3D).

> This is a **separate universe** from the Kinnu kids channel. The Kinnu canonical
> cast (Kinnu, Gappu, Vibhu, Anshu, Prinshu) is NOT part of this and must not be mixed.

The whole point of a library: build it **once**, then each new story is mostly
**writing a script + arranging existing pieces**. New art is only needed when a story
introduces a genuinely new character or location — and that addition then joins the
library for next time.

---

## 1. Characters

Each character is built once, sliced into a cutout rig (like `buddy_hd`), reusable in
every story forever. Grouped by role so the cast covers almost any story.

### Phase 1 — Core cast (build these first: 10 characters)
A family + a couple of community figures is enough to shoot many stories.

| # | Name (working) | Age / role | Why it earns its place |
|---|---|---|---|
| 1 | **Aarav** | Boy ~9, curious/mischievous | Kid lead — funny + moral stories for kids |
| 2 | **Anya** | Girl ~9, smart/kind | Kid lead — pairs with Aarav |
| 3 | **Pari** | Girl ~12, responsible big sister | Bridges kid + teen stories |
| 4 | **Rohit** | Teen boy ~16, student | Teen/school stories |
| 5 | **Papa (Suresh)** | Father ~40 | Adult lead, family stories |
| 6 | **Mummy (Sunita)** | Mother ~38 | Adult lead, family stories |
| 7 | **Dadaji** | Grandfather, wise elder | The classic moral-story narrator/teacher |
| 8 | **Dadiji** | Grandmother, storyteller | Warmth, bedtime-story framing |
| 9 | **Guruji / Teacher** | School teacher | School + moral lessons |
| 10 | **Sharma ji** | Nosy/funny neighbor uncle | Comic relief across stories |

### Phase 2 — Extended cast (add as stories demand)
| # | Name (working) | Age / role | Use |
|---|---|---|---|
| 11 | **Chintu** | Little boy ~5, toddler | Comic relief, "younger sibling" |
| 12 | **Simran** | Teen girl ~16 | Pairs with Rohit |
| 13 | **Vikram** | Young man ~25, city job | Relatable young-adult lead |
| 14 | **Neighbor Aunty** | ~40 | Gossip/comic + community scenes |
| 15 | **Lala ji** | Shopkeeper / vendor | Market & money/honesty morals |
| 16 | **Doctor** | ~45 | Hospital, health, safety stories |
| 17 | **Havaldar** | Police constable | Honesty/safety/justice morals |
| 18 | **Poor man / laborer** | adult | Kindness/charity morals |
| 19 | **Greedy rich man (Seth)** | adult | Classic moral-story antagonist |
| 20 | **Sadhu / saint** | elder | Wisdom-giver in folk/moral tales |

**Tip — outfit swaps stretch the cast:** the same face with a swapped outfit can play
multiple roles (Vikram in office shirt vs. casual; Papa in kurta vs. shirt). Build the
face once, add alternate clothing layers as cheap variants.

### What "build one character" actually means (per-character asset set)
Built **once per character**, then the rig reuses them in every story:
- **Body parts** for the rig: head, torso, upper-arm/forearm (×2), thigh/shin (×2) — for standing/walking/gesturing.
- **Face expressions:** neutral, happy, sad, angry, surprised, crying, laughing.
- **Mouth visemes** for lip-sync: ~6–9 mouth shapes (rest → wide), like buddy's 9 mouths.
- **Views:** front + ¾ (and a side view only if a character must walk in profile).
- **Optional:** a seated pose (for car/sofa/classroom scenes).

---

## 2. Backgrounds / Environments

Built once each, reused across all stories. Day/evening/night variants only for the
locations that need them.

### Phase 1 — Core locations (build first: ~8)
1. **Living room** (sofa, TV) — most dialogue scenes
2. **Kitchen**
3. **Bedroom**
4. **Courtyard / aangan** (house front)
5. **Classroom**
6. **Street / lane** (residential)
7. **Market / bazaar**
8. **Garden / park**

### Phase 2 — Extended locations
- Home: dining area, rooftop (chhat), staircase, study room
- Village: village lane, mud-house exterior, farm/field, well, pond/river bank
- Nature: forest, riverside, mountains, open road, night sky
- Public: temple, hospital/clinic, police station, school building exterior, shop interior, bus stop, railway station, bank/office
- Festive: decorated home (Diwali/wedding), fair/mela

### Time-of-day variants (only where stories need them)
Day / evening (golden) / night for: living room, courtyard, street, village lane.

---

## 3. Vehicles & moving scenes

Cars/buses don't need physics — the car stays centered and the **background scrolls
with parallax** (far city slow, near trees fast) to fake driving. Built once:
- **Car** — exterior (for "driving" scenes) + interior (seated characters behind windshield + glass/reflection layer)
- **Auto-rickshaw**
- **Bus** (interior + exterior)
- **Bicycle / scooter / motorbike**
- **Bullock cart** (village/folk tales)
- **Parallax driving backgrounds:** city road, village road, highway (these are wide scrolling images)

---

## 4. Props

Small reusable objects placed per scene:
- Furniture: chair, table, bed, sofa, almirah, shelf
- Kitchen: plate/thali, glass, pot, stove
- Daily: phone, bag/school-bag, book, notebook, pen, money/coins, basket, umbrella
- Food: sweets (mithai), fruits, tea cup
- Story-specific: trophy, gift box, medicine, letter, lamp/diya, flowers

---

## 5. Build order (recommended)

1. **Pilot:** 1 background (living room) + 3 core characters (Aarav, Papa, Dadaji) + lip-sync test → prove the look + talking quality on the 4060.
2. **Phase 1 library:** 10 core characters + 8 core backgrounds + basic props. Enough to produce many stories with zero new art.
3. **First few stories:** write scripts, arrange existing assets, render. Note which missing asset each story wants.
4. **Phase 2:** add extended cast/locations/vehicles as real stories demand them.

## 6. Where things live (repo layout)
- Kinnu/cartoon characters: `assets/characters/kinnu_universe/<name>_hd/`
- Social/story characters: `assets/characters/social_universe/<name>_hd/`
- Kinnu/cartoon backgrounds: `assets/backgrounds/kinnu_universe/`
- Social/story backgrounds: `assets/backgrounds/social_universe/`
- Shared or legacy props: `assets/cartoon/props/` for now; split later if props start mixing styles.
- Stories (scripts/scenes): `content/stories/<story-id>/scenes.yaml`

Compatibility note: older rigs/backgrounds under `assets/cartoon/...` still render.
Do not add new realistic/social assets there.

Story config rule:

```yaml
universe: social_universe
background: public_office.png
cast:
  student: student_hd
  journalist: journalist_hd
```

The compiler expands those to `social_universe/student_hd` and
`social_universe/public_office.png` in generated `scenes.yaml`.

## 7a. Required engine work BEFORE Phase 1 (from review)
1. **Story renderer path:** build a `story.yaml -> scenes.yaml` compiler (mirror the
   existing `tutorial.py` / `tutorial-build`). Today `new-story` only writes
   `story.yaml` + `script.yaml` (an unrendered "future path"); there is no multi-character
   story-to-scenes compiler yet. Without it, every story needs hand-written `scenes.yaml`.
2. **Strict character asset manifest** per character: `source_sheet`, `style_prompt`,
   exact part names, transparent-PNG alpha, identical lighting + camera angle, mouth
   alignment, neck/hand/feet pivots. Save the source sheet in the repo.
3. **Naming rule (separate universe):** put social assets under
   `assets/characters/social_universe/` and `assets/backgrounds/social_universe/`.
   In story configs, use ids like `social_universe/journalist_hd` so Kinnu/Buddy
   assets never mix in.
4. **Validation tests:** every character composes without clipping; mouth overlays align;
   neck/hand/feet pivots correct (same bar as `test_cartoon_buddy.py`).
5. **Parallax-road / vehicles:** LATER. Do not block the pilot on it (current engine has
   simple camera pan/zoom only; layered scrolling roads need new code).

## 7b. Chosen route: Option C for main recurring characters
The animation engine is proven; the gating risk is ART. The project now chooses
**Option C: external/hand-authored parts sheets** for main recurring story characters.

Why:
- SDXL full-body stills look good but only work as talking figures.
- Procedural rigs move well but look too toy/cartoon-like for this story channel.
- External/high-quality parts sheets give the best balance: good look + reusable movement.

Implementation rule:
- Main cast: Option C parts sheet + `asset_manifest.json`.
- Random one-scene characters: talking-only figures are allowed.
- Walking/running: use side-view art; later upgrade to 4-8 frame side walk cycles.

Current status:
- `story_father_hd` is the first working Option C character.
- Better source sheets are saved for Father v2, Mother, and Grandmother.
- `story_young_hd` is a local hybrid/placeholder and should be replaced when a better sheet arrives.

Detailed spec and prompts: `content/stories/OPTION_C_CHARACTER_PIPELINE.md`.

## 7c. Reduced Phase 1 (validate before scaling)
Do NOT build 10 characters + 8 backgrounds up front. First:
1 full working character + 1 simple second character + 1 living-room background
-> render a **60-90 sec story test** -> only then scale the library.

## 7. Honest notes
- Faces will be **semi-realistic 2D illustration**, not photoreal (matches the reference).
- Lip-sync on realistic faces needs more mouth-blend tuning than a cartoon snout.
- Everything is flat 2D + parallax — no true 3D camera orbits.
- Biggest upfront cost = the character library (faces + expressions + visemes). After
  that, stories are cheap (mostly writing + TTS + arranging).
