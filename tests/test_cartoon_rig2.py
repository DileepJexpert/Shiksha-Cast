from pathlib import Path

from shiksha_cast.cartoon import motion
from shiksha_cast.cartoon.build import _adv_pose
from shiksha_cast.cartoon.rig2 import SkeletalCharacter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_kinnu_hd_side_point_hand_is_not_clipped():
    ch = SkeletalCharacter(PROJECT_ROOT / "assets" / "cartoon" / "characters" / "kinnu_hd")
    pose = {
        "arm_left": (0, 2),
        "arm_right": (-90, -6),
        "leg_left": (0, 0),
        "leg_right": (0, 0),
        "head": 0,
        "eyes": "open",
        "mouth": "X",
        "brows": "neutral",
    }

    img = ch.compose(pose, padding=ch.render_padding)
    bbox = img.getchannel("A").getbbox()

    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 20
    assert top > 20
    assert img.width - right > 20
    assert img.height - bottom > 20


def test_kinnu_hd_head_pivot_is_face_centered():
    ch = SkeletalCharacter(PROJECT_ROOT / "assets" / "cartoon" / "characters" / "kinnu_hd")

    assert 0.36 <= ch.pivot["head"][0] <= 0.41
    assert ch.pivot["head"][0] < 0.5


def test_kinnu_hd_uses_clean_legs_without_visible_knee_buttons():
    ch = SkeletalCharacter(PROJECT_ROOT / "assets" / "cartoon" / "characters" / "kinnu_hd")

    assert ch.joint_caps["knee"] is False


def test_kinnu_hd_forearm_joint_is_trimmed_for_elbow_cap():
    ch = SkeletalCharacter(PROJECT_ROOT / "assets" / "cartoon" / "characters" / "kinnu_hd")

    original = ch._img("forearm_right").getchannel("A")
    trimmed = ch._joint_trimmed_img("forearm_right", "forearm").getchannel("A")
    pivot_y = int(ch._pv("forearm_right", "forearm")[1])
    band_y = max(0, pivot_y - 4)
    original_alpha = sum(original.getpixel((x, band_y)) for x in range(original.width))
    trimmed_alpha = sum(trimmed.getpixel((x, band_y)) for x in range(trimmed.width))

    assert trimmed_alpha < original_alpha


def test_run_cycle_is_stronger_than_walk_cycle():
    walk = motion.walk(1.0)
    run = motion.run(1.0)

    assert abs(run["angles"]["leg_right"]) > abs(walk["angles"]["leg_right"])
    assert abs(run["angles"]["arm_left"]) > abs(walk["angles"]["arm_left"])
    assert run["bob"] > walk["bob"]


def test_advanced_kinnu_run_action_moves_and_swings_limbs():
    actions = [
        {"who": "kinnu_hd", "do": "run", "to": 0.70, "start": 0.0, "end": 2.0},
    ]

    pose, x_cur, facing, bob = _adv_pose(
        "kinnu_hd", actions, t=0.25, fps=15, phase_off=0.0, x_frac=0.20, facing0="right",
    )

    assert x_cur > 0.20
    assert facing == "right"
    assert abs(pose["leg_left"][0]) > 10
    assert abs(pose["arm_right"][0]) > 5
    assert bob > 0


def test_advanced_kinnu_run_target_persists_after_action_ends():
    actions = [
        {"who": "kinnu_hd", "do": "run", "to": 0.70, "start": 0.0, "end": 2.0},
    ]

    pose, x_cur, facing, bob = _adv_pose(
        "kinnu_hd", actions, t=2.5, fps=15, phase_off=0.0, x_frac=0.20, facing0="right",
    )

    assert x_cur == 0.70
    assert facing == "right"
    assert pose["leg_left"] == (0.0, 0.0)
    assert pose["leg_right"] == (0.0, 0.0)


def test_advanced_kinnu_swim_rotates_body_horizontal():
    actions = [
        {"who": "kinnu_hd", "do": "swimto", "to": 0.70, "start": 0.0, "end": 2.0},
    ]

    pose, x_cur, facing, bob = _adv_pose(
        "kinnu_hd", actions, t=0.5, fps=15, phase_off=0.0, x_frac=0.20, facing0="right",
    )

    assert x_cur > 0.20
    assert facing == "right"
    assert pose["body_angle"] < -70
    assert pose["body_anchor"] == "center"
    assert pose["water_tint"] is True
    assert abs(pose["arm_left"][0]) > 80
    assert abs(pose["leg_left"][0]) > 1


def test_advanced_kinnu_jump_tucks_legs():
    actions = [
        {"who": "kinnu_hd", "do": "jump", "start": 0.0, "end": 1.2},
    ]

    pose, x_cur, facing, bob = _adv_pose(
        "kinnu_hd", actions, t=0.6, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert x_cur == 0.50
    assert bob > 50
    assert pose["leg_left"][1] > 20
    assert pose["leg_right"][1] < -20
    assert pose["body_angle"] == 0.0
    assert pose["body_anchor"] == "feet"
    assert pose["water_tint"] is False


def test_advanced_kinnu_cry_uses_tears_and_frown():
    actions = [
        {"who": "kinnu_hd", "do": "cry", "start": 0.0, "end": 2.0},
    ]

    pose, _x_cur, _facing, _bob = _adv_pose(
        "kinnu_hd", actions, t=0.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert pose["brows"] == "sad"
    assert pose["eyes"] == "closed"
    assert pose["mouth"] == "sad"
    assert pose["tears"] is True


def test_advanced_kinnu_laugh_keeps_eyes_open():
    actions = [
        {"who": "kinnu_hd", "do": "laugh", "start": 0.0, "end": 2.0},
    ]

    pose, _x_cur, _facing, _bob = _adv_pose(
        "kinnu_hd", actions, t=0.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert pose["eyes"] == "open"
    assert pose["mouth"] == "D"
    assert pose["head_turn"] == "center"


def test_advanced_kinnu_head_turn_actions():
    actions = [
        {"who": "kinnu_hd", "do": "look_left", "start": 0.0, "end": 1.0},
        {"who": "kinnu_hd", "do": "look_right", "start": 1.0, "end": 2.0},
        {"who": "kinnu_hd", "do": "look_back", "start": 2.0, "end": 3.0},
        {"who": "kinnu_hd", "do": "look_straight", "start": 3.0, "end": 4.0},
    ]

    pose_left, *_ = _adv_pose(
        "kinnu_hd", actions, t=0.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )
    pose_right, *_ = _adv_pose(
        "kinnu_hd", actions, t=1.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )
    pose_back, *_ = _adv_pose(
        "kinnu_hd", actions, t=2.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )
    pose_center, *_ = _adv_pose(
        "kinnu_hd", actions, t=3.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert pose_left["head_turn"] == "left"
    assert pose_right["head_turn"] == "right"
    assert pose_back["head_turn"] == "back"
    assert pose_center["head_turn"] == "center"


def test_advanced_pose_includes_tail_wag_value():
    actions = [
        {"who": "kinnu_hd", "do": "laugh", "start": 0.0, "end": 2.0},
    ]

    pose, _x_cur, _facing, _bob = _adv_pose(
        "kinnu_hd", actions, t=0.5, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert "tail" in pose
    assert abs(pose["tail"]) > 1
