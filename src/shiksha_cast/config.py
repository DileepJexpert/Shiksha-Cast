from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class VoiceConfig(BaseModel):
    provider: str = "parler"
    model: str = "ai4bharat/indic-parler-tts"
    description: str = ""
    sample_rate: int = 44100


class TimingConfig(BaseModel):
    pad_before_ms: int = 300
    pad_after_ms: int = 700
    min_slide_s: float = 4


class MusicConfig(BaseModel):
    bed: Optional[str] = None
    duck_db: int = -18


class BrandingConfig(BaseModel):
    intro: Optional[str] = None
    outro: Optional[str] = None
    mascot_overlay: Optional[str] = None


class ImageGenConfig(BaseModel):
    provider: str = "sdxl"
    model: str = "stabilityai/sdxl-turbo"
    num_steps: int = 4
    kenburns: bool = True


class ChannelConfig(BaseModel):
    channel: str = "Katixo Shiksha"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    imagegen: ImageGenConfig = Field(default_factory=ImageGenConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)
    branding: BrandingConfig = Field(default_factory=BrandingConfig)


class SlideScript(BaseModel):
    n: int
    narration: str = ""
    visual_prompt: Optional[str] = None
    voice_description: Optional[str] = None
    voice: Optional[str] = None  # per-slide speaker (e.g. Veena "kavya"); overrides global
    min_slide_s: Optional[float] = None


class ScriptFile(BaseModel):
    chapter: str
    slides: list[SlideScript]


def load_channel_config(project_root: Path) -> ChannelConfig:
    path = project_root / "config" / "channel.yaml"
    if not path.exists():
        return ChannelConfig()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return ChannelConfig.model_validate(data)


def find_script_yaml(chapter_dir: Path) -> Path:
    """Find script YAML: prefer script.yaml, then {dirname}.yaml, then any .yaml."""
    canonical = chapter_dir / "script.yaml"
    if canonical.exists():
        return canonical
    named = chapter_dir / f"{chapter_dir.name}.yaml"
    if named.exists():
        return named
    yamls = list(chapter_dir.glob("*.yaml"))
    if not yamls:
        raise FileNotFoundError(f"No script YAML found in {chapter_dir}")
    return yamls[0]


def load_script(chapter_dir: Path) -> ScriptFile:
    script_path = find_script_yaml(chapter_dir)
    with open(script_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ScriptFile.model_validate(data)


def find_pdf(chapter_dir: Path) -> Path:
    pdfs = list(chapter_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF found in {chapter_dir}")
    if len(pdfs) > 1:
        pdfs = [p for p in pdfs if p.stem == chapter_dir.name]
    return pdfs[0]


def resolve_chapter(project_root: Path, chapter: str) -> tuple[Path, Path]:
    """Return (chapter_dir, pdf_path) for a chapter name like 'ch03'."""
    chapter_dir = project_root / "content" / chapter
    if not chapter_dir.is_dir():
        raise FileNotFoundError(f"Chapter directory not found: {chapter_dir}")
    pdf_path = find_pdf(chapter_dir)
    return chapter_dir, pdf_path
