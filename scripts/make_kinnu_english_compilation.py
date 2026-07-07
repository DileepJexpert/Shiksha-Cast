"""Build one 5-minute-ish Kinnu English compilation from lesson slides.

This script reuses the rendered green-board PNGs from ke01-ke10 and creates:
  content/kids-english/ke00-grammar-starter-5min/script.yaml
  content/kids-english/ke00-grammar-starter-5min/UPLOAD_METADATA.md
  build/ke00-grammar-starter-5min/slides/slide_001.png ...

Run the slide deck renderer first:
  python scripts/make_english_board_slides.py --all
"""

from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont


EPISODE_ID = "ke00-grammar-starter-5min"
CONTENT_DIR = Path("content/kids-english") / EPISODE_ID
BUILD_SLIDES_DIR = Path("build") / EPISODE_ID / "slides"

# Seven slides per lesson keeps the result close to five minutes with the
# channel min_slide_s=4 timing, while still covering rule, examples, quiz,
# reading practice, and recap.
SELECTED_SLIDES = [1, 2, 3, 4, 5, 7, 8]
W, H = 1920, 1080
BOARD = (24, 95, 67)
CHALK = (246, 250, 238)
FONTS = Path("C:/Windows/Fonts")

LESSONS = [
    (
        "ke01-a-or-an",
        "A or An",
        [
            "Lesson one: a or an.",
            "Use a before a consonant sound.",
            "Use an before a vowel sound.",
            "Say: a ball, a cat, an apple, an egg.",
            "Your turn: an apple.",
            "Read aloud: I see a cat. I eat an apple.",
            "Remember: say the word aloud, then choose a or an.",
        ],
    ),
    (
        "ke02-this-that",
        "This or That",
        [
            "Lesson two: this or that.",
            "Use this for something near you.",
            "Use that for something far from you.",
            "Say: this book, that kite.",
            "Your turn: this pencil.",
            "Read aloud: This is my bag. That is a tree.",
            "Remember: this is near, that is far.",
        ],
    ),
    (
        "ke03-am-is-are",
        "Am, Is, Are",
        [
            "Lesson three: am, is, are.",
            "Use am with I.",
            "Use is with one person or one thing.",
            "Use are with you, we, and they.",
            "Your turn: I am happy.",
            "Read aloud: She is kind. They are friends.",
            "Remember: I am, he is, they are.",
        ],
    ),
    (
        "ke04-he-she-it",
        "He, She, It",
        [
            "Lesson four: he, she, it.",
            "Use he for a boy or man.",
            "Use she for a girl or woman.",
            "Use it for an animal, place, or thing.",
            "Your turn: she is my sister.",
            "Read aloud: He runs. She sings. It jumps.",
            "Remember: choose the word that matches the noun.",
        ],
    ),
    (
        "ke05-i-you-we-they",
        "I, You, We, They",
        [
            "Lesson five: I, you, we, they.",
            "Use I when you talk about yourself.",
            "Use you when you talk to someone.",
            "Use we for a group with you inside it.",
            "Your turn: we are students.",
            "Read aloud: I read. You write. They play.",
            "Remember: pronouns make sentences short and clear.",
        ],
    ),
    (
        "ke06-has-have",
        "Has or Have",
        [
            "Lesson six: has or have.",
            "Use has with he, she, and it.",
            "Use have with I, you, we, and they.",
            "Say: she has a doll. They have books.",
            "Your turn: he has a kite.",
            "Read aloud: I have a pencil. It has wheels.",
            "Remember: one friend has, many friends have.",
        ],
    ),
    (
        "ke07-do-does",
        "Do or Does",
        [
            "Lesson seven: do or does.",
            "Use do with I, you, we, and they.",
            "Use does with he, she, and it.",
            "Say: do you read? Does she sing?",
            "Your turn: does he play?",
            "Read aloud: Do they jump? Does it work?",
            "Remember: does goes with he, she, and it.",
        ],
    ),
    (
        "ke08-was-were",
        "Was or Were",
        [
            "Lesson eight: was or were.",
            "Use was for one person or thing in the past.",
            "Use were for many people or things in the past.",
            "Say: I was tired. We were happy.",
            "Your turn: she was late.",
            "Read aloud: The birds were loud. It was sunny.",
            "Remember: was and were tell about the past.",
        ],
    ),
    (
        "ke09-can-cannot",
        "Can or Cannot",
        [
            "Lesson nine: can and cannot.",
            "Use can for something possible.",
            "Use cannot for something not possible.",
            "Say: I can swim. I cannot fly.",
            "Your turn: birds can fly.",
            "Read aloud: We can help. A fish cannot walk.",
            "Remember: can means able to do it.",
        ],
    ),
    (
        "ke10-there-is-there-are",
        "There Is or There Are",
        [
            "Lesson ten: there is, there are.",
            "Use there is for one thing.",
            "Use there are for many things.",
            "Say: there is one apple. There are three apples.",
            "Your turn: there are five stars.",
            "Read aloud: There is a book. There are two pencils.",
            "Remember: one uses is, many uses are.",
        ],
    ),
]

