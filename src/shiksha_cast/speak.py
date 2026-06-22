from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shiksha_cast.cache import BuildManifest, content_hash
from shiksha_cast.config import ChannelConfig, ScriptFile, SlideScript
from shiksha_cast.tts.base import TTSProvider


@dataclass
class SpeakResult:
    chapter: str
    audio_paths: list[Path] = field(default_factory=list)
    durations: list[float] = field(default_factory=list)
    synthesized_count: int = 0
    cached_count: int = 0


def _get_provider(cfg: ChannelConfig) -> TTSProvider:
    name = cfg.voice.provider
    if name == "parler":
        import importlib.util

        # Parler needs all of these; if any is missing, fall back to the stub
        # tone provider so the pipeline still produces a (silent-ish) video.
        required = ("torch", "soundfile", "parler_tts", "transformers")
        missing = [m for m in required if importlib.util.find_spec(m) is None]
        if missing:
            import logging

            logging.getLogger(__name__).warning(
                "Parler TTS unavailable (missing: %s). Falling back to stub tone. "
                "Install real voice with: pip install -e \".[tts]\"",
                ", ".join(missing),
            )
            from shiksha_cast.tts.stub import StubTTSProvider
            return StubTTSProvider()

        from shiksha_cast.tts.parler import ParlerTTSProvider
        return ParlerTTSProvider()
    elif name == "stub":
        from shiksha_cast.tts.stub import StubTTSProvider
        return StubTTSProvider()
    else:
        raise ValueError(f"Unknown TTS provider: {name}")


def speak_chapter(
    chapter: str,
    project_root: Path,
    script: ScriptFile,
    cfg: ChannelConfig,
    force: bool = False,
) -> SpeakResult:
    provider = _get_provider(cfg)
    build_dir = project_root / "build" / chapter
    audio_dir = build_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    manifest = BuildManifest(build_dir)
    result = SpeakResult(chapter=chapter)

    for slide in script.slides:
        out_path = audio_dir / f"slide_{slide.n:03d}.wav"
        voice_desc = slide.voice_description or cfg.voice.description
        cache_key = content_hash(
            slide.narration, voice_desc, provider.name(), str(cfg.voice.sample_rate)
        )

        entry = manifest.get("speak", f"{slide.n}:{cache_key}")

        if not force and entry and out_path.exists():
            result.cached_count += 1
            result.audio_paths.append(out_path)
            result.durations.append(entry["duration"])
            continue

        duration = provider.synthesize(slide.narration, voice_desc, out_path)

        manifest.set("speak", f"{slide.n}:{cache_key}", {
            "output": str(out_path),
            "duration": duration,
            "narration_hash": cache_key,
        })
        result.synthesized_count += 1
        result.audio_paths.append(out_path)
        result.durations.append(duration)

    manifest.save()
    return result
