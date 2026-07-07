"""Tests for the tutorial-build generator (7-beat lesson -> scenes.yaml)."""
import yaml

from shiksha_cast.cartoon import tutorial

SPEC = {
    "class": 3,
    "subject": "Maths",
    "chapter": "Addition",
    "topic": "What is Addition?",
    "language": "English",
    "characters": {"teacher": "kinnu_hd", "student": "vibhu_sheet_hd"},
    "voices": {"teacher": "af_heart", "student": "am_adam"},
    "beats": {
        "hook": {"say": ["Hello!", "Ready?"], "banner": "Let's Learn!"},
        "concept": {"say": ["Addition is putting together."],
                    "board": {"title": "What is Addition?", "lines": ["+ means add", "count all"]}},
        "example": {"say": ["Two plus three."], "props": ["apple.png", "apple.png"],
                    "board": {"title": "2 + 3 = ?", "lines": ["count", "= 5"]},
                    "callout": "count them all!"},
        "question": {"say": ["What is 4 + 1?"], "banner": "Your Turn!"},
        "solve": {"say": ["Start at four."],
                  "board": {"title": "4 + 1 = ?", "steps": ["start at 4", "4 + 1 = 5"]},
                  "callouts": ["start at 4", "the answer!"]},
        "recap": {"say": ["Addition is putting together."],
                  "board": {"title": "Remember!", "lines": ["+ means add"]}},
        "practice": {"say": ["Try at home."], "outro": "Bye bye!",
                     "board": {"title": "Practice Time!", "lines": ["2 + 2 = ?"]}},
    },
}


def test_slugify():
    assert tutorial.slugify("Class 3", "Maths!", "What is Addition?") == "class-3-maths-what-is-addition"


def test_episode_id_from_fields():
    assert tutorial.episode_id(SPEC) == "c3-maths-what-is-addition"


def test_build_scenes_has_seven_beats_in_order():
    out = tutorial.build_scenes(SPEC)
    ids = [s["id"] for s in out["scenes"]]
    assert ids == ["s1_hook", "s2_concept", "s3_example", "s4_question",
                   "s5_solve", "s6_recap", "s7_practice"]


def test_cast_includes_both_characters_with_voices():
    out = tutorial.build_scenes(SPEC)
    assert out["cast"] == {"kinnu_hd": "af_heart", "vibhu_sheet_hd": "am_adam"}


def test_talk_lines_are_emitted_for_teacher():
    out = tutorial.build_scenes(SPEC)
    hook = out["scenes"][0]
    talks = [a for a in hook["actions"] if a["do"] == "talk"]
    assert [t["text"] for t in talks] == ["Hello!", "Ready?"]
    assert all(t["who"] == "kinnu_hd" for t in talks)


def test_board_lines_get_reveal_times():
    out = tutorial.build_scenes(SPEC)
    concept = out["scenes"][1]
    lines = concept["board"]["lines"]
    ats = [ln["at"] for ln in lines]
    assert ats == sorted(ats)          # increasing reveal order
    assert all(isinstance(ln["text"], str) for ln in lines)


def test_steps_alias_is_accepted_as_lines():
    out = tutorial.build_scenes(SPEC)
    solve = out["scenes"][4]
    texts = [ln["text"] for ln in solve["board"]["lines"]]
    assert "start at 4" in texts and "4 + 1 = 5" in texts


def test_example_props_become_prop_row():
    out = tutorial.build_scenes(SPEC)
    example = out["scenes"][2]
    assert len(example["props"]) == 2
    assert all(p["asset"] == "apple.png" for p in example["props"])


def test_overlays_banner_and_callout_present():
    out = tutorial.build_scenes(SPEC)
    hook_ovs = out["scenes"][0]["overlays"]
    assert any(o["type"] == "banner" for o in hook_ovs)
    ex_ovs = out["scenes"][2]["overlays"]
    assert any(o["type"] == "callout" for o in ex_ovs)


def test_no_student_spec_still_builds():
    spec = {**SPEC, "characters": {"teacher": "kinnu_hd"}}
    out = tutorial.build_scenes(spec)
    assert out["cast"] == {"kinnu_hd": "af_heart"}
    # question scene should not reference a student
    q = out["scenes"][3]
    assert all(c["id"] == "kinnu_hd" for c in q["characters"])


def test_generated_scenes_yaml_round_trips_without_aliases():
    out = tutorial.build_scenes(SPEC)
    text = yaml.dump(out, Dumper=tutorial._NoAliasDumper, sort_keys=False, allow_unicode=True)
    assert "*id" not in text and "&id" not in text
    reload = yaml.safe_load(text)
    assert reload["episode"] == "c3-maths-what-is-addition"


def test_upload_metadata_has_required_sections():
    md = tutorial.upload_metadata(SPEC)
    for section in ("Title:", "Description:", "Hashtags:", "Tags:"):
        assert section in md
    assert "Katixo" in md
