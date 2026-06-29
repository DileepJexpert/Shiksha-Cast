from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint

app = typer.Typer(
    name="shiksha-cast",
    help="Turn PDF slide decks + narration scripts into YouTube-ready MP4 videos.",
    no_args_is_help=True,
    invoke_without_command=True,
)


def _find_project_root() -> Path:
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        if (d / "config" / "channel.yaml").exists():
            return d
    raise typer.BadParameter(
        "Could not find project root (no config/channel.yaml). "
        "Run from inside the shiksha-cast project or pass --root."
    )


@app.command()
def render(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Re-render all slides, ignoring cache"),
) -> None:
    """Render PDF slides to 1920x1080 PNGs."""
    from shiksha_cast.pipeline import run_render

    project_root = root or _find_project_root()
    result = run_render(chapter, project_root, force=force)

    rprint(f"[bold]{result.chapter}[/bold]: {len(result.slide_paths)} slides")
    rprint(f"  rendered: {result.rendered_count}  cached: {result.cached_count}")
    for p in result.slide_paths:
        rprint(f"  [dim]{p}[/dim]")


@app.command()
def speak(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Regenerate all audio, ignoring cache"),
) -> None:
    """Generate narration audio from script."""
    from shiksha_cast.pipeline import run_speak

    project_root = root or _find_project_root()
    result = run_speak(chapter, project_root, force=force)

    rprint(f"[bold]{result.chapter}[/bold]: {len(result.audio_paths)} audio clips")
    rprint(f"  synthesized: {result.synthesized_count}  cached: {result.cached_count}")
    for p, d in zip(result.audio_paths, result.durations):
        rprint(f"  [dim]{p}[/dim]  ({d:.1f}s)")


