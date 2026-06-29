from pathlib import Path

from PIL import Image

from shiksha_cast.render import render_chapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_render_produces_pngs():
    result = render_chapter("ch03", PROJECT_ROOT)
    assert len(result.slide_paths) == 3
    for p in result.slide_paths:
        assert p.exists()
        img = Image.open(p)
        assert img.size == (1920, 1080)


def test_render_cache():
    render_chapter("ch03", PROJECT_ROOT)
    r2 = render_chapter("ch03", PROJECT_ROOT)
    assert r2.cached_count == 3
    assert r2.rendered_count == 0


def test_render_force():
    result = render_chapter("ch03", PROJECT_ROOT, force=True)
    assert result.rendered_count == 3
    assert result.cached_count == 0
