from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shiksha_cast.assemble import (
    AssembleResult,
    assemble_chapter,
    build_kenburns_clip,
    concat_clips,
    mix_music_bed,
    probe_duration,
)
from shiksha_cast.captions import write_captions
from shiksha_cast.config import find_chapter_dir, load_channel_config, load_script
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


def _branding_asset(project_root: Path, rel: Optional[str]) -> Optional[Path]:
    """Resolve a branding asset path from config; return it only if it exists."""
    if not rel:
        return None
    p = Path(rel)
    if not p.is_absolute():
        p = project_root / p
    return p if p.exists() else None


def run_render(chapter: str, project_root: Path, force: bool = False) -> RenderResult:
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution
    return render_chapter(chapter, project_root, width=w, height=h, force=force)


def run_speak(chapter: str, project_root: Path, force: bool = False) -> SpeakResult:
    cfg = load_channel_config(project_root)
    chapter_dir = find_chapter_dir(project_root, chapter)
    script = load_script(chapter_dir)
    return speak_chapter(chapter, project_root, script, cfg, force=force)


def run_build(chapter: str, project_root: Path, force: bool = False) -> BuildResult:
    cfg = load_channel_config(project_root)
    w, h = cfg.resolution

    chapter_dir = find_chapter_dir(project_root, chapter)
    script = load_script(chapter_dir)

    slides_dir = project_root / "build" / chapter / "slides"
    has_pdf = any(chapter_dir.glob("*.pdf"))
    existing_slides = sorted(slides_dir.glob("slide_*.png")) if slides_dir.is_dir() else []

    if has_pdf:
        print(f"[STAGE] Rendering {len(script.slides)} slides from PDF...")
        render_result = render_chapter(chapter, project_root, width=w, height=h, force=force)
        print(f"[PROGRESS] Slides rendered: {render_result.rendered_count} new, {render_result.cached_count} cached")
    elif existing_slides:
        print(f"[STAGE] Using {len(existing_slides)} pre-uploaded slide images")
        render_result = RenderResult(
            chapter=chapter,
            slide_paths=existing_slides,
            pdf_hash="uploaded",
            rendered_count=0,
            cached_count=len(existing_slides),
        )
    else:
        raise FileNotFoundError(
            f"No PDF and no uploaded slides found for {chapter}. "
            "Upload a PDF or PNG slides first."
        )

    print(f"[STAGE] Generating narration audio for {len(script.slides)} slides...")
    speak_result = speak_chapter(chapter, project_root, script, cfg, force=force)
    print(f"[PROGRESS] Audio: {speak_result.synthesized_count} synthesized, {speak_result.cached_count} cached")

    print("[STAGE] Assembling video clips...")
    intro_path = _branding_asset(project_root, cfg.branding.intro)
    outro_path = _branding_asset(project_root, cfg.branding.outro)
    music_path = _branding_asset(project_root, cfg.music.bed)

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
        intro_path=intro_path,
        outro_path=outro_path,
        music_path=music_path,
        music_db=cfg.music.duck_db,
        sample_rate=cfg.voice.sample_rate,
        motion=cfg.imagegen.effective_motion(),
        min_slide_s_values=[s.min_slide_s for s in script.slides],
    )
    print(f"[PROGRESS] Video assembled: {assemble_result.slide_count} clips, {assemble_result.total_duration:.1f}s total")

    print("[STAGE] Writing captions...")
    # Captions must shift by the intro length so they stay in sync.
    intro_offset = probe_duration(intro_path) if intro_path else 0.0
    narrations = [s.narration for s in script.slides]
    srt_path = write_captions(
        chapter=chapter,
        project_root=project_root,
        narrations=narrations,
        durations=speak_result.durations,
        pad_before_s=cfg.timing.pad_before_ms / 1000,
        pad_after_s=cfg.timing.pad_after_ms / 1000,
        min_slide_s=cfg.timing.min_slide_s,
        start_offset_s=intro_offset,
        min_slide_s_values=[s.min_slide_s for s in script.slides],
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
    chapter_dir = find_chapter_dir(project_root, chapter)
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

        if img_path and img_path.exists():
            # Per-slide motion overrides the channel default; unknown -> default.
            allowed = {"parallax", "kenburns", "static"}
            slide = script.slides[i] if i < len(script.slides) else None
            motion = (slide.motion or "").lower() if slide else ""
            if motion not in allowed:
                motion = cfg.imagegen.effective_motion()
            if motion not in allowed:
                motion = "kenburns"
            if motion == "parallax":
                from shiksha_cast.animate import ParallaxUnavailable, build_parallax_clip
                try:
                    clip_dur = build_parallax_clip(
                        img_path, audio, clip_path,
                        duration=dur,
                        pad_before_s=pad_before,
                        pad_after_s=pad_after,
                        min_slide_s=min_slide,
                        fps=cfg.fps,
                        width=w,
                        height=h,
                        command_template=cfg.imagegen.parallax_command,
                    )
                except ParallaxUnavailable as e:
                    print(f"[WARN] Parallax unavailable for slide {i + 1}; "
                          f"using Ken Burns instead. ({e})")
                    motion = "kenburns"
            if motion == "kenburns":
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
            elif motion == "static":
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

    intro_path = _branding_asset(project_root, cfg.branding.intro)
    outro_path = _branding_asset(project_root, cfg.branding.outro)
    music_path = _branding_asset(project_root, cfg.music.bed)

    sequence = list(clip_paths)
    if intro_path:
        sequence.insert(0, intro_path)
        total_dur += probe_duration(intro_path)
        print("[PROGRESS] Prepending intro bumper")
    if outro_path:
        sequence.append(outro_path)
        total_dur += probe_duration(outro_path)
        print("[PROGRESS] Appending outro bumper")

    use_music = bool(music_path)
    concat_target = (build_dir / "ai_body.mp4") if use_music else output_mp4
    concat_clips(sequence, concat_target)

    if music_path:
        print("[PROGRESS] Mixing music bed under narration...")
        mix_music_bed(concat_target, music_path, output_mp4, cfg.music.duck_db, cfg.voice.sample_rate)

    narrations = [s.narration for s in script.slides]
    intro_offset = probe_duration(intro_path) if intro_path else 0.0
    srt_path = write_captions(
        chapter=chapter,
        project_root=project_root,
        narrations=narrations,
        durations=speak_result.durations,
        pad_before_s=pad_before,
        pad_after_s=pad_after,
        min_slide_s=min_slide,
        start_offset_s=intro_offset,
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
