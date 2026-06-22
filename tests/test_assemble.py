import subprocess
from pathlib import Path

import pytest

from shiksha_cast.assemble import assemble_chapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ffmpeg_available = subprocess.run(
    ["ffmpeg", "-version"], capture_output=True
).returncode == 0


@pytest.mark.skipif(not ffmpeg_available, reason="ffmpeg not installed")
def test_assemble_produces_mp4():
    slides_dir = PROJECT_ROOT / "build" / "ch03" / "slides"
    audio_dir = PROJECT_ROOT / "build" / "ch03" / "audio"
    if not slides_dir.exists() or not audio_dir.exists():
        pytest.skip("Run 'shiksha-cast build --chapter ch03' first")

    slide_paths = sorted(slides_dir.glob("slide_*.png"))
    audio_paths = sorted(audio_dir.glob("slide_*.wav"))
    if not slide_paths or not audio_paths:
        pytest.skip("No slides or audio found")

    durations = [3.0] * len(slide_paths)
    result = assemble_chapter(
        "ch03", PROJECT_ROOT, slide_paths, audio_paths, durations
    )
    assert result.video_path.exists()
    assert result.video_path.suffix == ".mp4"
    assert result.slide_count == len(slide_paths)
