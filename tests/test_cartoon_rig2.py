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
