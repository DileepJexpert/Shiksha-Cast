# Option-C source-art prompts (paste into a strong image tool)

For each story character we need **three** kinds of source art (NOT one final PNG).
Option-C rigging is set up to consume these once they exist. File names are exact —
save them into `dist/_spike_story/` (or hand them to the rigger).

**Golden rule — include this line in every prompt:**

> Do not create one final character only. Create separated animation parts with clean
> empty space between every part, plus side-view walking art in the exact same style.

Keep **one consistent style** across all of a character's assets: *2D cartoon
illustration, semi-realistic Indian, flat cel shading, clean dark outlines, plain solid
white background, no shadow.*

---

## story_young  (young man ~28, neat black hair, clean-shaven, light-blue collared shirt, dark-grey trousers, brown shoes)

### 1. `story_young_parts_sheet.png`  (landscape, ~1600×1100)
> Character animation model sheet of a semi-realistic Indian young man, 2D cartoon
> illustration, flat cel shading, clean dark outlines, plain white background. Do not
> create one final character only. Lay the body parts out SEPARATED with clean empty
> white space between every part, front view: head, torso (light-blue collared shirt),
> left upper arm, right upper arm, left forearm+hand, right forearm+hand, left thigh,
> right thigh, left shin+shoe, right shin+shoe. Each part fully detached, neatly spaced
> in a grid, same lighting and scale. No overlapping parts.

### 2. `story_young_side_walk.png`  (portrait, ~832×1216)
> Full-body SIDE PROFILE view of the same young man, facing right, mid-stride walking
> pose, one leg forward one leg back, arms swinging, same 2D cartoon semi-realistic
> style, flat cel shading, clean outlines, plain white background.

### 3. `story_young_walk_001.png` … `story_young_walk_006.png`  (portrait each)
6-frame side-profile walk cycle, same character/style, facing right, plain white bg:
- 001 contact (right leg forward) · 002 down · 003 pass · 004 contact (left leg forward) · 005 down · 006 pass
> Full-body side profile walk-cycle frame N of 6 of the same young man facing right,
> [pose for N], identical character, identical 2D cartoon semi-realistic style, plain
> white background.

---

## story_father  (man ~40, black hair + moustache, beige kurta, off-white pyjama, dark sandals)
Same three assets, same rules, swap the description:

### 1. `story_father_parts_sheet.png`
> Character animation model sheet of a semi-realistic Indian man about 40 with a black
> moustache, beige kurta and off-white pyjama, 2D cartoon illustration, flat cel shading,
> clean dark outlines, plain white background. Do not create one final character only.
> Lay the body parts out SEPARATED with clean empty white space between every part:
> head, torso (kurta), 2 upper arms, 2 forearms+hands, 2 thighs (pyjama), 2 shins+sandals.
> Each part fully detached, neatly spaced, same lighting and scale, no overlap.

### 2. `story_father_side_walk.png`
> Full-body SIDE PROFILE of the same man facing right, mid-stride walking, same style,
> plain white background.

### 3. `story_father_walk_001.png` … `story_father_walk_006.png`
> 6-frame side-profile walk cycle, same character/style, facing right, plain white bg.

---

## Why a strong tool (not local SDXL) for these
Local SDXL nails a *single* figure but is unreliable at (a) neatly separated parts with
gaps and (b) keeping the same face across 6 walk frames. A model with better instruction-
following / character-consistency (or hand-drawn / commissioned art) produces clean
Option-C sources. The rig then cuts the parts sheet and uses the side-walk sprite for
profile movement — realistic look AND real movement.
