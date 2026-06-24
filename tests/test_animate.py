from pathlib import Path

import pytest

from shiksha_cast import animate
from shiksha_cast.animate import ParallaxUnavailable, _depthflow_args
from shiksha_cast.config import ImageGenConfig


def test_effective_motion_resolution():
    assert ImageGenConfig().effective_motion() == "kenburns"
    assert ImageGenConfig(kenburns=False).effective_motion() == "static"
    assert ImageGenConfig(motion="parallax").effective_motion() == "parallax"
    # explicit motion overrides the legacy flag
    assert ImageGenConfig(kenburns=True, motion="static").effective_motion() == "static"


def test_default_depthflow_args_keeps_paths_with_spaces():
    args = _depthflow_args(None, Path("a b/img.png"), Path("o u/out.mp4"), 4.2, 30, 1920, 1080)
    assert args[0] == "depthflow"
    assert "a b" in args[args.index("-i") + 1]
    assert args[args.index("-t") + 1] == "4.200"
    assert args[args.index("-f") + 1] == "30"


def test_template_depthflow_args_strips_quotes():
    tmpl = 'depthflow input -i "{image}" main -o "{output}" -t {duration} -f {fps}'
    args = _depthflow_args(tmpl, Path("a b/img.png"), Path("out.mp4"), 4.2, 30, 1920, 1080)
    assert '"' not in " ".join(args)
    assert "a b/img.png" in args or any("a b" in a for a in args)


def test_build_parallax_clip_raises_when_depthflow_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(animate, "depthflow_available", lambda: False)
    with pytest.raises(ParallaxUnavailable):
        animate.build_parallax_clip(
            tmp_path / "img.png", tmp_path / "a.wav", tmp_path / "out.mp4", duration=3.0
        )
