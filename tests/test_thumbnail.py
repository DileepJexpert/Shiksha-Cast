from pathlib import Path

from shiksha_cast.thumbnail import build_thumbnail, write_thumbnail

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_build_thumbnail_dimensions():
    img = build_thumbnail("s06-yawning", PROJECT_ROOT)
    assert img.size == (1280, 720)
    assert img.mode == "RGB"


def test_write_thumbnail_creates_png(tmp_path):
    out = write_thumbnail("s06-yawning", PROJECT_ROOT)
    assert out.exists()
    assert out.name == "s06-yawning.thumb.png"
    assert out.stat().st_size > 1000
