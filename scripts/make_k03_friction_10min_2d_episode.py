"""Generate a long 2D Kinnu cartoon episode about friction.

The output is a scenes.yaml consumed by:

  python -m shiksha_cast cartoon-build -c k03-friction-10min-2d

It uses the HD Kinnu cutout rig and the character-free K03 friction backgrounds.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAR = "kinnu_hd"
OUT = ROOT / "content" / "kinnu" / "cartoon" / "k03-friction-10min-2d" / "scenes.yaml"
BG = "build/k03-friction/backgrounds/bg_{:03d}.png"


def esc(text: str) -> str:
    return text.replace('"', "'")


class Builder:
    def __init__(self) -> None:
        self.scenes: list[str] = []

    def scene(
        self,
        bg: str,
        talks: list[str],
        *,
        gesture: tuple[str, str | None, float] | None = None,
        move: dict | None = None,
        pos: tuple[float, float] = (0.22, 0.99),
        scale: float = 0.88,
        zoom: tuple[float, float] | None = None,
        facing: str = "right",
    ) -> None:
        sid = f"s{len(self.scenes) + 1:02d}"
        lines = [
            f"  - id: {sid}",
            f"    background: {bg}",
            "    transition: { in: 0.25, out: 0.25 }",
        ]
        if zoom:
            lines.append(f"    camera: {{ zoom: [{zoom[0]}, {zoom[1]}] }}")
        lines.append(
            f"    characters: [{{ id: {CHAR}, pos: [{pos[0]}, {pos[1]}], "
            f"scale: {scale}, facing: {facing} }}]"
        )
        lines.append("    actions:")
        if move:
            bits = [f"who: {CHAR}", f"do: {move['do']}"]
            if "to" in move:
                bits.append(f"to: {move['to']}")
            if "from" in move:
                bits.append(f"from: {move['from']}")
            bits.append(f"start: {move.get('start', 0.0)}")
            bits.append(f"end: {move.get('end', 2.0)}")
            lines.append(f"      - {{ {', '.join(bits)} }}")
        if gesture:
            do, side, end = gesture
            bits = [f"who: {CHAR}", f"do: {do}"]
            if side:
                bits.append(f"side: {side}")
            bits.extend(["start: 0.0", f"end: {end}"])
            lines.append(f"      - {{ {', '.join(bits)} }}")
        for talk in talks:
            lines.append(f'      - {{ who: {CHAR}, do: talk, text: "{esc(talk)}" }}')
        self.scenes.append("\n".join(lines))

    def yaml(self) -> str:
        head = (
            "episode: k03-friction-10min-2d\n"
            "title: Kinnu Learns Friction - Why We Slip, Grip, and Stop\n"
            "fps: 15\n"
            "cast:\n"
            f"  {CHAR}: af_heart\n"
            "scenes:\n"
        )
        return head + "\n\n".join(self.scenes) + "\n"


b = Builder()

sections = [
    (
        BG.format(1),
        ("wave", None, 2.5),
        {"do": "walkto", "to": 0.30, "start": 0.2, "end": 2.4},
        [
            "Hello friends, I am Kinnu, and today something funny happened in our science classroom.",
            "I stepped on a shiny wet floor, my feet slid forward, and I shouted, Oops, why am I slipping?",
            "That funny slip is the perfect way to learn a powerful science word: friction.",
            "Friction is invisible, but it helps us walk, stop, hold things, write, ride, and play safely.",
            "In this full episode, we will test smooth floors, rough floors, shoes, tyres, heat, and a few brainy quizzes.",
            "Stay with me till the end, because you will become a friction detective in your own home.",
        ],
    ),
    (
        BG.format(2),
        ("point", "right", 3.5),
        {"do": "run", "to": 0.58, "start": 0.0, "end": 2.0},
        [
            "First, look carefully at this smooth wet floor. It looks shiny, but it can be tricky.",
            "When my shoe touches this floor, there is not much grip between the shoe and the tile.",
            "Less grip means less friction, and with less friction my foot can slide instead of stopping.",
            "That is why wet bathroom floors, polished tiles, and ice can feel slippery under our feet.",
            "Slipping is not magic. It is just a sign that friction has become too small to hold us.",
            "Whenever you see a wet floor sign, walk slowly, because your shoes need time to grip.",
        ],
    ),
    (
        BG.format(3),
        ("point", "right", 4.0),
        {"do": "walkto", "to": 0.42, "start": 0.0, "end": 2.4},
        [
            "Now let us compare two surfaces, one smooth and one rough, like a real science experiment.",
            "A smooth surface has tiny bumps too, but the bumps are very small and easy to slide over.",
            "A rough surface has bigger tiny bumps, and those bumps catch, rub, and slow things down.",
            "More rubbing means more friction. Less rubbing means less friction. That is the key idea.",
            "Imagine sliding your palm on glass, then on a rough doormat. The doormat pulls your hand back more.",
            "That pull-back feeling is friction working between your hand and the surface.",
        ],
    ),
    (
        BG.format(4),
        ("point", "right", 4.0),
        {"do": "walkto", "to": 0.50, "start": 0.0, "end": 2.2},
        [
            "Let us test a toy car. I push it on smooth tile, and it rolls for a long distance.",
            "The wheels still touch the floor, but the friction is small, so the car keeps moving longer.",
            "Now I push the same toy car on carpet. It slows down quickly and stops much earlier.",
            "The carpet has many soft rough fibers. Those fibers push against the wheels and create more friction.",
            "This is why the same push can give different results on different surfaces.",
            "Science detective rule number one: always ask, what surfaces are touching each other?",
        ],
    ),
    (
        BG.format(5),
        ("cheer", None, 2.4),
        None,
        [
            "Friction is not only about stopping toys. Friction helps us walk without falling.",
            "Look at the bottom of shoes. You will see lines, grooves, dots, or rough patterns.",
            "Those patterns dig gently into the ground and give our feet grip with every step.",
            "Sports shoes, school shoes, and sandals all use friction to help us stand and move safely.",
            "Car tyres also have grooves. The grooves push water away and help the tyre touch the road better.",
            "When tyres become too smooth, they lose grip, and that can be dangerous on wet roads.",
        ],
    ),
    (
        BG.format(6),
        ("point", "right", 4.0),
        {"do": "walkto", "to": 0.60, "start": 0.0, "end": 2.2},
        [
            "Now try a tiny experiment with your hands. Rub your palms together quickly for five seconds.",
            "One, two, three, four, five. Stop. Do your palms feel warmer now?",
            "That warmth came because friction changed some movement energy into heat.",
            "This is why sliding down a rope too fast can burn your hand, and why brakes can become hot.",
            "Friction can warm things up. Sometimes that is useful, and sometimes we need to control it.",
            "Machines use oil or grease to reduce friction, so parts do not get too hot or wear out fast.",
        ],
    ),
    (
        BG.format(7),
        ("point", "right", 4.5),
        None,
        [
            "Let us play a quick quiz. Which has more friction, ice or sandpaper?",
            "Think for a moment. Ice is smooth and slippery, so it has less friction.",
            "Sandpaper is rough, scratchy, and full of tiny bumps, so it has more friction.",
            "Next question: why can we write with a pencil on paper?",
            "The paper rubs against the pencil tip. Friction pulls tiny pencil particles onto the paper.",
            "Without friction, the pencil would slide around and writing would be almost impossible.",
        ],
    ),
    (
        BG.format(8),
        ("cheer", None, 2.8),
        {"do": "run", "to": 0.72, "start": 0.0, "end": 1.8},
        [
            "Friction can be our friend. It helps shoes grip, pencils write, brakes stop, and hands hold.",
            "But friction can also slow bicycles, make machines hot, and wear down moving parts.",
            "So engineers do not simply say friction is good or bad. They ask how much friction is needed.",
            "For walking, we want more grip. For sliding on a playground slide, we want less grip.",
            "For car brakes, we want strong friction. For engine parts, we use oil to reduce friction.",
            "Smart science means choosing the right amount of friction for the job.",
        ],
    ),
]

for repeat in range(6):
    for bg, gesture, move, lines in sections:
        # Repeating with small variations gives the long-form practice style kids
        # channels use: learn, repeat, quiz, recap, then apply again.
        if repeat == 0:
            talks = lines[:2]
        elif repeat == 1:
            talks = lines[2:4]
        elif repeat == 2:
            talks = lines[4:6]
        elif repeat == 3:
            talks = [
                f"Practice round: {lines[0]}",
                f"Say it with me: {lines[1]}",
            ]
        else:
            talks = [
                f"Quick recap: {lines[2]}",
                f"Remember this: {lines[3]}",
            ]
        b.scene(bg, talks, gesture=gesture, move=move, zoom=(1.0, 1.04))

b.scene(
    BG.format(1),
    [
        "Fantastic work, science explorer. Today you learned that friction is the grip between touching surfaces.",
        "Less friction can make things slide. More friction can help things stop, hold, and stay safe.",
        "Look around your room today and find three places where friction is helping you.",
        "Like and subscribe for more learning with Kinnu. Bye bye, and keep exploring science!",
    ],
    gesture=("wave", None, 3.0),
    pos=(0.28, 0.99),
    zoom=(1.04, 1.0),
)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(b.yaml(), encoding="utf-8")
print(f"wrote {OUT} ({len(b.scenes)} scenes, char={CHAR}, fps=15)")
