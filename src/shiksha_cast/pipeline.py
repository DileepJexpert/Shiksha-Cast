from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shiksha_cast.assemble import AssembleResult, assemble_chapter
from shiksha_cast.captions import write_captions
from shiksha_cast.config import load_channel_config, load_script, resolve_chapter
from shiksha_cast.render import RenderResult, render_chapter
from shiksha_cast.speak import SpeakResult, speak_chapter


@dataclass
class BuildResult:
    render: RenderResult
    speak: SpeakResult
    assemble: AssembleResult
    srt_path: Path


def run_render(chapter: str, project_root: Path, force: bool = False) -> RenderResult:
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution
    return render_chapter(chapter, project_root, width=w, height=h, force=force)


def run_speak(chapter: str, project_root: Path, force: bool = False) -> SpeakResult:
    cfg = load_channel_config(project_root)
    chapter_dir, _ = resolve_chapter(project_root, chapter)
    script = load_script(chapter_dir)
    return speak_chapter(chapter, project_root, script, cfg, force=force)


def run_build(chapter: str, project_root: Path, force: bool = False) -> BuildResult:
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution
    chapter_dir, _ = resolve_chapter(project_root, chapter)
    script = load_script(chapter_dir)

    render_result = render_chapter(chapter, project_root, width=w, height=h, force=force)

    speak_result = speak_chapter(chapter, project_root, script, cfg, force=force)

    assemble_result = assemble_chapter(
        chapter=chapter,
        project_root=project_root,
        slide_paths=render_result.slide_paths,
        audio_paths=speak_result.audio_paths,
        durations=speak_result.durations,
        fps=cfg.fps,
        pad_before_s=cfg.timing.pad_before_ms / 1000,
        pad_after_s=cfg.timing.pad_after_ms / 1000,
        min_slide_s=cfg.timing.min_slide_s,
    )

    narrations = [s.narration for s in script.slides]
    srt_path = write_captions(
        chapter=chapter,
        project_root=project_root,
        narrations=narrations,
        durations=speak_result.durations,
        pad_before_s=cfg.timing.pad_before_ms / 1000,
        pad_after_s=cfg.timing.pad_after_ms / 1000,
        min_slide_s=cfg.timing.min_slide_s,
    )

    return BuildResult(
        render=render_result,
        speak=speak_result,
        assemble=assemble_result,
        srt_path=srt_path,
    )
