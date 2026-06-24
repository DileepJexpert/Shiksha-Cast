"""2.5D parallax animation via DepthFlow (depth-based motion on a still image).

DepthFlow estimates a depth map for an image and renders a 3D parallax video —
much more alive than a flat Ken Burns pan, and it fits an 8 GB GPU. This module
shells out to the DepthFlow CLI (the most stable interface across versions) to
render a silent parallax clip, then muxes the slide's narration audio onto it
with the same padding the rest of the pipeline uses.

If DepthFlow isn't installed or a render fails, build_parallax_clip raises
ParallaxUnavailable so the caller can fall back to Ken Burns — a build never
breaks just because parallax isn't set up.
"""
from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from shiksha_cast.assemble import mux_audio_onto_video


class ParallaxUnavailable(RuntimeError):
    """DepthFlow is missing or failed; caller should fall back to another motion."""


def depthflow_available() -> bool:
    return shutil.which("depthflow") is not None


def _depthflow_args(
    template: str | None,
    image: Path,
    output: Path,
    duration: float,
    fps: int,
    width: int,
    height: int,
) -> list[str]:
    if template:
        filled = template.format(
            image=str(image), output=str(output),
            duration=f"{duration:.3f}", fps=fps, width=width, height=height,
        )
        # posix=False keeps Windows backslashes; strip any leftover quotes.
        return [t.strip('"').strip("'") for t in shlex.split(filled, posix=False)]
    return [
        "depthflow",
        "input", "-i", str(image),
        "main", "-o", str(output),
        "-t", f"{duration:.3f}",
        "-f", str(fps),
        "-w", str(width),
        "-h", str(height),
    ]


def render_parallax_video(
    image: Path,
    output: Path,
    duration: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    command_template: str | None = None,
    timeout_s: int = 600,
) -> Path:
    """Render a silent parallax video from a still image. Raises ParallaxUnavailable."""
    if not depthflow_available():
        raise ParallaxUnavailable(
            "DepthFlow not found on PATH. Install it with: pip install depthflow"
        )
    args = _depthflow_args(command_template, image, output, duration, fps, width, height)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout_s)
    except FileNotFoundError as e:
        raise ParallaxUnavailable(f"Could not launch DepthFlow: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise ParallaxUnavailable(f"DepthFlow timed out after {timeout_s}s") from e
    except subprocess.CalledProcessError as e:
        raise ParallaxUnavailable(
            f"DepthFlow failed (exit {e.returncode}):\n{e.stderr or e.stdout}"
        ) from e
    if not output.exists():
        raise ParallaxUnavailable("DepthFlow ran but produced no output file")
    return output


def build_parallax_clip(
    image_png: Path,
    audio_wav: Path,
    output_mp4: Path,
    duration: float,
    pad_before_s: float = 0.3,
    pad_after_s: float = 0.7,
    min_slide_s: float = 4.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    command_template: str | None = None,
) -> float:
    """Render a parallax-animated slide clip (image -> depth motion + narration).

    Returns the clip duration. Raises ParallaxUnavailable on any DepthFlow issue.
    """
    clip_dur = max(min_slide_s, pad_before_s + duration + pad_after_s)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        silent = Path(td) / "parallax.mp4"
        render_parallax_video(
            image_png, silent, clip_dur,
            fps=fps, width=width, height=height, command_template=command_template,
        )
        mux_audio_onto_video(
            silent, audio_wav, output_mp4,
            clip_dur=clip_dur,
            pad_before_s=pad_before_s,
            fps=fps,
            width=width,
            height=height,
        )
    return clip_dur
