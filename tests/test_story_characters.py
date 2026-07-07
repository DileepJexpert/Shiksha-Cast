"""Validation for the STORY-UNIVERSE cast (separate from the Kinnu kids cast)."""
import json
from pathlib import Path

from PIL import Image

from shiksha_cast.cartoon.build import _adv_pose
from shiksha_cast.cartoon.rig2 import SkeletalCharacter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARS = PROJECT_ROOT / "assets" / "cartoon" / "characters"
FATHER = CHARS / "story_father_hd"
YOUNG = CHARS / "story_young_hd"
STORY_CAST = (FATHER, YOUNG)


def test_story_cast_uses_separate_prefixed_characters():
    for char_dir in STORY_CAST:
        assert char_dir.exists()
        assert char_dir.name.startswith("story_")


def test_story_cast_required_parts_exist():
    required = {
        "rig2.json", "head.png", "torso.png",
        "upper_arm_left.png", "upper_arm_right.png",
        "forearm_left.png", "forearm_right.png",
        "thigh_left.png", "thigh_right.png",
        "shin_left.png", "shin_right.png",
        "knee_left.png", "knee_right.png",
        "eyes_open.png", "eyes_closed.png", "eyes_happy.png",
        "brows_neutral.png", "brows_happy.png", "brows_sad.png", "brows_surprised.png",
        "mouth_X.png", "mouth_B.png", "mouth_C.png", "mouth_D.png", "mouth_E.png",
    }
    for char_dir in STORY_CAST:
        missing = sorted(p for p in required if not (char_dir / p).exists())
        assert not missing
    assert (FATHER / "side_walk.png").exists()


def test_story_father_declares_option_c_manifest():
    manifest_path = FATHER / "asset_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["asset_route"] == "option_c_external_part_sheet"
    assert manifest["source_assets"]["front_parts_sheet"].endswith("story_father_parts_sheet.png")
    assert manifest["capabilities"]["talk"] is True
    assert manifest["capabilities"]["side_walk_sprite"] is True


def _route(char_dir: Path) -> str:
    mf = char_dir / "asset_manifest.json"
    if mf.exists():
        return json.loads(mf.read_text(encoding="utf-8")).get("asset_route", "")
    return ""


def test_story_cast_parts_are_real_transparent_art():
    # Two asset routes: the full parts-sheet puppet has real separate limbs; the
    # local hybrid carries the whole figure in torso.png (+ side_walk sprite) with
    # transparent limb placeholders. Check whichever the character actually uses.
    for char_dir in STORY_CAST:
        if _route(char_dir) == "local_hybrid_talking_figure_plus_side_walk":
            names = ("torso", "side_walk")
        else:
            names = ("upper_arm_left", "forearm_right", "thigh_left", "shin_right", "torso")
        for name in names:
            im = Image.open(char_dir / f"{name}.png").convert("RGBA")
            assert im.getchannel("A").getbbox() is not None
            assert im.width > 40 and im.height > 40
            assert (char_dir / f"{name}.png").stat().st_size > 1000


def test_story_cast_is_articulated():
    for char_dir in STORY_CAST:
        ch = SkeletalCharacter(char_dir)
        assert ch.bone["upper_arm"] > 0 and ch.bone["thigh"] > 0
        pose, x_cur, _facing, _bob = _adv_pose(
            char_dir.name,
            [{"who": char_dir.name, "do": "walkto", "to": 0.65, "start": 0.0, "end": 2.0}],
            0.8,
            30,
            0.0,
            0.30,
            "right",
        )
        assert abs(pose["leg_left"][0]) > 1
        assert abs(pose["arm_right"][0]) > 1
        assert x_cur > 0.30


def test_story_father_composes_without_clipping():
    ch = SkeletalCharacter(FATHER)
    img = ch.compose({"mouth": "D", "head": 6}, padding=ch.render_padding)
    bbox = img.getchannel("A").getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    assert left > 10
    assert top > 10
    assert img.width - right > 10
    assert img.height - bottom > 10


def test_story_father_can_render_side_walk_sprite():
    ch = SkeletalCharacter(FATHER)
    frame = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ch.place(frame, {"side_sprite": "side_walk"}, 0.5, 680, 560, facing="right")
    assert frame.getchannel("A").getbbox() is not None


def test_story_father_mouth_overlay_changes_pixels():
    """Opening the mouth must actually paint different pixels (lip-sync works)."""
    ch = SkeletalCharacter(FATHER)
    closed = ch.compose({"mouth": "X"}, padding=ch.render_padding)
    wide = ch.compose({"mouth": "D"}, padding=ch.render_padding)
    assert closed.tobytes() != wide.tobytes()
