from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

from shiksha_cast.cache import BuildManifest, file_hash


@dataclass
class RenderResult:
    chapter: str
    slide_paths: list[Path] = field(default_factory=list)
    pdf_hash: str = ""
    rendered_count: int = 0
    cached_count: int = 0


def _render_page(page: pdfium.PdfPage, target_w: int, target_h: int) -> Image.Image:
    page_w = page.get_width()
    page_h = page.get_height()
    scale = min(target_w / page_w, target_h / page_h)
    bitmap = page.render(scale=scale)
    img = bitmap.to_pil()
    if img.size == (target_w, target_h):
        return img
    canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    x = (target_w - img.width) // 2
    y = (target_h - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def render_chapter(
    chapter: str,
    project_root: Path,
    width: int = 1920,
    height: int = 1080,
    force: bool = False,
) -> RenderResult:
    from shiksha_cast.config import resolve_chapter

    chapter_dir, pdf_path = resolve_chapter(project_root, chapter)
    pdf_h = file_hash(pdf_path)

    build_dir = project_root / "build" / chapter
    slides_dir = build_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    manifest = BuildManifest(build_dir)
    result = RenderResult(chapter=chapter, pdf_hash=pdf_h)

    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        for i in range(len(doc)):
            out_path = slides_dir / f"slide_{i + 1:03d}.png"
            cache_key = f"{i + 1}:{pdf_h}:{width}x{height}"
            entry = manifest.get("render", cache_key)

            if not force and entry and out_path.exists():
                result.cached_count += 1
                result.slide_paths.append(out_path)
                continue

            page = doc[i]
            img = _render_page(page, width, height)
            img.save(out_path)
            page.close()

            manifest.set("render", cache_key, {"output": str(out_path), "pdf_hash": pdf_h})
            result.rendered_count += 1
            result.slide_paths.append(out_path)
    finally:
        doc.close()

    manifest.save()
    return result
