"""Generate a FULL ~10-minute 'Count 1 to 10' episode scenes.yaml for Kinnu.

Duration is driven by narration length (talk lines auto-chain to audio), so this
builds many scenes with repetition, counting rounds, a sing-along, count-backwards
and a recap to reach ~10 minutes. Re-run to regenerate; edit the SECTIONS below to
tune content. Character id is a parameter so it works for kinnu_hd or a future
Indian-art rig that replaces it.

Usage: python scripts/make_count10_episode.py [char_id]   (default kinnu_hd)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAR = sys.argv[1] if len(sys.argv) > 1 else "kinnu_hd"
OUT = ROOT / "content" / "kinnu" / "cartoon" / "kinnu-count-10min" / "scenes.yaml"

STAR_BG = "build/k02-star-bridge-counting/backgrounds/bg_{:03d}.png"
NUM = ["zero", "one", "two", "three", "four", "five",
       "six", "seven", "eight", "nine", "ten"]


def esc(t):
    return t.replace('"', "'")


class Builder:
    def __init__(self):
        self.scenes = []
        self.n = 0

    def scene(self, bg, talks, *, gesture=None, zoom=None, trans_in=0.4, trans_out=0.4,
              props=None, pos=(0.24, 0.99), scale=0.9):
        self.n += 1
        sid = f"s{self.n:02d}"
        lines = [f"  - id: {sid}", f"    background: {bg}"]
        t = []
        if trans_in:
            t.append(f"in: {trans_in}")
        if trans_out:
            t.append(f"out: {trans_out}")
        if t:
            lines.append(f"    transition: {{ {', '.join(t)} }}")
        if zoom:
            lines.append(f"    camera: {{ zoom: [{zoom[0]}, {zoom[1]}] }}")
        lines.append(f"    characters: [{{ id: {CHAR}, pos: [{pos[0]}, {pos[1]}], "
                     f"scale: {scale}, facing: right }}]")
        if props:
            lines.append("    props:")
            for pr in props:
                lines.append(
                    f"      - {{ asset: {pr['asset']}, pos: [{pr['pos'][0]:.3f}, {pr['pos'][1]:.3f}], "
                    f"scale: {pr.get('scale', 0.09)}, anim: {pr.get('anim', 'bob')}, z: front, "
                    f"start: {pr.get('start', 0.0)} }}")
        lines.append("    actions:")
        if gesture:
            g = gesture
            lines.append(f"      - {{ who: {CHAR}, do: {g[0]}, "
                         + (f"side: {g[1]}, " if len(g) > 1 and g[1] else "")
                         + f"start: 0.0, end: {g[2] if len(g) > 2 else 3.0} }}")
        for tk in talks:
            lines.append(f'      - {{ who: {CHAR}, do: talk, text: "{esc(tk)}" }}')
        self.scenes.append("\n".join(lines))

    def yaml(self):
        head = (f"episode: kinnu-count-10min\n"
                f"title: Kinnu's Big Counting Adventure - Count 1 to 10 (Full Episode)\n"
                f"fps: 30\ncast:\n  {CHAR}: af_heart\nscenes:\n")
        return head + "\n\n".join(self.scenes) + "\n"


def apples(count):
    xs = [0.42 + 0.11 * i for i in range(count)]
    return [{"asset": "apple.png", "pos": (min(x, 0.96), 0.55 + 0.04 * (i % 2)),
             "scale": 0.07, "anim": "bob", "start": 0.3 * i} for i, x in enumerate(xs)]


def stars(count):
    xs = [0.40 + 0.12 * (i % 5) for i in range(count)]
    ys = [0.30 if i < 5 else 0.50 for i in range(count)]
    return [{"asset": "star.png", "pos": (xs[i], ys[i]), "scale": 0.06,
             "anim": "spin", "start": 0.25 * i} for i in range(count)]


b = Builder()

# --- 1. Intro ---
b.scene("classroom.png", [
    "Hello friends! I am Kinnu! Welcome back to our learning corner.",
    "Are you ready to learn and have lots and lots of fun today?",
], gesture=("wave", None, 3.2), zoom=(1.0, 1.05), trans_out=0.4)
b.scene("classroom.png", [
    "Today we are going to count all the way from one to ten.",
    "Counting is so much fun, and you can count along with me!",
], gesture=("point", "right", 3.0))
b.scene("classroom.png", [
    "First, let's stretch our hands up high, and get our voices ready.",
    "Take a deep breath in, and let's begin our counting adventure!",
], gesture=("cheer", None, 2.4), zoom=(1.05, 1.0))

# --- 2. Star Bridge: count 1..10, one number per scene, with repeat ---
b.scene("night_sky.png", [
    "Look! A magical Star Bridge has appeared in the night sky.",
    "The bridge opens only when we count its stars correctly. Let's go!",
], gesture=("cheer", None, 2.0), zoom=(1.05, 1.0))

for k in range(1, 11):
    bg = STAR_BG.format(min(k, 8))
    say = NUM[k].capitalize()
    if k == 1:
        talks = [f"Here is the very first star. This is number one. Can you say it? {say}!",
                 "Let's say it again, nice and loud. One! Wonderful, friends!"]
    elif k <= 9:
        prev = ", ".join(NUM[i] for i in range(1, k + 1))
        talks = [f"Now look, another star is glowing. That makes {say}!",
                 f"Let's count from the start: {prev}. Great counting!"]
    else:
        talks = ["Nine... and the last one... Ten! Hooray!",
                 "We counted all ten stars and crossed the magic bridge!"]
    g = ("point", "right", 4.0) if k % 2 else ("cheer", None, 2.0)
    b.scene(bg, talks, gesture=g, props=stars(k) if k in (3, 5, 10) else None,
            zoom=(1.0, 1.06) if k % 3 == 0 else None)

# --- 3. Count the apples in the garden ---
b.scene("garden.png", [
    "Wonderful! Now let's count something yummy. Let's count apples!",
    "Look at these red apples in the garden. Let's count them together.",
], gesture=("point", "right", 3.5), zoom=(1.0, 1.05))
for c in (3, 5):
    talks = [f"Count with me: {', '.join(NUM[i] for i in range(1, c + 1))}!",
             f"That is {NUM[c]} apples. You are doing a super job!"]
    b.scene("garden.png", talks, gesture=("point", "right", 4.5), props=apples(c))
b.scene("garden.png", [
    "Let's count all of them now. One, two, three, four, five apples!",
    "Five juicy apples! Yummy yummy. Great counting, friends!",
], gesture=("cheer", None, 2.4), props=apples(5))

# --- 4. Count claps and stomps (interactive) ---
b.scene("classroom.png", [
    "Now let's count with our own body. Let's count claps!",
    "Clap with me. One clap, two claps, three claps, four claps, five claps!",
], gesture=("cheer", None, 2.4), zoom=(1.0, 1.05))
b.scene("classroom.png", [
    "Now let's stomp our feet. One, two, three, four, five, six!",
    "Six big stomps! You are so good at counting. Keep going!",
], gesture=("point", "right", 4.0))

# --- 5. Counting song / sing-along ---
b.scene("playground.png", [
    "Let's sing the counting song! Sing along with me, friends.",
    "One, two, three, four, five! Six, seven, eight, nine, ten!",
], gesture=("cheer", None, 2.4), zoom=(1.0, 1.06))
b.scene("playground.png", [
    "One more time, a little faster! One, two, three, four, five!",
    "Six, seven, eight, nine, ten! You sang it perfectly!",
], gesture=("cheer", None, 2.4))

# --- 6. Count at the market ---
b.scene("market.png", [
    "Let's go to the market and count fresh vegetables!",
    "One tomato, two onions, three carrots, four potatoes, five peppers!",
], gesture=("point", "right", 4.5), zoom=(1.0, 1.05))
b.scene("market.png", [
    "So many vegetables! Let's count up to ten with the fruits too.",
    "Six, seven, eight, nine, ten! Ten healthy foods. Wonderful!",
], gesture=("point", "right", 4.5))

# --- 7. Count backwards (bonus) ---
b.scene("night_sky.png", [
    "Now for a fun challenge. Can we count backwards from ten?",
    "Get ready... here we go, friends!",
], gesture=("point", "right", 3.0), zoom=(1.05, 1.0))
b.scene("night_sky.png", [
    "Ten, nine, eight, seven, six!",
    "Five, four, three, two, one! Blast off! You are amazing!",
], gesture=("cheer", None, 2.4), props=stars(5))

# --- 8. Big recap ---
b.scene("classroom.png", [
    "Let's remember all our numbers together, nice and slow.",
    "One, two, three, four, five, six, seven, eight, nine, ten!",
], gesture=("point", "right", 5.0), zoom=(1.0, 1.05))
b.scene("classroom.png", [
    "One more time, all together now!",
    "One, two, three, four, five, six, seven, eight, nine, ten! Hooray!",
], gesture=("cheer", None, 2.4))

# --- 9. Goodbye ---
b.scene("garden.png", [
    "You did a super job counting today, my friends!",
    "You can count anything around you. Counting is everywhere!",
], gesture=("point", "right", 3.5), zoom=(1.0, 1.05))
b.scene("night_sky.png", [
    "Come back soon for more fun and learning with Kinnu.",
    "Please like and subscribe, and tell your friends. Bye bye!",
], gesture=("wave", None, 2.4), trans_out=0.7)

OUT.write_text(b.yaml(), encoding="utf-8")
print(f"wrote {OUT}  ({b.n} scenes, char={CHAR})")
