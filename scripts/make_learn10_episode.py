"""Generate a ~10-minute Kinnu learning compilation (English): numbers 1-10, shapes,
colors, count-again, quiz, and outro. Uses kinnu_hd (2D cutout) + props, varied
backgrounds, and the point/wave/cheer gestures (with Codex's clipping + spring fixes).

Also generates bright numeral props (1..10) into assets/cartoon/props if missing.

Writes: content/kinnu/cartoon/kinnu-learn-10min/scenes.yaml
Then render with:  cartoon-build -c kinnu-learn-10min
"""
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROPS = ROOT / "assets" / "cartoon" / "props"
EP_DIR = ROOT / "content" / "kinnu" / "cartoon" / "kinnu-learn-10min"

NUM_COLORS = [
    (235, 70, 80), (245, 160, 55), (250, 205, 60), (75, 190, 110), (70, 140, 235),
    (160, 95, 200), (235, 90, 150), (60, 195, 200), (245, 120, 70), (120, 130, 240),
]
BALLOONS = ["balloon_red", "balloon_yellow", "balloon_blue", "balloon_green",
            "balloon_orange", "balloon_purple"]


def _font(size):
    for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_numeral(n, col):
    """Bright outlined numeral on transparent bg."""
    S = 460
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = _font(360)
    txt = str(n)
    bb = d.textbbox((0, 0), txt, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    x = (S - w) / 2 - bb[0]
    y = (S - h) / 2 - bb[1]
    # dark outline
    for dx in range(-8, 9, 2):
        for dy in range(-8, 9, 2):
            d.text((x + dx, y + dy), txt, font=f, fill=(40, 36, 46, 255))
    d.text((x, y), txt, font=f, fill=col + (255,))
    im.save(PROPS / f"num_{n}.png")


def ensure_numerals():
    PROPS.mkdir(parents=True, exist_ok=True)
    for i in range(1, 11):
        if not (PROPS / f"num_{i}.png").exists():
            make_numeral(i, NUM_COLORS[i - 1])


def kinnu(pos=(0.24, 0.99), scale=0.92, facing="right"):
    return [{"id": "kinnu_hd", "pos": list(pos), "scale": scale, "facing": facing}]


def talk(text):
    return {"who": "kinnu_hd", "do": "talk", "text": text}


def gest(do, **kw):
    a = {"who": "kinnu_hd", "do": do, "start": 0.2, "end": kw.pop("end", 30.0)}
    a.update(kw)
    return a


def scene(sid, bg, chars, actions, props=None, cam=None):
    s = {"id": sid, "background": bg, "transition": {"in": 0.3, "out": 0.3},
         "characters": chars, "actions": actions}
    if props:
        s["props"] = props
    if cam:
        s["camera"] = cam
    return s


def count_balloons(n, y=0.24):
    """Place up to 6 balloons spread across the top to visualize a small count."""
    k = min(n, 6)
    props = []
    xs = [0.42 + 0.085 * i for i in range(k)]
    for i, x in enumerate(xs):
        props.append({"asset": f"{BALLOONS[i % len(BALLOONS)]}.png",
                      "pos": [round(x, 3), y], "scale": 0.15, "anim": "float",
                      "start": round(0.3 + i * 0.12, 2)})
    return props


def build():
    ensure_numerals()
    S = []
    n = 0

    def nid():
        nonlocal n
        n += 1
        return f"s{n:02d}"

    # --- Intro ---
    S.append(scene(nid(), "garden.png", kinnu((0.30, 0.99), 0.95),
                   [gest("wave", end=5.0),
                    talk("Hello friends! I am Kinnu. Welcome back to our learning corner!"),
                    talk("Today we will learn numbers, shapes, and colors together. Are you ready?")],
                   cam={"zoom": [1.0, 1.05]}))
    S.append(scene(nid(), "garden.png", kinnu((0.28, 0.99), 0.95),
                   [gest("cheer", end=3.0),
                    talk("Let us begin! Clap your hands and learn with Kinnu. Here we go!")]))

    # --- Numbers 1 to 10 ---
    word = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    for i in range(1, 11):
        seq = ", ".join(word[:i])
        props = [{"asset": f"num_{i}.png", "pos": [0.70, 0.40], "scale": 0.34,
                  "anim": "pop", "start": 0.3}] + count_balloons(i)
        S.append(scene(nid(), "playground.png", kinnu((0.22, 0.99), 0.92),
                       [gest("point", side="right"),
                        talk(f"This is number {word[i-1]}."),
                        talk(f"Let us count with Kinnu: {seq}."),
                        talk(f"{word[i-1].capitalize()}! Can you say {word[i-1]}?")],
                       props=props))

    # --- Count again together ---
    S.append(scene(nid(), "night_sky.png", kinnu((0.24, 0.99), 0.92),
                   [gest("point_up"),
                    talk("Now let us count all the way from one to ten, faster!"),
                    talk("One, two, three, four, five, six, seven, eight, nine, ten!"),
                    talk("Wonderful counting, my friends!")]))
    S.append(scene(nid(), "night_sky.png", kinnu((0.24, 0.99), 0.92),
                   [gest("cheer", end=3.0),
                    talk("One more time! One, two, three, four, five. Six, seven, eight, nine, ten!")]))

    # --- Shapes ---
    shapes = [("circle", "A circle is round like a ball."),
              ("square", "A square has four equal sides."),
              ("triangle", "A triangle has three sides. One, two, three."),
              ("rectangle", "A rectangle looks like a long box, like a door or a book.")]
    for name, fact in shapes:
        S.append(scene(nid(), "classroom.png", kinnu((0.24, 0.99), 0.92),
                       [gest("point", side="right"),
                        talk(f"This is a {name}."),
                        talk(fact),
                        talk(f"Say it with Kinnu: {name}.")],
                       props=[{"asset": f"shape_{name}.png", "pos": [0.70, 0.45],
                               "scale": 0.40 if name == "rectangle" else 0.36,
                               "anim": "pop", "start": 0.3}]))

    # --- Colors ---
    colors = [("red", "An apple can be red."), ("yellow", "The sun can be yellow."),
              ("blue", "The sky can be blue."), ("green", "Leaves can be green."),
              ("orange", "An orange fruit is orange."), ("purple", "Grapes can be purple.")]
    for name, fact in colors:
        S.append(scene(nid(), "playground.png", kinnu((0.24, 0.99), 0.92),
                       [gest("point", side="right"),
                        talk(f"This balloon is {name}. {fact}"),
                        talk(f"Say it with Kinnu: {name}.")],
                       props=[{"asset": f"balloon_{name}.png", "pos": [0.68, 0.42],
                               "scale": 0.40, "anim": "float", "start": 0.3}]))

    # --- Quiz / your turn ---
    S.append(scene(nid(), "classroom.png", kinnu((0.22, 0.99), 0.92),
                   [gest("point", side="right"),
                    talk("Now it is your turn! Look at the screen."),
                    talk("Which shape is a triangle? Point to it and tell Kinnu!"),
                    talk("Pause the video and say your answer out loud.")],
                   props=[{"asset": "shape_square.png", "pos": [0.52, 0.40], "scale": 0.22, "anim": "pop", "start": 0.3},
                          {"asset": "shape_triangle.png", "pos": [0.70, 0.40], "scale": 0.22, "anim": "pop", "start": 0.5},
                          {"asset": "shape_circle.png", "pos": [0.88, 0.40], "scale": 0.22, "anim": "pop", "start": 0.7}]))
    S.append(scene(nid(), "playground.png", kinnu((0.22, 0.99), 0.92),
                   [gest("point", side="right"),
                    talk("Here is one more! How many balloons can you count?"),
                    talk("Count them with Kinnu: one, two, three, four!"),
                    talk("Did you get four? Great job!")],
                   props=count_balloons(4, y=0.34)))

    # --- Outro ---
    S.append(scene(nid(), "garden.png", kinnu((0.28, 0.99), 0.95),
                   [gest("cheer", end=3.0),
                    talk("Hooray! Today we learned our numbers, shapes, and colors."),
                    talk("You did such a great job, my friends!")],
                   cam={"zoom": [1.05, 1.0]}))
    S.append(scene(nid(), "garden.png", kinnu((0.30, 0.99), 0.95),
                   [gest("wave", end=5.0),
                    talk("See you again soon with Kinnu. Please like and subscribe."),
                    talk("Bye bye! A Katixo channel.")],
                   cam={"zoom": [1.0, 1.04]}))

    spec = {"episode": "kinnu-learn-10min",
            "title": "Kinnu's Big Learning Video - Numbers, Shapes & Colors for Kids | Katixo",
            "fps": 30, "cast": {"kinnu_hd": "af_heart"}, "scenes": S}
    EP_DIR.mkdir(parents=True, exist_ok=True)
    out = EP_DIR / "scenes.yaml"
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=200)
    print(f"wrote {out} with {len(S)} scenes")


if __name__ == "__main__":
    build()
