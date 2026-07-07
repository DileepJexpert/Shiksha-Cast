"""Tests for the story.yaml -> scenes.yaml compiler (story-universe factory)."""
from shiksha_cast.cartoon import story

SPEC = {
    "title": "The Borrowed Book",
    "fps": 30,
    "background": "story_living_room.png",
    "cast": {"papa": "story_father_hd", "ravi": "story_young_hd"},
    "voices": {"papa": "am_michael", "ravi": "am_adam"},
    "scenes": [
        {"id": "s1", "banner": "The Borrowed Book",
         "place": {"papa": "left", "ravi": "right"},
         "dialogue": [
             {"who": "papa", "text": "Come here, beta."},
             {"who": "ravi", "text": "Yes papa?"},
         ]},
        {"id": "s2", "dialogue": [{"who": "papa", "text": "Always return what you borrow."}]},
    ],
}


def test_story_id_slugifies_title():
    assert story.story_id({"title": "The Borrowed Book"}) == "story-the-borrowed-book"
    assert story.story_id({"story_id": "custom-id", "title": "X"}) == "custom-id"


def test_build_scenes_maps_cast_to_voices():
    out = story.build_scenes(SPEC)
    assert out["cast"] == {"story_father_hd": "am_michael", "story_young_hd": "am_adam"}
    assert out["episode"] == "story-the-borrowed-book"
    assert out["fps"] == 30
    assert len(out["scenes"]) == 2


def test_build_scenes_keeps_namespaced_social_asset_ids():
    spec = {
        **SPEC,
        "cast": {
            "reporter": "social_universe/journalist_hd",
            "student": "social_universe/student_hd",
        },
        "voices": {"reporter": "af_heart", "student": "am_adam"},
        "scenes": [{"dialogue": [{"who": "reporter", "text": "What happened?"}]}],
    }

    out = story.build_scenes(spec)

    assert out["cast"] == {
        "social_universe/journalist_hd": "af_heart",
        "social_universe/student_hd": "am_adam",
    }
    assert out["scenes"][0]["characters"][0]["id"] == "social_universe/journalist_hd"


def test_story_universe_prefixes_bare_assets_and_backgrounds():
    spec = {
        "title": "Paper Leak",
        "universe": "social_universe",
        "background": "public_office.png",
        "cast": {"reporter": "journalist_hd", "student": "student_hd"},
        "voices": {"reporter": "af_heart", "student": "am_adam"},
        "scenes": [
            {"dialogue": [{"who": "reporter", "text": "What happened?"}]},
            {"background": "news_room.png",
             "dialogue": [{"who": "student", "text": "The paper leaked."}]},
        ],
    }

    out = story.build_scenes(spec)

    assert out["cast"] == {
        "social_universe/journalist_hd": "af_heart",
        "social_universe/student_hd": "am_adam",
    }
    assert out["scenes"][0]["background"] == "social_universe/public_office.png"
    assert out["scenes"][1]["background"] == "social_universe/news_room.png"


def test_social_universe_defaults_to_veena_tts():
    spec = {
        "title": "Paper Leak",
        "universe": "social_universe",
        "cast": {"reporter": "journalist_hd", "student": "student_hd"},
        "voices": {"reporter": "kavya", "student": "agastya"},
        "scenes": [{"dialogue": [{"who": "student", "text": "Main chup nahi rahunga."}]}],
    }

    out = story.build_scenes(spec)

    assert out["tts_provider"] == "veena"
    assert out["cast"] == {
        "social_universe/journalist_hd": "kavya",
        "social_universe/student_hd": "agastya",
    }


def test_characters_placed_left_and_right_face_each_other():
    out = story.build_scenes(SPEC)
    chars = {c["id"]: c for c in out["scenes"][0]["characters"]}
    papa, ravi = chars["story_father_hd"], chars["story_young_hd"]
    assert papa["pos"][0] < 0.5 and papa["facing"] == "right"
    assert ravi["pos"][0] > 0.5 and ravi["facing"] == "left"


def test_dialogue_becomes_talk_actions_in_order():
    out = story.build_scenes(SPEC)
    acts = out["scenes"][0]["actions"]
    assert [a["who"] for a in acts] == ["story_father_hd", "story_young_hd"]
    assert all(a["do"] == "talk" and a["text"] for a in acts)


def test_dialogue_gesture_stays_attached_to_talk_action():
    spec = {
        **SPEC,
        "scenes": [{"dialogue": [{"who": "papa", "text": "Look here.", "gesture": "point"}]}],
    }
    out = story.build_scenes(spec)
    assert out["scenes"][0]["actions"][0]["gesture"] == "point"


def test_lone_speaker_keeps_pinned_side():
    out = story.build_scenes(SPEC)
    s2 = out["scenes"][1]
    assert len(s2["characters"]) == 1
    assert s2["characters"][0]["pos"][0] < 0.5
    assert s2["characters"][0]["facing"] == "right"


def test_characters_do_not_swap_sides_when_dialogue_order_changes():
    spec = {**SPEC, "scenes": [
        SPEC["scenes"][0],
        {"id": "s3", "dialogue": [
            {"who": "ravi", "text": "I will return it."},
            {"who": "papa", "text": "Good."},
        ]},
    ]}
    out = story.build_scenes(spec)
    chars = {c["id"]: c for c in out["scenes"][1]["characters"]}
    assert chars["story_father_hd"]["pos"][0] < 0.5
    assert chars["story_young_hd"]["pos"][0] > 0.5


def test_banner_becomes_overlay():
    out = story.build_scenes(SPEC)
    ov = out["scenes"][0]["overlays"]
    assert ov[0]["type"] == "banner" and ov[0]["text"] == "The Borrowed Book"


def test_metadata_has_title_and_tags():
    md = story.upload_metadata(SPEC)
    assert "The Borrowed Book" in md
    assert "Tags:" in md and "moral story" in md
