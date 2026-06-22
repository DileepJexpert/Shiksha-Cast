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
    """Generate narration audio from script (Milestone 2)."""
    raise typer.Exit("speak stage is not yet implemented (Milestone 2)")


@app.command()
def captions(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
) -> None:
    """Generate SRT captions from script + audio durations (Milestone 4)."""
    raise typer.Exit("captions stage is not yet implemented (Milestone 4)")


@app.command()
def build(
    chapter: str = typer.Option(..., "--chapter", "-c", help="Chapter ID, e.g. ch03"),
    root: Optional[Path] = typer.Option(None, "--root", "-r", help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Rebuild everything, ignoring cache"),
) -> None:
    """Full pipeline: render → speak → assemble → caption → package."""
    raise typer.Exit("Full build pipeline is not yet implemented")


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