@app.command()
def captions(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate SRT captions from script + audio durations."""
    from shiksha_cast.config import load_channel_config, load_script, resolve_chapter
    from shiksha_cast.captions import write_captions
    from shiksha_cast.pipeline import run_speak

    project_root = root or _find_project_root()
    cfg = load_channel_config(project_root)
    chapter_dir, _ = resolve_chapter(project_root, chapter)
    script = load_script(chapter_dir)

    speak_result = run_speak(chapter, project_root)

    srt_path = write_captions(
        chapter=chapter,
        project_root=project_root,
        narrations=[s.narration for s in script.slides],
        durations=speak_result.durations,
        pad_before_s=cfg.timing.pad_before_ms / 1000,
        pad_after_s=cfg.timing.pad_after_ms / 1000,
        min_slide_s=cfg.timing.min_slide_s,
    )
    rprint(f"[bold]Captions written:[/bold] {srt_path}")


@app.command()
def build(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Rebuild everything, ignoring cache"),
) -> None:
    """Full pipeline: render -> speak -> assemble -> caption -> MP4."""
    from shiksha_cast.assemble import FFmpegNotFoundError
    from shiksha_cast.pipeline import run_build

    project_root = root or _find_project_root()
    rprint("[bold]Starting full build...[/bold]")

    try:
        result = run_build(chapter, project_root, force=force)
    except FFmpegNotFoundError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    rprint()
    rprint(f"[bold green]Build complete![/bold green]")
    rprint(f"  Slides: {result.render.rendered_count} rendered, {result.render.cached_count} cached")
    rprint(f"  Audio:  {result.speak.synthesized_count} synthesized, {result.speak.cached_count} cached")
    rprint(f"  Video:  {result.assemble.video_path}")
    rprint(f"  SRT:    {result.srt_path}")
    rprint(f"  Duration: {result.assemble.total_duration:.1f}s")


@app.command(name="ai-build")
def ai_build(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Rebuild everything, ignoring cache"),
) -> None:
    """AI pipeline: generate images from visual prompts -> speak -> Ken Burns -> MP4."""
    from shiksha_cast.assemble import FFmpegNotFoundError
    from shiksha_cast.pipeline import run_ai_build

    project_root = root or _find_project_root()
    rprint("[bold]Starting AI build...[/bold]")
    rprint("[dim]This generates contextual images from your visual_prompt fields.[/dim]")

    try:
        result = run_ai_build(chapter, project_root, force=force)
    except FFmpegNotFoundError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except ImportError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        rprint("[dim]Install with: pip install -e \".[imagegen]\"[/dim]")
        raise typer.Exit(code=1)

    rprint()
    rprint(f"[bold green]AI Build complete![/bold green]")
    rprint(f"  Images: {result.visuals.generated_count} generated, {result.visuals.cached_count} cached")
    rprint(f"  Audio:  {result.speak.synthesized_count} synthesized, {result.speak.cached_count} cached")
    rprint(f"  Video:  {result.assemble.video_path}")
    rprint(f"  SRT:    {result.srt_path}")
    rprint(f"  Duration: {result.assemble.total_duration:.1f}s")


@app.command()
def concat(
    videos: List[Path] = typer.Argument(..., help="MP4 files to concatenate in order"),
    output: Path = typer.Option("dist/combined.mp4", "--output", "-o", help="Output MP4 path"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Concatenate multiple MP4 videos into one (e.g. combine chapters)."""
    from shiksha_cast.assemble import FFmpegNotFoundError, concat_clips

    project_root = root or _find_project_root()

    resolved = []
    for v in videos:
        p = v if v.is_absolute() else project_root / v
        if not p.exists():
            rprint(f"[bold red]Error:[/bold red] Video not found: {p}")
            raise typer.Exit(code=1)
        resolved.append(p)

    out_path = output if output.is_absolute() else project_root / output
    rprint(f"[bold]Concatenating {len(resolved)} videos...[/bold]")
    for v in resolved:
        rprint(f"  [dim]{v}[/dim]")

    try:
        concat_clips(resolved, out_path)
    except FFmpegNotFoundError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    rprint(f"\n[bold green]Done![/bold green] Output: {out_path}")


@app.command()
def meta(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. s06-yawning"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate YouTube metadata (title, description, tags, chapters) -> dist/<id>.youtube.md."""
    from shiksha_cast.metadata import build_metadata, write_metadata

    project_root = root or _find_project_root()
    m = build_metadata(chapter, project_root)
    out_path = write_metadata(chapter, project_root)

    rprint(f"[bold]Title:[/bold] {m.title}")
    rprint(f"[bold]Tags:[/bold] [dim]{', '.join(m.tags)}[/dim]")
    rprint(f"[bold]Chapters:[/bold] {len(m.chapters)}")
    rprint(f"[bold green]Metadata written:[/bold green] {out_path}")


@app.command()
def thumb(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. s06-yawning"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Render a 1280x720 YouTube thumbnail -> dist/<id>.thumb.png."""
    from shiksha_cast.thumbnail import write_thumbnail

    project_root = root or _find_project_root()
    out_path = write_thumbnail(chapter, project_root)
    rprint(f"[bold green]Thumbnail written:[/bold green] {out_path}")


@app.command(name="make-assets")
def make_assets(
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Regenerate assets that already exist"),
) -> None:
    """Generate branded intro/outro clips + a placeholder music bed into assets/."""
    from shiksha_cast.assets import generate_branding_assets

    project_root = root or _find_project_root()
    rprint("[bold]Generating branding assets...[/bold]")
    created = generate_branding_assets(project_root, force=force)
    for label, path in created:
        rprint(f"  [green]{label}[/green]: {path}")
    rprint("[dim]These are wired into builds automatically (channel.yaml branding).[/dim]")


@app.command(name="parallax-check")
def parallax_check(
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Image to test with (defaults to a generated test card)"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Verify DepthFlow 2.5D parallax works on this machine (renders a 2s test clip)."""
    import tempfile

    from shiksha_cast.animate import ParallaxUnavailable, depthflow_available, render_parallax_video

    project_root = root or _find_project_root()
    if not depthflow_available():
        rprint("[bold red]DepthFlow not found.[/bold red] Install it with:")
        rprint("  [cyan]pip install depthflow[/cyan]")
        rprint("[dim]Then set imagegen.motion: parallax in config/channel.yaml.[/dim]")
        raise typer.Exit(code=1)

    rprint("[bold]DepthFlow found.[/bold] Rendering a 2s test clip...")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        if image is None:
            from shiksha_cast.branding import CHANNEL_NAME, TEXT_LIGHT, font, new_canvas
            img, d = new_canvas(1280, 720)
            d.text((80, 320), CHANNEL_NAME, font=font("seguibl.ttf", 90), fill=TEXT_LIGHT)
            image = tdp / "test_card.png"
            img.save(image)
        out = project_root / "dist" / "parallax_test.mp4"
        try:
            render_parallax_video(Path(image), out, duration=2.0, fps=30, width=1280, height=720)
        except ParallaxUnavailable as e:
            rprint(f"[bold red]Parallax render failed:[/bold red] {e}")
            rprint("[dim]Your DepthFlow version may use different CLI flags — set "
                   "imagegen.parallax_command in config/channel.yaml to match.[/dim]")
            raise typer.Exit(code=1)
    rprint(f"[bold green]Success![/bold green] Test clip: {out}")
    rprint("[dim]Enable for builds: set imagegen.motion: parallax in config/channel.yaml,[/dim]")
    rprint("[dim]then run: python -m shiksha_cast ai-build -c <episode>[/dim]")


@app.command(name="new-episode")
def new_episode(
    topic: str = typer.Argument(..., help='Episode topic, e.g. "RO water purifier review"'),
    category: str = typer.Option("general-knowledge", "--category", help="content/ subfolder, e.g. how-it-works/technology"),
    slug: Optional[str] = typer.Option(None, "--slug", help="Folder name (default: derived from topic)"),
    slides: Optional[int] = typer.Option(None, "--slides", help="Number of slides (default from config)"),
    model: Optional[str] = typer.Option(None, "--model", help="Ollama model override, e.g. qwen2.5:7b"),
    audience: str = typer.Option("Indian students, age 11-16", "--audience", help="Target audience"),
    style: str = typer.Option(
        "Hinglish (mostly English with light Hindi), curious and fun", "--style", help="Narration style"
    ),
    build: bool = typer.Option(False, "--build", help="Run ai-build immediately after generating"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate a new episode script from a topic using a local LLM (Ollama)."""
    from shiksha_cast.config import load_channel_config
    from shiksha_cast.generate import GeneratorUnavailable, write_episode

    project_root = root or _find_project_root()
    cfg = load_channel_config(project_root)

    rprint(f'[bold]Generating script for:[/bold] "{topic}"')
    rprint(f"[dim]via {cfg.generator.provider} ({model or cfg.generator.model}) — this can take a minute...[/dim]")
    try:
        ep_dir, data = write_episode(
            topic, project_root, cfg.generator,
            category=category, slug=slug, n_slides=slides,
            audience=audience, style=style, model=model,
        )
    except GeneratorUnavailable as e:
        rprint(f"[bold red]Cannot generate:[/bold red] {e}")
        raise typer.Exit(code=1)

    ep_id = ep_dir.name
    rprint(f"[bold green]Created:[/bold green] {ep_dir / 'script.yaml'}")
    rprint(f"  Title: {data.get('chapter')}")
    rprint(f"  Slides: {len(data.get('slides', []))}")
    rprint(f"[dim]Review/edit the narration, then build:[/dim] python -m shiksha_cast ai-build -c {ep_id}")

    if build:
        from shiksha_cast.assemble import FFmpegNotFoundError
        from shiksha_cast.pipeline import run_ai_build

        rprint("\n[bold]Building video...[/bold]")
        try:
            result = run_ai_build(ep_id, project_root)
        except FFmpegNotFoundError as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)
        rprint(f"[bold green]Video:[/bold green] {result.assemble.video_path}")


@app.command(name="ollama-check")
def ollama_check(
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Check the local Ollama server and list pulled models."""
    from shiksha_cast.config import load_channel_config
    from shiksha_cast.local_ai import LocalAIUnavailable, list_ollama_models

    project_root = root or _find_project_root()
    cfg = load_channel_config(project_root)
    rprint(f"[bold]Ollama URL:[/bold] {cfg.generator.url}")
    rprint(f"[bold]Configured model:[/bold] {cfg.generator.model}")
    try:
        models = list_ollama_models(cfg.generator.url)
    except LocalAIUnavailable as e:
        rprint(f"[bold red]Ollama unavailable:[/bold red] {e}")
        rprint("[dim]Start Ollama, then pull a local model, for example:[/dim]")
        rprint(f"  [cyan]ollama pull {cfg.generator.model}[/cyan]")
        raise typer.Exit(code=1)

    if not models:
        rprint("[yellow]Ollama is running, but no models are pulled yet.[/yellow]")
        rprint(f"  [cyan]ollama pull {cfg.generator.model}[/cyan]")
        return

    rprint("[bold green]Ollama is running.[/bold green] Local models:")
    for m in models:
        size = f" ({m.size / (1024 ** 3):.1f} GB)" if m.size else ""
        marker = " [green]<- configured[/green]" if m.name == cfg.generator.model else ""
        rprint(f"  - {m.name}{size}{marker}")


@app.command(name="new-story")
def new_story(
    topic: str = typer.Argument(..., help='Story topic, e.g. "friction with Kinnu and Gappu"'),
    category: str = typer.Option("stories", "--category", help="content/ subfolder"),
    slug: Optional[str] = typer.Option(None, "--slug", help="Folder name (default: derived from topic)"),
    scenes: int = typer.Option(6, "--scenes", help="Number of story scenes"),
    model: Optional[str] = typer.Option(None, "--model", help="Ollama model override"),
    audience: str = typer.Option("kids age 5-10", "--audience", help="Target audience"),
    style: str = typer.Option(
        "Hinglish, funny and warm, like a playful science cartoon",
        "--style",
        help="Story/directing style",
    ),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate a two-character story plan with local Ollama.

    Writes both story.yaml (future multi-character animator) and script.yaml
    (current TTS/build-compatible dialogue with F:/M: speaker tags).
    """
    from shiksha_cast.config import load_channel_config
    from shiksha_cast.story import StoryUnavailable, write_story_episode

    project_root = root or _find_project_root()
    cfg = load_channel_config(project_root)

    rprint(f'[bold]Generating local story for:[/bold] "{topic}"')
    rprint(f"[dim]via Ollama ({model or cfg.generator.model}); no cloud API is used.[/dim]")
    try:
        ep_dir, story, script = write_story_episode(
            topic,
            project_root,
            cfg.generator,
            category=category,
            slug=slug,
            n_scenes=scenes,
            audience=audience,
            style=style,
            model=model,
        )
    except StoryUnavailable as e:
        rprint(f"[bold red]Cannot generate story:[/bold red] {e}")
        raise typer.Exit(code=1)

    ep_id = ep_dir.name
    rprint(f"[bold green]Created:[/bold green] {ep_dir}")
    rprint(f"  story:  {ep_dir / 'story.yaml'}")
    rprint(f"  script: {ep_dir / 'script.yaml'}")
    rprint(f"  Title:  {story.get('chapter')}")
    rprint(f"  Scenes: {len(story.get('scenes', []))}")
    rprint(f"[dim]Current build path:[/dim] python -m shiksha_cast ai-build -c {ep_id}")
    rprint(f"[dim]Talking-host path:[/dim] python scripts/build_talking_episode.py {ep_id}")
    rprint(f"[dim]Future path:[/dim] multi-character renderer will consume story.yaml directly.")


@app.command()
def shorts(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID"),
    start: float = typer.Option(0.0, "--start", help="Start time in seconds"),
    duration: float = typer.Option(45.0, "--duration", help="Short length in seconds (max ~60)"),
    hook: Optional[str] = typer.Option(None, "--hook", help="Hook text at the top (default: episode title)"),
    count: int = typer.Option(1, "--count", help="How many Shorts (sequential windows)"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Create vertical 9:16 Shorts (blurred fill + big captions + hook) -> dist/shorts/."""
    from shiksha_cast.shorts import build_short

    project_root = root or _find_project_root()
    for i in range(count):
        out = build_short(
            chapter, project_root,
            start_s=start + i * duration, duration_s=duration, hook_text=hook, index=i + 1,
        )
        rprint(f"[bold green]Short {i + 1}:[/bold green] {out}")


@app.command()
def thumbs(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Render thumbnail variants (curiosity/exam/kids/hinglish) -> dist/<id>.thumb.<style>.png."""
    from shiksha_cast.thumbnail import write_thumbnail_variants

    project_root = root or _find_project_root()
    for p in write_thumbnail_variants(chapter, project_root):
        rprint(f"  [green]{p.stem.split('.')[-1]}[/green]: {p}")


@app.command()
def package(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID"),
    no_short: bool = typer.Option(False, "--no-short", help="Skip generating a Short"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Assemble a ready-to-upload folder (video, thumbnail, captions, title/desc/tags, Short)."""
    from shiksha_cast.package import build_package

    project_root = root or _find_project_root()
    rprint(f"[bold]Packaging {chapter}...[/bold]")
    pkg = build_package(chapter, project_root, include_short=not no_short)
    rprint(f"[bold green]Upload package ready:[/bold green] {pkg}")
    rprint("[dim]See README.txt inside for the upload checklist.[/dim]")


@app.command(name="cartoon-build")
def cartoon_build(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Cartoon episode id (folder with scenes.yaml)"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output MP4 path"),
) -> None:
    """Render a cutout-CARTOON episode from scenes.yaml (separated-part characters that
    walk/wave/point/blink/talk, per-character voices, music, captions)."""
    import glob

    from shiksha_cast.cartoon.build import build_episode

    project_root = root or _find_project_root()
    matches = glob.glob(str(project_root / "content" / "**" / chapter / "scenes.yaml"), recursive=True)
    if not matches:
        raise typer.BadParameter(f"No scenes.yaml found for cartoon episode '{chapter}' under content/.")
    rprint(f"[bold]Building cartoon {chapter}[/bold] from {matches[0]}")
    p = build_episode(matches[0], project_root, out=str(out) if out else None)
    rprint(f"[bold green]Cartoon ready:[/bold green] {p}")


@app.command(name="cartoon-build-3d")
def cartoon_build_3d(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Cartoon episode id (folder with scenes.yaml)"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output MP4 path"),
) -> None:
    """Render a 3D-CARTOON episode: a VRoid VRM character (Blender, posed + lip-synced)
    over the 2D backgrounds, with the same TTS/music/captions pipeline."""
    import glob

    from shiksha_cast.cartoon.build3d import build_episode_3d

    project_root = root or _find_project_root()
    matches = glob.glob(str(project_root / "content" / "**" / chapter / "scenes.yaml"), recursive=True)
    if not matches:
        raise typer.BadParameter(f"No scenes.yaml found for cartoon episode '{chapter}' under content/.")
    rprint(f"[bold]Building 3D cartoon {chapter}[/bold] from {matches[0]}")
    p = build_episode_3d(matches[0], project_root, out=str(out) if out else None)
    rprint(f"[bold green]3D cartoon ready:[/bold green] {p}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
