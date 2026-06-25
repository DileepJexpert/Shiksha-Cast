from pathlib import Path

from shiksha_cast.package import build_package
from shiksha_cast.thumbnail import build_thumbnail

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_thumbnail_styles_render_distinct_dimensions():
    for style in ("curiosity", "exam", "kids", "hinglish"):
        img = build_thumbnail("ro-water-review", PROJECT_ROOT, style=style)
        assert img.size == (1280, 720)


def test_build_package_creates_text_assets_and_thumbnails():
    # include_short=False keeps it ffmpeg-free and fast.
    pkg = build_package("ro-water-review", PROJECT_ROOT, include_short=False)
    for name in ("title.txt", "titles.txt", "description.txt", "tags.txt",
                 "pinned-comment.txt", "README.txt", "thumbnail.png"):
        assert (pkg / name).exists(), f"missing {name}"
    # all four thumbnail styles present
    for style in ("curiosity", "exam", "kids", "hinglish"):
        assert (pkg / "thumbnails" / f"{style}.png").exists()
    # title file is non-empty
    assert (pkg / "title.txt").read_text(encoding="utf-8").strip()
