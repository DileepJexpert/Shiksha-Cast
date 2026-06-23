from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shiksha_cast.assemble import AssembleResult, assemble_chapter, build_kenburns_clip, concat_clips
from shiksha_cast.captions import write_captions
from shiksha_cast.config import load_channel_config, load_script, resolve_chapter
from shiksha_cast.render import RenderResult, render_chapter
from shiksha_cast.speak import SpeakResult, speak_chapter
from shiksha_cast.visualize import VisualizeResult, generate_visuals


@dataclass
class BuildResult:
    render: RenderResult
    speak: SpeakResult
    assemble: AssembleResult
    srt_path: Path


@dataclass
class AIBuildResult:
    visuals: VisualizeResult
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

    print(f"[STAGE] Rendering {len(script.slides)} slides from PDF...")
    render_result = render_chapter(chapter, project_root, width=w, height=h, force=force)
    print(f"[PROGRESS] Slides rendered: {render_result.rendered_count} new, {render_result.cached_count} cached")

    print(f"[STAGE] Generating narration audio for {len(script.slides)} slides...")
    speak_result = speak_chapter(chapter, project_root, script, cfg, force=force)
    print(f"[PROGRESS] Audio: {speak_result.synthesized_count} synthesized, {speak_result.cached_count} cached")

    print("[STAGE] Assembling video clips...")
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
    print(f"[PROGRESS] Video assembled: {assemble_result.slide_count} clips, {assemble_result.total_duration:.1f}s total")

    print("[STAGE] Writing captions...")
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
    print(f"[PROGRESS] Captions written to {srt_path}")

    return BuildResult(
        render=render_result,
        speak=speak_result,
        assemble=assemble_result,
        srt_path=srt_path,
    )


def run_ai_build(
    chapter: str,
    project_root: Path,
    force: bool = False,
    fallback_slide_paths: Optional[list[Path]] = None,
) -> AIBuildResult:
    """Build video using AI-generated images with Ken Burns animation."""
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution
    chapter_dir = project_root / "content" / chapter
    if not chapter_dir.is_dir():
        raise FileNotFoundError(f"Chapter directory not found: {chapter_dir}")
    script = load_script(chapter_dir)

    visual_result = generate_visuals(chapter, project_root, script, cfg, force=force)

    speak_result = speak_chapter(chapter, project_root, script, cfg, force=force)

    build_dir = project_root / "build" / chapter
    clips_dir = build_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    pad_before = cfg.timing.pad_before_ms / 1000
    pad_after = cfg.timing.pad_after_ms / 1000
    min_slide = cfg.timing.min_slide_s

    clip_paths: list[Path] = []
    total_dur = 0.0

    for i, (img_path, audio, dur) in enumerate(
        zip(visual_result.image_paths, speak_result.audio_paths, speak_result.durations)
    ):
        clip_path = clips_dir / f"clip_{i + 1:03d}.mp4"

        if img_path and img_path.exists() and cfg.imagegen.kenburns:
            clip_dur = build_kenburns_clip(
                img_path, audio, clip_path,
                duration=dur,
                effect_index=i,
                pad_before_s=pad_before,
                pad_after_s=pad_after,
                min_slide_s=min_slide,
                fps=cfg.fps,
                width=w,
                height=h,
            )
        elif img_path and img_path.exists():
            from shiksha_cast.assemble import build_slide_clip
            clip_dur = build_slide_clip(
                img_path, audio, clip_path,
                duration=dur,
                pad_before_s=pad_before,
                pad_after_s=pad_after,
                min_slide_s=min_slide,
                fps=cfg.fps,
            )
        elif fallback_slide_paths and i < len(fallback_slide_paths):
            from shiksha_cast.assemble import build_slide_clip
            clip_dur = build_slide_clip(
                fallback_slide_paths[i], audio, clip_path,
                duration=dur,
                pad_before_s=pad_before,
                pad_after_s=pad_after,
                min_slide_s=min_slide,
                fps=cfg.fps,
            )
        else:
            from shiksha_cast.assemble import build_slide_clip
            placeholder = build_dir / "slides" / f"slide_{i + 1:03d}.png"
            if not placeholder.exists():
                raise FileNotFoundError(
                    f"Slide {i + 1}: no AI image and no fallback slide found. "
                    "Add a visual_prompt to generate an image, or provide a PDF."
                )
            clip_dur = build_slide_clip(
                placeholder, audio, clip_path,
                duration=dur,
                pad_before_s=pad_before,
                pad_after_s=pad_after,
                min_slide_s=min_slide,
                fps=cfg.fps,
            )

        clip_paths.append(clip_path)
        total_dur += clip_dur

    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    output_mp4 = dist_dir / f"{chapter}.mp4"
    concat_clips(clip_paths, output_mp4)

    narrations = [s.narration for s in script.slides]
    srt_path = write_captions(
        chapter=chapter,
        project_root=project_root,
        narrations=narrations,
        durations=speak_result.durations,
        pad_before_s=pad_before,
        pad_after_s=pad_after,
        min_slide_s=min_slide,
    )

    return AIBuildResult(
        visuals=visual_result,
        speak=speak_result,
        assemble=AssembleResult(
            video_path=output_mp4,
            slide_count=len(clip_paths),
            total_duration=total_dur,
        ),
        srt_path=srt_path,
    )
