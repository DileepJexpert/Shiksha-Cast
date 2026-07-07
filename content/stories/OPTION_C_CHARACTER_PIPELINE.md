# Option C Character Pipeline

Option C is now the chosen route for **main recurring story characters**:

- Use external/high-quality character art as the source.
- Slice it into transparent rig parts.
- Use the front rig for talking and gestures.
- Use side-view art for walking/running.
- Add side walk-cycle frames later when we need real alternating legs.

This avoids the two bad extremes:

- SDXL full-body stills look good but barely move.
- Procedural rigs move but look too cartoon/toy-like for story videos.

## Required Assets Per Main Character

For each permanent character, create these source files and save them under
`assets/cartoon/source/`.

### 1. Front Parts Sheet

Use one PNG sheet with a transparent or easily removable plain/checker background.
All parts must have space between them.

Required parts:

- full polished head with neutral face
- torso/clothes
- left upper arm
- left forearm with hand
- right upper arm
- right forearm with hand
- left thigh
- left shin with foot
- right thigh
- right shin with foot
- mouth shapes: closed, small open, medium open, wide open, smile, sad, O-mouth

Useful optional parts:

- eyes open/closed/happy
- brows neutral/happy/sad/surprised
- seated body pose
- pointing hand
- folded-arm pose

### 2. Side Walk Art

Minimum: one side-view full-body walking pose.

Better: 4-8 side-view walk-cycle frames of the same character, same size, same style,
transparent background, all facing right.

Current engine support:

- `side_walk.png` is supported now.
- multi-frame side walk cycle is the next engine upgrade.

## Source Naming

Use these names:

- `story_<name>_parts_sheet.png`
- `story_<name>_side_walk.png`
- later: `story_<name>_walk_001.png` ... `story_<name>_walk_008.png`

Generated rig output:

- `assets/characters/social_universe/<name>_hd/`
- must include `rig2.json`
- must include `asset_manifest.json`

## Prompt Template

```text
Create a high-quality semi-realistic 2D cartoon character parts sheet for animation.

Character: [describe character: age, role, clothing, hair, expression].
Style: polished Indian YouTube story animation, clean 2D illustration, soft shading,
not photo-realistic, not 3D, not chibi, consistent lighting.

Transparent background PNG if possible. No text, no labels, no scenery.

Arrange separated parts with clear space between them:
head with neutral face, torso, left upper arm, left forearm with hand, right upper arm,
right forearm with hand, left thigh, left shin with foot, right thigh, right shin with foot.

Also include mouth shapes:
closed, small open, medium open, wide open, smile, sad, O-mouth.

All parts must match the same character exactly: same clothes, same colors, same line style,
same lighting, same proportions.
```

Side-view prompt:

```text
Create the same character in side view for walking animation, facing right.
Full body visible, same clothes, same colors, same face, same art style.
Transparent background PNG if possible. No text, no labels, no scenery.
Pose: natural mid-walk with one leg forward and one leg back, arms swinging naturally.
```

Best side-walk prompt:

```text
Create 6 separate side-view walk-cycle frames of the same character, facing right.
Same size, same ground line, same proportions, transparent background.
Frame 1 contact, frame 2 down, frame 3 passing, frame 4 up, frame 5 opposite contact,
frame 6 passing. No text, no labels, no scenery.
```

## Current Option C Status

| Character | Source sheet | Front rig | Side walk | Walk cycle | Notes |
|---|---:|---:|---:|---:|---|
| `story_father_hd` | yes | yes | yes | no | current rig works; replace with Father v2 next |
| `story_father_parts_sheet_v2` | yes | no | no | no | better Father source now saved |
| `story_mother_parts_sheet` | yes | no | no | no | good for talking/standing/sitting mother |
| `story_grandmother_parts_sheet` | yes | no | no | no | good for Dadiji storyteller |
| `story_young_hd` | partial | hybrid | yes | no | local hybrid only; replace when better sheet arrives |

Saved family-cast source files:

- `assets/cartoon/source/story_father_parts_sheet_v2.png`
- `assets/cartoon/source/story_mother_parts_sheet.png`
- `assets/cartoon/source/story_grandmother_parts_sheet.png`

Recommended next build order:

1. Father v2 rig, because it can replace the current Papa immediately.
2. Mother talking/gesture rig.
3. Grandmother talking/gesture rig.
4. Side-view walking art only for characters who must visibly walk.
