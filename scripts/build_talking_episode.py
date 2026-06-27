"""Build a Binocs-style "talking Kinnu" episode: a BACKGROUND per slide + one reusable
talking-Kinnu overlay (lip-synced to the narration), then concat + music bed + -14 LUFS
master + captions. Reuses the normal narration (Kokoro) and assemble steps.

Backgrounds: build/<ep>/backgrounds/bg_001.png ...   (falls back to build/<ep>/slides/
slide_NNN.png so it still renders before real no-character backgrounds exist).
Rig: assets/kinnu_rig (your real 3-mouth PNGs) or assets/kinnu_rig_placeholder.

Usage:
  python scripts/build_talking_episode.py <episode-id> [--rig DIR] [--bg-dir DIR]
         [--char-x 0.18] [--char-h 0.72] [--out dist/<ep>.mp4]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from shiksha_cast.assemble import concat_clips, mix_music_bed, normalize_loudness  # noqa: E402
from shiksha_cast.captions import write_captions  # noqa: E402
from shiksha_cast.config import find_chapter_dir, load_channel_config, load_script  # noqa: E402
from shiksha_cast.speak import speak_chapter  # noqa: E402

from lipsync_clip import build_talking_clip  # noqa: E402


def _default_rig(root: Path) -> Path:
    real = root / "assets" / "kinnu_rig"
    rj = real / "rig.json"
    if rj.exists():
        try:
            rig = json.load(open(rj, encoding="utf-8"))
            files = list(rig.get("frames", {}).values())
            if not files:
                files = [rig.get("character")] + list(rig.get("mouths", {}).values())
            if files and all((real / f).exists() for f in files if f):
                return real
        except Exception:
            pass
    return root / "assets" / "kinnu_rig_placeholder"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--rig", default=None)
    ap.add_argument("--bg-dir", default=None)
    ap.add_argument("--char-x", type=float, default=0.18, help="Kinnu center x (0..1); 0.18 = lower-left")
    ap.add_argument("--char-h", type=float, default=0.72, help="Kinnu height fraction of frame")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    ep = a.episode
    cfg = load_channel_config(ROOT)
    w, h = cfg.resolution
    chapter_dir = find_chapter_dir(ROOT, ep)
    script = load_script(chapter_dir)

    rig = Path(a.rig) if a.rig else _default_rig(ROOT)
    print(f"[rig] {rig.name}")

    build_dir = ROOT / "build" / ep
    bg_dir = Path(a.bg_dir) if a.bg_dir else (build_dir / "backgrounds")
    slides_dir = build_dir / "slides"

    print(f"[stage] narration ({len(script.slides)} slides)...")
    speak = speak_chapter(ep, ROOT, script, cfg, force=False)

    clips_dir = build_dir / "talk_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clip_paths = []
    n = len(speak.audio_paths)
    for i, (audio, _dur) in enumerate(zip(speak.audio_paths, speak.durations), 1):
        bg = bg_dir / f"bg_{i:03d}.png"
        if not bg.exists():
            bg = slides_dir / f"slide_{i:03d}.png"  # fallback until real backgrounds exist
        bg_arg = str(bg) if bg.exists() else None
        out_clip = clips_dir / f"clip_{i:03d}.mp4"
        print(f"[clip] {i}/{n} (bg={'yes' if bg_arg else 'sky'})...")
        build_talking_clip(
            str(audio), str(rig), str(out_clip), bg=bg_arg, fps=cfg.fps,
            width=w, height=h,
            pad_before_s=cfg.timing.pad_before_ms / 1000,
            pad_after_s=cfg.timing.pad_after_ms / 1000,
            min_slide_s=cfg.timing.min_slide_s,
            char_x_frac=a.char_x, char_height_frac=a.char_h,
        )
        clip_paths.append(out_clip)

    out = Path(a.out) if a.out else (ROOT / "dist" / f"{ep}.mp4")
    body = build_dir / "talk_body.mp4"
    print("[stage] concatenating...")
    concat_clips(clip_paths, body)

    music = (ROOT / cfg.music.bed) if cfg.music.bed else None
    if music and music.exists():
        print("[stage] music bed + -14 LUFS master...")
        mix_music_bed(body, music, out, cfg.music.duck_db, cfg.voice.sample_rate)
    else:
        print("[stage] -14 LUFS master...")
        normalize_loudness(body, out, cfg.voice.sample_rate)

    print("[stage] captions...")
    write_captions(
        chapter=ep, project_root=ROOT,
        narrations=[s.narration for s in script.slides],
        durations=speak.durations,
        pad_before_s=cfg.timing.pad_before_ms / 1000,
        pad_after_s=cfg.timing.pad_after_ms / 1000,
        min_slide_s=cfg.timing.min_slide_s, start_offset_s=0.0,
    )
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
