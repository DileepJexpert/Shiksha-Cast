"""Phoneme-accurate lip-sync via Rhubarb Lip Sync (optional, local, free).

Rhubarb (https://github.com/DanielWolf/rhubarb-lip-sync) analyses a narration WAV and
emits a timeline of mouth shapes in the Preston-Blair A-H + X scheme — which is exactly
the set the Kinnu HD rig draws (mouth_A … mouth_H, mouth_X). So its output maps 1:1 onto
our visemes, giving real "which phoneme" mouths instead of amplitude guesswork.

It is entirely optional: if the `rhubarb` binary isn't installed, callers fall back to the
amplitude-based Lipsync. Point the code at a non-PATH binary with $SHIKSHA_RHUBARB, or
disable it with SHIKSHA_RHUBARB=0.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Rhubarb already emits A-H and X; the Kinnu rig uses the same letters, so this is
# identity. Kept explicit so an unknown shape can't leak through as a bad filename.
_VALID = {"A", "B", "C", "D", "E", "F", "G", "H", "X"}

# Collapse the 9 visemes onto the simple 3-mouth rig (closed / half / open), by how
# open each shape is: A/X closed, B/C/G/H a small opening, D/E/F wide.
_TO_SIMPLE = {
    "X": "closed", "A": "closed",
    "B": "half", "C": "half", "G": "half", "H": "half",
    "D": "open", "E": "open", "F": "open",
}


def rhubarb_binary() -> str | None:
    """Path to the rhubarb executable, or None if unavailable/disabled."""
    override = os.environ.get("SHIKSHA_RHUBARB")
    if override in ("0", "off", "false", "no"):
        return None
    if override:
        return override if Path(override).exists() else None
    return shutil.which("rhubarb")


def available() -> bool:
    return rhubarb_binary() is not None


def visemes_for_wav(wav_path: str | Path, timeout: float = 300.0) -> list[tuple[float, float, str]]:
    """Return [(start_s, end_s, shape)] for a WAV, or [] if rhubarb is unavailable or
    fails. Uses the language-independent 'phonetic' recognizer so Hinglish narration
    works without an English dialog transcript."""
    binary = rhubarb_binary()
    if not binary:
        return []
    wav_path = Path(wav_path)
    if not wav_path.exists():
        return []
    out_json = Path(tempfile.mkdtemp()) / "cues.json"
    cmd = [binary, "-r", "phonetic", "-f", "json",
           "--extendedShapes", "GHX", "-o", str(out_json), str(wav_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        data = json.loads(out_json.read_text(encoding="utf-8"))
    except (subprocess.SubprocessError, OSError, ValueError) as e:  # noqa: BLE001
        print(f"[rhubarb] fell back to amplitude lip-sync ({type(e).__name__}: {e})")
        return []
    finally:
        try:
            out_json.unlink()
            out_json.parent.rmdir()
        except OSError:
            pass
    cues = []
    for c in data.get("mouthCues", []):
        shape = str(c.get("value", "X")).upper()
        if shape in _VALID:
            cues.append((float(c["start"]), float(c["end"]), shape))
    return cues


def viseme_at(cues: list[tuple[float, float, str]], t: float) -> str:
    """The mouth shape (A-H/X) active at local time t. Assumes cues are sorted and
    contiguous (as rhubarb emits them). Linear scan is fine for one line's worth."""
    for start, end, shape in cues:
        if start <= t < end:
            return shape
    return "X"


def simple_at(cues: list[tuple[float, float, str]], t: float) -> str:
    """viseme_at collapsed to the 3-shape rig: closed / half / open."""
    return _TO_SIMPLE.get(viseme_at(cues, t), "closed")
