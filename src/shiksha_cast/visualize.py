from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from shiksha_cast.config import ChannelConfig, ScriptFile

logger = logging.getLogger(__name__)


@dataclass
class VisualizeResult:
    chapter: str
    image_paths: list[Path] = field(default_factory=list)
    generated_count: int = 0
    cached_count: int = 0


def _get_provider(cfg: ChannelConfig):
    import importlib.util

    required = ("torch", "diffusers", "transformers")
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    if missing:
        raise ImportError(
            f"AI image generation requires: {', '.join(missing)}. "
            "Install with: pip install -e \".[imagegen]\""
        )

    from shiksha_cast.imagegen.sdxl import SDXLImageProvider
    return SDXLImageProvider(
        model_id=cfg.imagegen.model,
        num_steps=cfg.imagegen.num_steps,
    )


def generate_visuals(
    chapter: str,
    project_root: Path,
    script: ScriptFile,
    cfg: ChannelConfig,
    force: bool = False,
) -> VisualizeResult:
    from shiksha_cast.cache import BuildManifest, content_hash

    provider = _get_provider(cfg)
    build_dir = project_root / "build" / chapter
    images_dir = build_dir / "ai_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    manifest = BuildManifest(build_dir)
    result = VisualizeResult(chapter=chapter)

    for slide in script.slides:
        visual_prompt = getattr(slide, 'visual_prompt', None) or ''
        if not visual_prompt:
            result.image_paths.append(None)
            continue

        out_path = images_dir / f"visual_{slide.n:03d}.png"
        cache_key = content_hash(visual_prompt, provider.name())

        entry = manifest.get("visualize", f"{slide.n}:{cache_key}")

        if not force and entry and out_path.exists():
            result.cached_count += 1
            result.image_paths.append(out_path)
            continue

        provider.generate(visual_prompt, out_path)

        manifest.set("visualize", f"{slide.n}:{cache_key}", {
            "output": str(out_path),
            "prompt": visual_prompt,
        })
        result.generated_count += 1
        result.image_paths.append(out_path)

    manifest.save()

    # Free the image model from VRAM before the next stage (TTS) loads — on an
    # 8 GB GPU, leaving SDXL resident OOMs the Veena worker.
    if hasattr(provider, "unload"):
        provider.unload()

    return result
