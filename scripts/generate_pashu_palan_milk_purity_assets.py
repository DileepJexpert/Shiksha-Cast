from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

WIDTH = 1920
HEIGHT = 1080

SLIDES = [
    (
        "How to Check Milk Purity at Home",
        "Basic screening methods for families and dairy farmers",
        "Milk purity is not just white color. It means clean handling, natural composition and reliable testing.",
    ),
    (
        "Pure Milk Meaning",
        "Clean + Natural + Safely Handled",
        "Good milk has natural smell, normal texture, no visible dirt, and comes through hygienic process.",
    ),
    (
        "Quality Starts at Farm",
        "Clean milking decides trust",
        "Clean hands, clean udder, clean steel vessel and quick boiling or chilling protect milk quality.",
    ),
    (
        "Smell & Appearance Check",
        "First home-level clue",
        "Check natural smell, creamy white look, unusual foam, watery appearance and visible particles.",
    ),
    (
        "Sediment / Cloth Check",
        "Simple hygiene screening",
        "Filter a little milk through a clean white cloth. Dust or hair means poor handling.",
    ),
    (
        "Boiling Behaviour",
        "Freshness clue, not proof",
        "Normal milk forms cream layer. Unusual smell or sudden curdling can indicate freshness or storage issue.",
    ),
    (
        "Lactometer Basics",
        "Density check for milk",
        "A lactometer gives a density clue. Temperature affects reading, so note temperature also.",
    ),
    (
        "How to Use Lactometer",
        "Pour - settle foam - float - read",
        "Use clean cylinder, let foam settle, read at eye level and compare with a standard chart.",
    ),
    (
        "Fat and SNF",
        "Milk value depends on composition",
        "Fat gives richness. SNF means solids-not-fat: protein, lactose, minerals and natural solids.",
    ),
    (
        "Home Check vs Lab Test",
        "Screening vs proof",
        "Home checks are useful clues. Lab or certified testing is reliable proof for business decisions.",
    ),
    (
        "Buyer Checklist",
        "Practical trust points",
        "Reliable source, clean container, natural smell, no sediment, regular reading, transparent seller.",
    ),
    (
        "Recap + Next Video",
        "Smell - Filter - Boil - Lactometer - Fat/SNF - Lab",
        "Next: What are Fat and SNF, and how do they affect dairy farmer payment?",
    ),
]


def _font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/System/Library/Fonts") / name,
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_slide(index: int, title: str, subtitle: str, body: str, output_path: Path) -> None:
    title_font = _font("DejaVuSans-Bold.ttf", 78)
    subtitle_font = _font("DejaVuSans.ttf", 42)
    body_font = _font("DejaVuSans.ttf", 36)
    small_font = _font("DejaVuSans.ttf", 28)

    image = Image.new("RGB", (WIDTH, HEIGHT), (250, 246, 235))
    draw = ImageDraw.Draw(image)

    green = (33, 94, 70)
    light_green = (221, 236, 218)
    brown = (150, 90, 40)
    text = (45, 45, 45)

    draw.rectangle([0, 0, WIDTH, 130], fill=green)
    draw.rectangle([0, HEIGHT - 90, WIDTH, HEIGHT], fill=green)
    draw.text((70, 32), "Katixo Pashu Palan", font=subtitle_font, fill=(255, 255, 255))
    draw.text((1690, 35), f"S{index:02d}", font=subtitle_font, fill=(255, 255, 255))

    draw.ellipse([1350, 170, 1850, 670], fill=light_green, outline=(90, 143, 92), width=6)
    draw.ellipse([1450, 260, 1750, 560], fill=(255, 255, 255), outline=(70, 130, 90), width=6)

    # Simple steel milk can illustration.
    draw.rounded_rectangle([1420, 350, 1780, 800], radius=30, fill=(220, 223, 225), outline=(90, 90, 90), width=6)
    draw.rectangle([1490, 280, 1710, 360], fill=(205, 208, 210), outline=(90, 90, 90), width=5)
    draw.arc([1500, 190, 1700, 360], 180, 360, fill=(90, 90, 90), width=8)
    draw.rectangle([1450, 430, 1750, 700], fill=(245, 245, 245), outline=green, width=4)

    y = 210
    for line in _wrap(draw, title, title_font, 1180):
        draw.text((90, y), line, font=title_font, fill=green)
        y += 92

    y += 18
    for line in _wrap(draw, subtitle, subtitle_font, 1180):
        draw.text((95, y), line, font=subtitle_font, fill=brown)
        y += 58

    y += 35
    draw.rounded_rectangle([90, y, 1240, y + 270], radius=28, fill=(255, 255, 255), outline=(219, 203, 165), width=4)
    yy = y + 38
    for line in _wrap(draw, body, body_font, 1050):
        draw.text((130, yy), line, font=body_font, fill=text)
        yy += 52

    draw.text(
        (70, HEIGHT - 62),
        "Milk Purity Series | Educational screening only - lab test is reliable proof",
        font=small_font,
        fill=(255, 255, 255),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95, optimize=True)


def create_pdf(slide_paths: list[Path], pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=(WIDTH, HEIGHT))
    for slide_path in slide_paths:
        c.drawImage(ImageReader(str(slide_path)), 0, 0, width=WIDTH, height=HEIGHT, preserveAspectRatio=False)
        c.showPage()
    c.save()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    episode_dir = repo_root / "content" / "pashu-palan" / "milk-purity" / "s01-milk-purity-at-home"
    slides_dir = episode_dir / "slides"
    slide_paths: list[Path] = []

    for index, (title, subtitle, body) in enumerate(SLIDES, start=1):
        slide_path = slides_dir / f"slide_{index:03d}.png"
        draw_slide(index, title, subtitle, body, slide_path)
        slide_paths.append(slide_path)
        print(f"created {slide_path.relative_to(repo_root)}")

    pdf_path = episode_dir / "s01-milk-purity-at-home.pdf"
    create_pdf(slide_paths, pdf_path)
    print(f"created {pdf_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
