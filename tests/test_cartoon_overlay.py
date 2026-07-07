"""Tests for the in-scene teaching graphics layer (chalkboard + UI overlays)."""
from PIL import Image

from shiksha_cast.cartoon import overlay

W, H = 1920, 1080


def _blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _chalk_pixels(img):
    """Count light (chalk-text / title) pixels painted on a board."""
    px = img.load()
    n = 0
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            r, g, b, a = px[x, y]
            if a > 0 and r > 200 and g > 200 and b > 180:
                n += 1
    return n


def test_fade_envelope():
    assert overlay._fade(0.5, 0.0, 3.0) == 1.0
    assert overlay._fade(-1.0, 0.0, 3.0) == 0.0
    assert overlay._fade(5.0, 0.0, 3.0) == 0.0
    assert 0.0 < overlay._fade(0.1, 0.0, 3.0) < 1.0     # fading in
    assert 0.0 < overlay._fade(2.95, 0.0, 3.0) < 1.0    # fading out


def test_board_is_drawn():
    img = _blank()
    overlay.draw_board(img, {"title": "Test", "lines": ["a", "b"]}, 0.0, W, H)
    assert img.getchannel("A").getbbox() is not None   # something was painted


def test_board_reveals_lines_over_time():
    board = {
        "title": "Addition",
        "lines": [
            {"text": "7 + 5 = 12", "at": 1.0},
            {"text": "carry the 1", "at": 3.0},
            {"text": "Answer: 32", "at": 5.0, "big": True},
        ],
    }
    early = _blank(); overlay.draw_board(early, board, 0.0, W, H)
    mid = _blank(); overlay.draw_board(mid, board, 3.5, W, H)
    late = _blank(); overlay.draw_board(late, board, 6.0, W, H)

    n_early, n_mid, n_late = _chalk_pixels(early), _chalk_pixels(mid), _chalk_pixels(late)
    assert n_early < n_mid < n_late      # each revealed line adds chalk text


def test_overlay_banner_only_visible_in_window():
    overlays = [{"type": "banner", "text": "Let's Learn!", "start": 1.0, "end": 4.0}]

    before = _blank(); overlay.draw_overlays(before, overlays, 0.2, W, H)
    during = _blank(); overlay.draw_overlays(during, overlays, 2.5, W, H)
    after = _blank(); overlay.draw_overlays(after, overlays, 9.0, W, H)

    assert before.getchannel("A").getbbox() is None
    assert during.getchannel("A").getbbox() is not None
    assert after.getchannel("A").getbbox() is None


def test_overlay_callout_and_label_paint():
    for typ in ("callout", "label"):
        img = _blank()
        overlay.draw_overlays(
            img, [{"type": typ, "text": "carry the 1", "pos": [0.5, 0.5],
                   "start": 0.0, "end": 5.0}], 2.0, W, H,
        )
        assert img.getchannel("A").getbbox() is not None
