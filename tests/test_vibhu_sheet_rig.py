from pathlib import Path

from shiksha_cast.cartoon.build import _adv_pose
from shiksha_cast.cartoon.rig2 import SkeletalCharacter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = PROJECT_ROOT / "assets" / "cartoon" / "characters" / "vibhu_sheet_hd"

REQUIRED_PARTS = [
    "rig2.json",
    "head.png",
    "head_back.png",
    "torso.png",
    "upper_arm_left.png",
    "upper_arm_right.png",
    "forearm_left.png",
    "forearm_right.png",
    "thigh_left.png",
    "thigh_right.png",
    "shin_left.png",
    "shin_right.png",
    "knee_left.png",
    "knee_right.png",
    "mouth_X.png",
    "mouth_A.png",
    "mouth_B.png",
    "mouth_C.png",
    "mouth_D.png",
    "mouth_E.png",
    "mouth_F.png",
    "mouth_G.png",
    "mouth_H.png",
    "mouth_sad.png",
    "eyes_open.png",
    "eyes_closed.png",
    "eyes_happy.png",
    "brows_neutral.png",
    "brows_happy.png",
    "brows_sad.png",
    "brows_surprised.png",
]


def test_vibhu_sheet_required_parts_exist():
    missing = [part for part in REQUIRED_PARTS if not (CHAR_DIR / part).exists()]
    assert not missing


def test_vibhu_sheet_compose_does_not_clip():
    ch = SkeletalCharacter(CHAR_DIR)
    pose = {
        "arm_left": (140, 8),
        "arm_right": (-140, -8),
        "leg_left": (0, 0),
        "leg_right": (0, 0),
        "mouth": "D",
        "eyes": "happy",
        "brows": "happy",
    }
    img = ch.compose(pose, padding=ch.render_padding)
    bbox = img.getchannel("A").getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 15
    assert top > 15
    assert img.width - right > 15
    assert img.height - bottom > 15


def test_vibhu_sheet_walk_jump_swim_are_available():
    walk_actions = [{"who": "vibhu_sheet_hd", "do": "walkto", "to": 0.65, "start": 0.0, "end": 2.0}]
    walk_pose, walk_x, *_ = _adv_pose("vibhu_sheet_hd", walk_actions, 0.8, 15, 0.0, 0.2, "right")
    assert walk_x > 0.2
    assert abs(walk_pose["leg_left"][0]) > 1

    jump_actions = [{"who": "vibhu_sheet_hd", "do": "jump", "start": 0.0, "end": 1.2}]
    jump_pose, *_rest, jump_bob = _adv_pose(
        "vibhu_sheet_hd",
        jump_actions,
        0.6,
        15,
        0.0,
        0.5,
        "right",
    )
    assert jump_bob > 50
    assert jump_pose["leg_left"][1] > 20

    swim_actions = [{"who": "vibhu_sheet_hd", "do": "swimto", "to": 0.7, "start": 0.0, "end": 2.0}]
    swim_pose, *_ = _adv_pose("vibhu_sheet_hd", swim_actions, 0.6, 15, 0.0, 0.2, "right")
    assert abs(swim_pose["body_angle"]) > 70
    assert swim_pose["water_tint"] is True
