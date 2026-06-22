from __future__ import annotations

from pathlib import Path

from shiksha_cast.config import load_channel_config
from shiksha_cast.render import RenderResult, render_chapter


def run_render(chapter: str, project_root: Path, force: bool = False) -> RenderResult:
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution
    return render_chapter(chapter, project_root, width=w, height=h, force=force)
