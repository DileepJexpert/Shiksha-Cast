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
    # Per-slide motion for `ai-build`: "kenburns" (ffmpeg zoom/pan),
    # "parallax" (DepthFlow 2.5D depth animation), or "static".
    # None => derive from the legacy `kenburns` flag.
    motion: Optional[str] = None
    # Override the DepthFlow render command; placeholders:
    # {image} {output} {duration} {fps} {width} {height}. None => built-in default.
    parallax_command: Optional[str] = None

    def effective_motion(self) -> str:
        if self.motion:
            return self.motion.lower()
        return "kenburns" if self.kenburns else "static"


class GeneratorConfig(BaseModel):
    """Local script generation (topic -> script.yaml) via an LLM."""
    provider: str = "ollama"
    model: str = "llama3.1:latest"
    url: str = "http://localhost:11434"
    slides: int = 14


class ChannelConfig(BaseModel):
    channel: str = "Katixo Shiksha"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    imagegen: ImageGenConfig = Field(default_factory=ImageGenConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)


class SlideScript(BaseModel):
    n: int
    narration: str = ""
    visual_prompt: Optional[str] = None
    voice_description: Optional[str] = None
    voice: Optional[str] = None  # per-slide speaker (e.g. Veena "kavya"); overrides global
    min_slide_s: Optional[float] = None
    motion: Optional[str] = None  # per-slide ai-build motion: parallax|kenburns|static; overrides global


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


def _is_episode_dir(d: Path) -> bool:
    """An episode dir is any folder that contains a script YAML."""
    return d.is_dir() and bool(list(d.glob("*.yaml")))


def iter_episode_dirs(project_root: Path) -> list[Path]:
    """Every episode directory under content/, however deeply nested.

    Episodes may live inside category folders (e.g.
    content/how-it-works/technology/s02-wifi). Category folders themselves
    have no script YAML, so they are skipped. Names starting with '.' or '_'
    (e.g. _archive) are ignored at any level.
    """
    content_root = project_root / "content"
    if not content_root.is_dir():
        return []
    found: list[Path] = []
    for d in sorted(content_root.rglob("*")):
        if not d.is_dir():
            continue
        if any(part.startswith((".", "_")) for part in d.relative_to(content_root).parts):
            continue
        if _is_episode_dir(d):
            found.append(d)
    return found


def find_chapter_dir(project_root: Path, chapter: str) -> Path:
    """Locate an episode directory by name, anywhere under content/.

    Tries the flat layout (content/<chapter>) first for speed and backward
    compatibility, then searches category subfolders recursively.
    """
    content_root = project_root / "content"
    flat = content_root / chapter
    if flat.is_dir():
        return flat
    if content_root.is_dir():
        matches = [d for d in content_root.rglob(chapter) if d.is_dir() and d.name == chapter]
        scripted = [d for d in matches if list(d.glob("*.yaml"))]
        chosen = scripted or matches
        if len(chosen) == 1:
            return chosen[0]
        if len(chosen) > 1:
            joined = ", ".join(str(d.relative_to(project_root)) for d in chosen)
            raise FileNotFoundError(f"Ambiguous chapter '{chapter}'; multiple matches: {joined}")
    raise FileNotFoundError(f"Chapter directory not found: {chapter} (searched under {content_root})")


def resolve_chapter(project_root: Path, chapter: str) -> tuple[Path, Path]:
    """Return (chapter_dir, pdf_path) for a chapter name like 'ch03'."""
    chapter_dir = find_chapter_dir(project_root, chapter)
    pdf_path = find_pdf(chapter_dir)
    return chapter_dir, pdf_path
