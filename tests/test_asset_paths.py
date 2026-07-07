from shiksha_cast.asset_paths import resolve_background_path, resolve_character_dir


def test_bare_character_id_preserves_legacy_cartoon_lookup(tmp_path):
    legacy = tmp_path / "assets" / "cartoon" / "characters" / "kinnu_hd"
    legacy.mkdir(parents=True)

    assert resolve_character_dir(tmp_path, "kinnu_hd") == legacy


def test_namespaced_character_id_uses_new_character_root(tmp_path):
    expected = tmp_path / "assets" / "characters" / "social_universe" / "journalist_hd"

    assert resolve_character_dir(tmp_path, "social_universe/journalist_hd") == expected


def test_explicit_asset_character_path_is_respected(tmp_path):
    expected = tmp_path / "assets" / "characters" / "social_universe" / "officer_hd"

    assert resolve_character_dir(tmp_path, "assets/characters/social_universe/officer_hd") == expected


def test_bare_background_preserves_legacy_cartoon_lookup(tmp_path):
    legacy = tmp_path / "assets" / "cartoon" / "backgrounds" / "classroom.png"
    legacy.parent.mkdir(parents=True)
    legacy.touch()

    assert resolve_background_path(tmp_path, "classroom.png") == legacy


def test_namespaced_background_uses_new_background_root(tmp_path):
    expected = tmp_path / "assets" / "backgrounds" / "social_universe" / "office.png"

    assert resolve_background_path(tmp_path, "social_universe/office.png") == expected
