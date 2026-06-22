import tempfile
from pathlib import Path

from shiksha_cast.cache import BuildManifest, content_hash, file_hash


def test_content_hash_deterministic():
    h1 = content_hash("hello", "world")
    h2 = content_hash("hello", "world")
    assert h1 == h2
    assert len(h1) == 16


def test_content_hash_varies():
    h1 = content_hash("hello")
    h2 = content_hash("goodbye")
    assert h1 != h2


def test_file_hash(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("test content")
    h1 = file_hash(f)
    h2 = file_hash(f)
    assert h1 == h2
    assert len(h1) == 16


def test_manifest_roundtrip(tmp_path: Path):
    m = BuildManifest(tmp_path)
    m.set("render", "key1", {"output": "slide.png", "hash": "abc"})
    m.save()

    m2 = BuildManifest(tmp_path)
    entry = m2.get("render", "key1")
    assert entry is not None
    assert entry["output"] == "slide.png"


def test_manifest_missing_key(tmp_path: Path):
    m = BuildManifest(tmp_path)
    assert m.get("render", "nonexistent") is None
