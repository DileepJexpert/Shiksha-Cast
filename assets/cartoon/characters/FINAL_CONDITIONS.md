# Character Final Conditions

This file separates final YouTube-ready child characters from temporary rigs.

## Final Today

### Vibhu

- Final asset id: `vibhu_sheet_hd`
- Use for new tutorials and stories when Vibhu is needed.
- Visual condition: accepted.
- Rig condition: accepted for talk, listen, think, point, jump, walk, swim, cry, laugh, and head-turn tests.
- Notes: use this instead of older `vibhu_hd`. The old `vibhu_hd` remains only as a legacy/simple rig.

## Temporary Today

### Gappu

- Current asset id: `gappu_hd`
- Visual condition: temporary only.
- Safe use: talk, listen, think, smile, small idle movement.
- Avoid for auto-generated wide point, cheer, jump, run, and close-up hero shots.
- Reason: current image parts are simple and the arm/leg shapes look stiff in large poses.
- Final requirement: create a new high-quality sheet-based `gappu_sheet_hd`, matching the quality of `vibhu_sheet_hd`.

## Required Parts For A Final Sheet-Based Character

A final child character folder must include:

- `rig2.json`
- `head.png`
- `head_back.png` when head-turn/back view is expected
- `torso.png`
- `upper_arm_left.png`, `upper_arm_right.png`
- `forearm_left.png`, `forearm_right.png`
- `thigh_left.png`, `thigh_right.png`
- `shin_left.png`, `shin_right.png`
- `knee_left.png`, `knee_right.png`
- `eyes_open.png`, `eyes_closed.png`, `eyes_happy.png`
- `brows_neutral.png`, `brows_happy.png`, `brows_sad.png`, `brows_surprised.png`
- `mouth_X.png`, `mouth_A.png`, `mouth_B.png`, `mouth_C.png`, `mouth_D.png`
- `mouth_E.png`, `mouth_F.png`, `mouth_G.png`, `mouth_H.png`, `mouth_sad.png`

## Visual Acceptance Rules

- Full body must look natural in neutral pose.
- Head must sit centered on the neck.
- Eyes must be clear, not hidden by glasses unless glasses are part of the locked design.
- Arms must not look bulky or broken at shoulder/elbow joints.
- Palms/fingers must remain visible in point and wave poses.
- Knees need caps or smooth overlap so upper/lower leg joints do not stack like real exposed joints.
- Feet must stay grounded in idle and walk preview.
- Transparent PNG edges must be clean, with no black/white background baked in.
- Character style must be consistent with Kinnu: bright kid-safe cartoon, clean outlines, friendly face.

## Animation Acceptance Rules

Before marking a character final, render the QC sheet:

```powershell
python -m pytest tests\test_vibhu_sheet_rig.py tests\test_cartoon_castmates.py
```

And visually inspect:

- idle
- talk
- point
- jump
- think
- walk

The preview sheets are written under `dist/character-qc/` when generated manually.
