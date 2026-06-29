from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from shiksha_cast.cache import BuildManifest, content_hash
from shiksha_cast.config import ChannelConfig, ScriptFile
from shiksha_cast.tts.base import TTSProvider

# In-slide two-host dialogue: lines beginning with a speaker tag are voiced by
# that speaker and stitched together. F:/M: map to default female/male voices;
# explicit Veena voice names also work. N:/narrator: uses the slide/channel default.
_DIALOGUE_TAG = re.compile(
    r"^\s*(F|M|N|kavya|maitri|agastya|vinaya|narrator)\s*:\s*(.*)$", re.IGNORECASE
)
_FEMALE_DEFAULT = "kavya"
_MALE_DEFAULT = "agastya"


def _parse_dialogue(narration: str):
    """Split narration into (voice_or_None, text) segments when it uses speaker
    tags at line starts. Returns None if there are no tags (use single-voice synth)."""
    segs: list[tuple] = []
    cur_voice, cur_text, saw_tag = None, [], False
    for line in narration.splitlines():
        m = _DIALOGUE_TAG.match(line)
        if m:
            saw_tag = True
            if cur_text:
                segs.append((cur_voice, " ".join(cur_text).strip()))
            tag = m.group(1).lower()
            cur_voice = {"f": _FEMALE_DEFAULT, "m": _MALE_DEFAULT,
                         "n": None, "narrator": None}.get(tag, tag)
            cur_text = [m.group(2).strip()]
        else:
            cur_text.append(line.strip())
    if cur_text:
        segs.append((cur_voice, " ".join(cur_text).strip()))
    if not saw_tag:
        return None
    segs = [(v, t) for v, t in segs if t]
    return segs or None


def _synthesize_dialogue(provider, segments, voice_desc, out_path, default_speaker) -> float:
    """Synthesize each speaker segment with its own voice and stitch into one wav."""
    import numpy as np
    import soundfile as sf

    parts, sr = [], None
    for i, (voice, text) in enumerate(segments):
        provider.set_speaker(voice or default_speaker or "kavya")
        tmp = out_path.parent / f".seg_{out_path.stem}_{i}.wav"
        provider.synthesize(text, voice_desc, tmp)
        a, sr = sf.read(str(tmp))
        parts.append(np.asarray(a, dtype="float32"))
        parts.append(np.zeros(int(sr * 0.28), dtype="float32"))  # pause between turns
        try:
            tmp.unlink()
        except OSError:
            pass
    sr = sr or 24000
    audio = np.concatenate(parts) if parts else np.zeros(int(sr * 0.2), dtype="float32")
    sf.write(str(out_path), audio, sr)
    return len(audio) / sr


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
        return ParlerTTSProvider(model_name=cfg.voice.model)
    elif name == "kokoro":
        from shiksha_cast.tts.kokoro import KokoroTTSProvider

        # For Kokoro, voice.model holds the preset voice name (e.g. "af_heart").
        # Tolerate a leftover Parler HF id ("org/model") by falling back to default.
        voice = cfg.voice.model
        if not voice or "/" in voice:
            voice = "af_heart"
        return KokoroTTSProvider(voice=voice)
    elif name == "veena":
        from shiksha_cast.tts.veena import VeenaTTSProvider

        # For Veena, voice.model holds the speaker name (kavya/agastya/maitri/vinaya).
        speaker = cfg.voice.model
        if not speaker or "/" in speaker:
            speaker = "kavya"
        return VeenaTTSProvider(speaker=speaker)
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

    try:
        _speak_slides(provider, script, cfg, audio_dir, manifest, result, force)
    finally:
        # Always release the TTS backend (e.g. the Veena worker subprocess holding
        # GPU VRAM) so it can't be orphaned and clog the GPU for the next run.
        close = getattr(provider, "close", None)
        if callable(close):
            close()

    manifest.save()
    return result


def _speak_slides(provider, script, cfg, audio_dir, manifest, result, force) -> None:
    total = len(script.slides)
    for slide in script.slides:
        out_path = audio_dir / f"slide_{slide.n:03d}.wav"
        voice_desc = slide.voice_description or cfg.voice.description
        slide_voice = getattr(slide, "voice", None)
        # Per-slide voice is appended to the key ONLY when set, so slides without it
        # keep the same hash (backward compatible with existing caches).
        key_parts = [slide.narration, voice_desc, provider.name(), str(cfg.voice.sample_rate)]
        if slide_voice:
            key_parts.append(slide_voice)
        cache_key = content_hash(*key_parts)

        entry = manifest.get("speak", f"{slide.n}:{cache_key}")

        if not force and entry and out_path.exists():
            result.cached_count += 1
            result.audio_paths.append(out_path)
            result.durations.append(entry["duration"])
            print(f"[PROGRESS] Audio slide {slide.n}/{total}: cached ({entry['duration']:.1f}s)")
            continue

        print(f"[PROGRESS] Audio slide {slide.n}/{total}: synthesizing...")
        # In-slide dialogue (F:/M: tagged lines) -> multi-voice stitched clip.
        segments = _parse_dialogue(slide.narration) if hasattr(provider, "set_speaker") else None
        if segments:
            duration = _synthesize_dialogue(provider, segments, voice_desc, out_path, cfg.voice.model)
        else:
            # Apply a per-slide speaker if the provider supports it (e.g. Veena voices).
            if slide_voice and hasattr(provider, "set_speaker"):
                provider.set_speaker(slide_voice)
            duration = provider.synthesize(slide.narration, voice_desc, out_path)
        print(f"[PROGRESS] Audio slide {slide.n}/{total}: done ({duration:.1f}s)")

        manifest.set("speak", f"{slide.n}:{cache_key}", {
            "output": str(out_path),
            "duration": duration,
            "narration_hash": cache_key,
        })
        # Save after each slide so a killed/interrupted build (e.g. machine sleep)
        # can resume from where it left off instead of restarting from scratch.
        manifest.save()
        result.synthesized_count += 1
        result.audio_paths.append(out_path)
        result.durations.append(duration)

    manifest.save()
