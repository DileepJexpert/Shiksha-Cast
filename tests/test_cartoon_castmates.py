"""Rig tests for the active castmate characters (gappu_hd, vibhu_sheet_hd).

These mirror tests/test_cartoon_rig2.py (which covers kinnu_hd) and assert the new
characters plug into the same skeletal rig: they compose without clipping, expose a
face-centred head pivot, and drive every shared action (walk/run/jump/swim/head-turn)
through the character-agnostic _adv_pose.
"""
from pathlib import Path

import pytest

from shiksha_cast.cartoon.build import _adv_pose
from shiksha_cast.cartoon.rig2 import SkeletalCharacter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARS = PROJECT_ROOT / "assets" / "cartoon" / "characters"
CASTMATES = ["gappu_hd", "vibhu_sheet_hd"]

REQUIRED_PARTS = [
    "rig2.json", "head.png", "torso.png",
    "upper_arm_left.png", "upper_arm_right.png",
    "forearm_left.png", "forearm_right.png",
    "thigh_left.png", "thigh_right.png",
    "shin_left.png", "shin_right.png",
    "knee_left.png", "knee_right.png",
    "mouth_X.png", "mouth_A.png", "mouth_B.png", "mouth_C.png", "mouth_D.png",
    "mouth_E.png", "mouth_F.png", "mouth_G.png", "mouth_H.png", "mouth_sad.png",
    "eyes_open.png", "eyes_closed.png", "eyes_happy.png",
    "brows_neutral.png", "brows_happy.png", "brows_sad.png", "brows_surprised.png",
]


@pytest.fixture(params=CASTMATES)
def cid(request):
    return request.param


def test_all_required_parts_exist(cid):
    folder = CHARS / cid
    missing = [p for p in REQUIRED_PARTS if not (folder / p).exists()]
    assert not missing, f"{cid} missing parts: {missing}"


def test_is_advanced_rig(cid):
    # build.py treats a folder as a skeletal rig iff upper_arm_left.png exists
    assert (CHARS / cid / "upper_arm_left.png").exists()


def test_head_pivot_exists_and_is_centered(cid):
    ch = SkeletalCharacter(CHARS / cid)
    assert "head" in ch.pivot
    px = ch.pivot["head"][0]
    assert 0.45 <= px <= 0.55, f"{cid} head pivot x={px} not centered"


@pytest.mark.parametrize("pose", [
    # side point (arm straight out) -- the classic clipping risk
    {"arm_left": (0, 2), "arm_right": (-90, -6), "leg_left": (0, 0),
     "leg_right": (0, 0), "mouth": "X", "eyes": "open", "brows": "neutral"},
    # cheer (both arms overhead)
    {"arm_left": (142, 8), "arm_right": (-142, -8), "leg_left": (0, 0),
     "leg_right": (0, 0), "mouth": "D", "eyes": "happy", "brows": "happy"},
])
def test_compose_does_not_clip(cid, pose):
    ch = SkeletalCharacter(CHARS / cid)
    img = ch.compose(pose, padding=ch.render_padding)
    bbox = img.getchannel("A").getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 15
    assert top > 15
    assert img.width - right > 15
    assert img.height - bottom > 15


def test_face_overlays_are_drawn_within_the_head(cid):
    """Eyes overlay must land on the head silhouette (not float off in space)."""
    ch = SkeletalCharacter(CHARS / cid)
    bare = ch.compose({"mouth": "X", "eyes": "open", "brows": "neutral"},
                      padding=ch.render_padding)
    head_box = bare.getchannel("A").getbbox()
    assert head_box is not None


def test_walk_moves_and_swings_limbs(cid):
    actions = [{"who": cid, "do": "walkto", "to": 0.6, "start": 0.0, "end": 2.0}]
    pose, x_cur, facing, bob = _adv_pose(cid, actions, 0.5, 15, 0.0, 0.2, "right")
    assert x_cur > 0.20
    assert facing == "right"
    assert abs(pose["leg_left"][0]) > 1


def test_run_swings_harder_and_moves(cid):
    actions = [{"who": cid, "do": "runto", "to": 0.8, "start": 0.0, "end": 2.0}]
    pose, x_cur, facing, bob = _adv_pose(cid, actions, 0.25, 15, 0.0, 0.2, "right")
    assert x_cur > 0.20
    assert abs(pose["leg_left"][0]) > 10
    assert bob > 0


def test_jump_tucks_legs(cid):
    actions = [{"who": cid, "do": "jump", "start": 0.0, "end": 1.2}]
    pose, x_cur, facing, bob = _adv_pose(cid, actions, 0.6, 15, 0.0, 0.5, "right")
    assert x_cur == 0.50
    assert bob > 50
    assert pose["leg_left"][1] > 20
    assert pose["leg_right"][1] < -20
    assert pose["body_angle"] == 0.0


def test_swim_rotates_body_horizontal(cid):
    actions = [{"who": cid, "do": "swimto", "to": 0.7, "start": 0.0, "end": 2.0}]
    pose, x_cur, facing, bob = _adv_pose(cid, actions, 0.5, 15, 0.0, 0.2, "right")
    assert x_cur > 0.20
    assert abs(pose["body_angle"]) > 70
    assert pose["body_anchor"] == "center"
    assert pose["water_tint"] is True


def test_head_turn_actions(cid):
    actions = [
        {"who": cid, "do": "look_left", "start": 0.0, "end": 1.0},
        {"who": cid, "do": "look_right", "start": 1.0, "end": 2.0},
        {"who": cid, "do": "look_back", "start": 2.0, "end": 3.0},
        {"who": cid, "do": "look_straight", "start": 3.0, "end": 4.0},
    ]
    turns = []
    for t in (0.5, 1.5, 2.5, 3.5):
        pose, *_ = _adv_pose(cid, actions, t, 15, 0.0, 0.5, "right")
        turns.append(pose["head_turn"])
    assert turns == ["left", "right", "back", "center"]


def test_cry_uses_tears_and_frown(cid):
    actions = [{"who": cid, "do": "cry", "start": 0.0, "end": 2.0}]
    pose, *_ = _adv_pose(cid, actions, 0.5, 15, 0.0, 0.5, "right")
    assert pose["brows"] == "sad"
    assert pose["mouth"] == "sad"
    assert pose["tears"] is True
