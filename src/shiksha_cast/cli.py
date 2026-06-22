from __future__ import annotations

from pathlib import Path
from typing import Optional

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


@app.command()
def meta(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate YouTube metadata stub (Milestone 5)."""
    raise typer.Exit("meta stage is not yet implemented (Milestone 5)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