FINAL_REVIEW = [
    (
        "ke01-a-or-an",
        8,
        "Final review: not a apple, say an apple.",
        "Final Review",
    ),
    (
        "ke03-am-is-are",
        8,
        "Final review: I am, he is, they are.",
        "Final Review",
    ),
    (
        "ke06-has-have",
        8,
        "Final review: she has, they have.",
        "Final Review",
    ),
    (
        "ke09-can-cannot",
        8,
        "Final review: can means able; cannot means not able.",
        "Final Review",
    ),
    (
        "ke10-there-is-there-are",
        8,
        "Great job. One uses there is; many uses there are.",
        "Final Review",
    ),
]

TOTAL_SLIDES = len(LESSONS) * len(SELECTED_SLIDES) + len(FINAL_REVIEW)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeuib.ttf", "arialbd.ttf", "comicbd.ttf"):
        path = FONTS / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    return ImageFont.load_default()


def _copy_slide_with_compilation_badge(src: Path, dst: Path, slide_no: int) -> None:
    img = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(img)
    label = f"{slide_no:02d}/{TOTAL_SLIDES:02d}"
    fnt = _font(30)

    # Hide the source lesson badge, such as 03/08, and replace it with the
    # compilation badge so the combined video does not look like repeated decks.
    draw.rounded_rectangle([1640, 108, 1788, 156], radius=14, fill=BOARD)
    x = 1714 - draw.textlength(label, font=fnt) / 2
    draw.text((x + 2, 120 + 2), label, font=fnt, fill=(0, 0, 0))
    draw.text((x, 120), label, font=fnt, fill=CHALK)
    img.save(dst, quality=95)


def _clean_build_slides() -> None:
    BUILD_SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    for old in BUILD_SLIDES_DIR.glob("slide_*.png"):
        old.unlink()


def _copy_slides() -> list[dict[str, object]]:
    slides: list[dict[str, object]] = []
    slide_no = 1

    for lesson_id, lesson_title, narrations in LESSONS:
        if len(narrations) != len(SELECTED_SLIDES):
            raise ValueError(f"{lesson_id} has {len(narrations)} narrations, expected {len(SELECTED_SLIDES)}")

        source_dir = Path("content/kids-english") / lesson_id / "slides"
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Rendered slides missing: {source_dir}")

        for source_no, narration in zip(SELECTED_SLIDES, narrations):
            src = source_dir / f"slide_{source_no:03d}.png"
            if not src.exists():
                raise FileNotFoundError(src)
            dst = BUILD_SLIDES_DIR / f"slide_{slide_no:03d}.png"
            _copy_slide_with_compilation_badge(src, dst, slide_no)
            slides.append(
                {
                    "n": slide_no,
                    "narration": narration,
                    "voice": "af_heart",
                    "source_lesson": lesson_id,
                    "source_slide": source_no,
                    "section": lesson_title,
                }
            )
            slide_no += 1

    for lesson_id, source_no, narration, section in FINAL_REVIEW:
        source_dir = Path("content/kids-english") / lesson_id / "slides"
        src = source_dir / f"slide_{source_no:03d}.png"
        if not src.exists():
            raise FileNotFoundError(src)
        dst = BUILD_SLIDES_DIR / f"slide_{slide_no:03d}.png"
        _copy_slide_with_compilation_badge(src, dst, slide_no)
        slides.append(
            {
                "n": slide_no,
                "narration": narration,
                "voice": "af_heart",
                "source_lesson": lesson_id,
                "source_slide": source_no,
                "section": section,
            }
        )
        slide_no += 1

    return slides


def _write_script(slides: list[dict[str, object]]) -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure run_build uses the copied PNGs, not a stale PDF.
    for pdf in CONTENT_DIR.glob("*.pdf"):
        pdf.unlink()

    data = {
        "chapter": "Kinnu English Grammar Starter - 10 Rules in 5 Minutes",
        "brand": "Kinnu English",
        "template": "compiled_uploaded_slides",
        "slides": slides,
    }
    (CONTENT_DIR / "script.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _write_metadata() -> None:
    text = """# Upload Metadata

## Title
10 English Grammar Rules for Kids | Kinnu English Class | A/An, This/That, Am/Is/Are

## Description
Learn 10 small English grammar rules with Kinnu in a friendly green-board class.

In this 5-minute starter lesson, kids practise:
- A or An
- This or That
- Am, Is, Are
- He, She, It
- I, You, We, They
- Has or Have
- Do or Does
- Was or Were
- Can or Cannot
- There is / There are

Best for young learners, beginners, and daily English practice at home.

## Tags
kids english, english for kids, grammar for kids, a or an, this that, am is are, has have, do does, was were, can cannot, there is there are, english lesson, primary english, kinnu english, learn english kids

## Category
Education

## Audience
Kids, beginners, primary school learners
"""
    (CONTENT_DIR / "UPLOAD_METADATA.md").write_text(text, encoding="utf-8")


def main() -> None:
    _clean_build_slides()
    slides = _copy_slides()
    _write_script(slides)
    _write_metadata()
    print(f"{EPISODE_ID}: copied {len(slides)} slides to {BUILD_SLIDES_DIR}")
    print(f"{EPISODE_ID}: script -> {CONTENT_DIR / 'script.yaml'}")


if __name__ == "__main__":
    main()
