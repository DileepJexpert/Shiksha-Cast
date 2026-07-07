"""tutorial-build: turn a compact, curriculum-grounded lesson spec into a full
cutout-cartoon ``scenes.yaml`` (plus YouTube metadata), following one fixed
7-beat teaching format so every Kinnu Learning Academy video has the same shape:

    1. Hook / question        4. Kinnu asks a question
    2. Explain the concept     5. Solve step by step
    3. Show an example         6. Quick recap
                               7. Practice / homework

The lesson CONTENT (what is said, the worked example, the steps) is authored by a
human (or, later, drafted by a local Ollama from an NCERT chapter and reviewed) --
this module owns only the STRUCTURE: how each beat becomes scenes with a teaching
chalkboard (see cartoon/overlay.py), title banners, callouts, props and lively
teacher/student actions. It deliberately reuses the existing cartoon-build
renderer; it does not render anything itself.

Spec schema (tutorial.yaml):

    class: 3
    subject: Maths
    chapter: Addition
    topic: What is Addition?
    language: English                 # English -> Kokoro; (Hindi/Hinglish -> Veena, future)
    characters: { teacher: kinnu_hd, student: vibhu_sheet_hd }
    voices:     { teacher: af_heart,  student: am_adam }   # optional
    background: classroom_full.png    # optional
    beats:
      hook:     { say: [...], banner: "Let's Learn Addition!" }
      concept:  { say: [...], board: { title: "...", lines: [...] } }
      example:  { say: [...], board: {...}, props: [apple,apple,...], callout: "..." }
      question: { say: [...], banner: "Your Turn!" }
      solve:    { say: [...], board: { title: "...", lines: [...] }, callouts: [...] }
      recap:    { say: [...], board: { title: "Remember!", lines: [...] } }
      practice: { say: [...], board: { title: "Practice Time!", lines: [...] },
                  outro: "Bye bye! Like and subscribe!" }
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

BEAT_ORDER = ["hook", "concept", "example", "question", "solve", "recap", "practice"]
DEFAULT_BG = "classroom_full.png"
DEFAULT_VOICES = {"teacher": "af_heart", "student": "am_adam"}


def slugify(*parts: str) -> str:
    s = "-".join(str(p) for p in parts if p)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


class _NoAliasDumper(yaml.SafeDumper):
    """Emit plain YAML without &anchors/*aliases (shared pos/size constants would
    otherwise serialize as aliases, which is valid but ugly and easy to misedit)."""

    def ignore_aliases(self, data):
        return True


def load_spec(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def episode_id(spec: dict) -> str:
    if spec.get("episode_id"):
        return spec["episode_id"]
    return slugify(f"c{spec.get('class', 3)}", spec.get("subject", ""), spec.get("topic", ""))


# --------------------------------------------------------------------------- #
#  small builders
# --------------------------------------------------------------------------- #
def _talks(who: str, lines) -> list:
    out = []
    for ln in (lines or []):
        out.append({"who": who, "do": "talk", "text": str(ln)})
    return out


def _board(spec_board: dict | None, pos=None, size=None) -> dict | None:
    if not spec_board:
        return None
    b = dict(spec_board)
    # accept either lines: [...] or steps: [...]
    if "steps" in b and "lines" not in b:
        b["lines"] = b.pop("steps")
    lines = []
    for i, ln in enumerate(b.get("lines", [])):
        ln = {"text": ln} if isinstance(ln, str) else dict(ln)
        ln.setdefault("at", round(0.5 + i * 1.4, 2))
        lines.append(ln)
    b["lines"] = lines
    if pos:
        b.setdefault("pos", pos)
    if size:
        b.setdefault("size", size)
    return b


def _prop_row(assets: list, y=0.30, scale=0.12, x0=0.40, x1=0.92) -> list:
    """Lay a list of prop assets out in a horizontal row above a board area."""
    props = []
    n = max(1, len(assets))
    for i, a in enumerate(assets):
        x = x0 if n == 1 else x0 + (x1 - x0) * i / (n - 1)
        props.append({"asset": a, "pos": [round(x, 3), y], "scale": scale,
                      "anim": "pop", "start": round(0.4 + i * 0.3, 2)})
    return props


# --------------------------------------------------------------------------- #
#  beat -> scene(s)
# --------------------------------------------------------------------------- #
def build_scenes(spec: dict) -> dict:
    chars = spec.get("characters", {})
    teacher = chars.get("teacher", "kinnu_hd")
    student = chars.get("student")
    voices = {**DEFAULT_VOICES, **(spec.get("voices") or {})}
    bg = spec.get("background", DEFAULT_BG)
    beats = spec.get("beats", {})
    fps = int(spec.get("fps", 15))

    cast = {teacher: voices["teacher"]}
    if student:
        cast[student] = voices["student"]

    # teacher placement: left when a board is on the right
    T_SIDE = [0.17, 0.99]
    T_MID = [0.32, 0.99]
    S_RIGHT = [0.82, 0.99]
    BOARD_POS = [0.66, 0.40]
    BOARD_SIZE = [0.58, 0.62]

    scenes: list = []

    def scene(sid, **kw):
        s = {"id": sid, "background": kw.pop("background", bg),
             "transition": {"in": 0.3, "out": 0.25}}
        s.update(kw)
        scenes.append(s)

    # ---- 1. HOOK ----
    hk = beats.get("hook", {})
    chars1 = [{"id": teacher, "pos": T_MID, "scale": 0.9, "facing": "right"}]
    acts1 = [{"who": teacher, "do": "wave", "start": 0.0, "end": 3.5}]
    if student:
        chars1.append({"id": student, "pos": S_RIGHT, "scale": 0.86, "facing": "left"})
        acts1.append({"who": student, "do": "wave", "start": 0.4, "end": 3.5})
    acts1 += _talks(teacher, hk.get("say"))
    ov1 = [{"type": "banner", "text": hk.get("banner", "Let's Learn!"), "start": 0.0, "end": 4.0}]
    scene("s1_hook", characters=chars1, actions=acts1, overlays=ov1)

    # ---- 2. CONCEPT ----
    cc = beats.get("concept", {})
    acts2 = [{"who": teacher, "do": "point", "side": "right", "start": 0.2, "end": 9.0}]
    acts2 += _talks(teacher, cc.get("say"))
    scene("s2_concept",
          characters=[{"id": teacher, "pos": T_SIDE, "scale": 0.9, "facing": "right"}],
          actions=acts2, board=_board(cc.get("board"), BOARD_POS, BOARD_SIZE))

    # ---- 3. EXAMPLE ----
    ex = beats.get("example", {})
    acts3 = [{"who": teacher, "do": "point", "side": "right", "start": 0.2, "end": 10.0}]
    acts3 += _talks(teacher, ex.get("say"))
    ov3 = []
    if ex.get("callout"):
        ov3.append({"type": "callout", "text": ex["callout"], "pos": [0.29, 0.58],
                    "start": 1.0, "end": 8.0, "color": "pink"})
    # counters sit in a clear band along the top; the board drops slightly so they
    # never overlap the title.
    props3 = _prop_row(ex["props"], y=0.11, scale=0.09, x0=0.42, x1=0.92) if ex.get("props") else []
    ex_board_pos = [0.66, 0.47] if ex.get("props") else BOARD_POS
    ex_board_size = [0.56, 0.50] if ex.get("props") else BOARD_SIZE
    scene("s3_example",
          characters=[{"id": teacher, "pos": T_SIDE, "scale": 0.9, "facing": "right"}],
          actions=acts3, board=_board(ex.get("board"), ex_board_pos, ex_board_size),
          overlays=ov3, props=props3)

    # ---- 4. QUESTION (Kinnu asks; student thinks) ----
    qq = beats.get("question", {})
    chars4 = [{"id": teacher, "pos": T_MID, "scale": 0.9, "facing": "right"}]
    acts4 = [{"who": teacher, "do": "think", "start": 0.2, "end": 2.0}]
    if student:
        chars4.append({"id": student, "pos": S_RIGHT, "scale": 0.86, "facing": "left"})
        acts4.append({"who": student, "do": "think", "start": 0.5, "end": 6.0})
    acts4 += _talks(teacher, qq.get("say"))
    ov4 = [{"type": "banner", "text": qq.get("banner", "Your Turn!"), "start": 0.0,
            "end": 4.0, "color": "blue"}]
    scene("s4_question", characters=chars4, actions=acts4, overlays=ov4)

    # ---- 5. SOLVE step by step ----
    sv = beats.get("solve", {})
    acts5 = [{"who": teacher, "do": "point", "side": "right", "start": 0.2, "end": 12.0}]
    acts5 += _talks(teacher, sv.get("say"))
    ov5 = []
    for i, co in enumerate(sv.get("callouts", []) or []):
        ov5.append({"type": "callout", "text": str(co), "pos": [0.29, 0.56],
                    "start": round(1.5 + i * 2.5, 2), "end": round(4.0 + i * 2.5, 2),
                    "color": "yellow"})
    scene("s5_solve",
          characters=[{"id": teacher, "pos": T_SIDE, "scale": 0.9, "facing": "right"}],
          actions=acts5, board=_board(sv.get("board"), BOARD_POS, BOARD_SIZE), overlays=ov5)

    # ---- 6. RECAP ----
    rc = beats.get("recap", {})
    chars6 = [{"id": teacher, "pos": T_SIDE, "scale": 0.9, "facing": "right"}]
    acts6 = [{"who": teacher, "do": "clap", "start": 0.0, "end": 2.5}]
    acts6 += _talks(teacher, rc.get("say"))
    rb = rc.get("board") or {"title": "Remember!", "lines": rc.get("say", [])[:4]}
    scene("s6_recap", characters=chars6, actions=acts6,
          board=_board(rb, BOARD_POS, BOARD_SIZE))

    # ---- 7. PRACTICE / OUTRO ----
    pr = beats.get("practice", {})
    chars7 = [{"id": teacher, "pos": T_SIDE, "scale": 0.9, "facing": "right"}]
    if student:
        chars7.append({"id": student, "pos": [0.30, 0.99], "scale": 0.86, "facing": "right"})
    acts7 = [{"who": teacher, "do": "point", "side": "right", "start": 0.2, "end": 9.0}]
    acts7 += _talks(teacher, pr.get("say"))
    if pr.get("outro"):
        acts7.append({"who": teacher, "do": "wave", "start": 9.0, "end": 14.0})
        acts7 += _talks(teacher, [pr["outro"]])
    pb = pr.get("board") or {"title": "Practice Time!", "lines": pr.get("problems", [])}
    ov7 = [{"type": "banner", "text": "Practice Time!", "start": 0.0, "end": 4.0, "color": "green"}]
    scene("s7_practice", characters=chars7, actions=acts7,
          board=_board(pb, BOARD_POS, BOARD_SIZE), overlays=ov7,
          transition={"in": 0.3, "out": 0.5})

    title = spec.get("title") or _auto_title(spec)
    return {"episode": episode_id(spec), "title": title, "fps": fps,
            "cast": cast, "scenes": scenes}


# --------------------------------------------------------------------------- #
#  metadata
# --------------------------------------------------------------------------- #
def _auto_title(spec: dict) -> str:
    topic = spec.get("topic", "Lesson")
    subject = spec.get("subject", "")
    klass = spec.get("class", "")
    return f"{topic} | Class {klass} {subject} | Kinnu Learning"


def upload_metadata(spec: dict) -> str:
    topic = spec.get("topic", "Lesson")
    subject = spec.get("subject", "")
    chapter = spec.get("chapter", "")
    klass = spec.get("class", "")
    lang = spec.get("language", "English")
    title = spec.get("title") or _auto_title(spec)
    desc = spec.get("description") or (
        f"Learn {topic} in this fun {lang} lesson for Class {klass} {subject} "
        f"(Chapter: {chapter}). Kinnu teaches step by step with a blackboard, "
        f"examples and easy practice questions."
    )
    tags = [
        "kinnu", "kinnu learning", f"class {klass} {subject.lower()}",
        f"{subject.lower()} for kids", topic.lower(), chapter.lower(),
        f"class {klass} {subject.lower()} {chapter.lower()}".strip(),
        "ncert class 3", "kids education", "learn with kinnu", "katixo channel",
    ]
    tags = [t for t in tags if t and t.strip()]
    subj_tag = re.sub(r"[^A-Za-z0-9]", "", subject) or "Learning"
    # phrase the first bullet naturally whether the topic is a noun or a question
    topic_bullet = topic.rstrip("?") if topic.strip().lower().startswith(("what", "how", "why", "when")) \
        else f"What {topic} means"
    return (
        f"Title:\n{title}\n\n"
        f"Description:\n{desc}\n\n"
        "In this video, kids will learn:\n"
        f"✅ {topic_bullet}\n"
        "✅ Step-by-step solving on the blackboard\n"
        "✅ A worked example\n"
        "✅ Practice questions to try at home\n\n"
        f"Great for Class {klass} students, preschool, and early learners.\n\n"
        "A Katixo channel.\n\n"
        f"Hashtags:\n#KinnuLearning #Class{klass}{subj_tag} #{subj_tag}ForKids "
        "#KidsEducation #NCERT #LearnWithKinnu\n\n"
        f"Tags:\n{', '.join(tags)}\n"
    )


# --------------------------------------------------------------------------- #
#  scaffold (write scenes.yaml + UPLOAD_METADATA.md next to the spec)
# --------------------------------------------------------------------------- #
def generate(spec_path: str | Path) -> dict:
    spec_path = Path(spec_path)
    spec = load_spec(spec_path)
    out_dir = spec_path.parent
    scenes = build_scenes(spec)
    scenes_path = out_dir / "scenes.yaml"
    scenes_path.write_text(
        yaml.dump(scenes, Dumper=_NoAliasDumper, sort_keys=False,
                  allow_unicode=True, width=100),
        encoding="utf-8",
    )
    meta_path = out_dir / "UPLOAD_METADATA.md"
    meta_path.write_text(upload_metadata(spec), encoding="utf-8")
    return {"episode": scenes["episode"], "scenes_path": scenes_path,
            "metadata_path": meta_path, "n_scenes": len(scenes["scenes"])}


def taxonomy_dir(content_root: Path, spec: dict) -> Path:
    """content/<channel>/tutorials/class<N>/<subject>/<chapter>/<episode_id>/"""
    return (content_root / "tutorials" / f"class{spec.get('class', 3)}"
            / slugify(spec.get("subject", "")) / slugify(spec.get("chapter", ""))
            / episode_id(spec))
