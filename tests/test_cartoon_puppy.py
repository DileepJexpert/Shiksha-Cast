from pathlib import Path

from shiksha_cast.cartoon.build import _adv_pose
from shiksha_cast.cartoon.rig2 import SkeletalCharacter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOTI = PROJECT_ROOT / "assets" / "cartoon" / "characters" / "moti_hd"


def test_moti_hd_required_parts_exist():
    required = {
        "rig2.json", "head.png", "head_back.png", "torso.png", "tail.png",
        "upper_arm_left.png", "upper_arm_right.png",
        "forearm_left.png", "forearm_right.png",
        "thigh_left.png", "thigh_right.png",
        "shin_left.png", "shin_right.png",
        "knee_left.png", "knee_right.png",
        "eyes_open.png", "eyes_closed.png", "eyes_happy.png",
        "brows_neutral.png", "brows_happy.png", "brows_sad.png", "brows_surprised.png",
        "mouth_X.png", "mouth_A.png", "mouth_B.png", "mouth_C.png", "mouth_D.png",
        "mouth_E.png", "mouth_F.png", "mouth_G.png", "mouth_H.png", "mouth_sad.png",
    }
    missing = sorted(p for p in required if not (MOTI / p).exists())
    assert not missing


def test_moti_hd_tail_joint_is_configured():
    ch = SkeletalCharacter(MOTI)

    assert "tail" in ch.joints
    assert "tail" in ch.pivot
    assert ch.neck_stub is True
    assert ch.pivot["tail"][1] < 0.4
    assert ch.joints["tail"][1] > ch.joints["shoulder_right"][1]


def test_moti_hd_compose_does_not_clip_with_tail_and_jump_pose():
    ch = SkeletalCharacter(MOTI)
    pose = {
        "arm_left": (76, 18), "arm_right": (-76, -18),
        "leg_left": (-48, 74), "leg_right": (48, -74),
        "tail": 28, "mouth": "D", "eyes": "happy", "brows": "happy",
    }

    img = ch.compose(pose, padding=ch.render_padding)
    bbox = img.getchannel("A").getbbox()

    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 15
    assert top > 15
    assert img.width - right > 15
    assert img.height - bottom > 15


def test_moti_hd_bark_opens_mouth_and_wags_tail():
    actions = [{"who": "moti_hd", "do": "bark", "start": 0.0, "end": 2.0}]

    pose, x_cur, facing, bob = _adv_pose(
        "moti_hd", actions, t=0.2, fps=15, phase_off=0.0, x_frac=0.50, facing0="right",
    )

    assert pose["mouth"] in {"D", "X"}
    assert abs(pose["tail"]) > 5
    assert pose["eyes"] == "happy"
    assert x_cur == 0.50
    assert facing == "right"
