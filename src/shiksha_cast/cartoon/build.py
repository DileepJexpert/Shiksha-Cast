"""Cutout cartoon episode builder.

Parses a scenes.yaml, synthesizes per-line narration (local Kokoro, per-character
voice), schedules a timeline, renders frames (poses from the motion library +
amplitude lip-sync + blinks), encodes per-scene clips, then concatenates with the
music bed, masters to -14 LUFS, and writes captions. No GPU at runtime.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from PIL import Image, ImageDraw

from shiksha_cast.assemble import concat_clips, mix_music_bed, normalize_loudness
from shiksha_cast.cartoon import motion
from shiksha_cast.cartoon.character import Character
from shiksha_cast.cartoon.lipsync import Lipsync
from shiksha_cast.config import load_channel_config
from shiksha_cast.tts.kokoro import KokoroTTSProvider

CHARS_DIR = "assets/cartoon/characters"
BG_DIR = "assets/cartoon/backgrounds"


def _bg(project_root: Path, name, W, H):
    if name:
        p = project_root / BG_DIR / name
        if p.exists():
            return Image.open(p).convert("RGBA").resize((W, H))
    img = Image.new("RGBA", (W, H), (170, 220, 255, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.78, H * 0.08, W * 0.92, H * 0.30], fill=(255, 220, 90, 255))
    d.rectangle([0, int(H * 0.80), W, H], fill=(85, 180, 110, 255))
    d.rectangle([0, int(H * 0.80), W, int(H * 0.82)], fill=(70, 160, 95, 255))
    return img


def _srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _schedule(scene):
    """Copy actions; give non-talk actions default windows. talk starts/ends are
    resolved during TTS (auto-chained) since they depend on audio length."""
    out = []
    for a in scene.get("actions", []):
        a = dict(a)
        if a.get("do") != "talk":
            a.setdefault("start", 0.0)
            a.setdefault("end", a["start"] + 1.4)
        out.append(a)
    return out


def build_episode(scene_path: str, project_root: Path, out: str | None = None) -> Path:
    spec = yaml.safe_load(open(scene_path, encoding="utf-8"))
    cfg = load_channel_config(project_root)
    W, H = cfg.resolution
    fps = int(spec.get("fps", cfg.fps))
    sr = cfg.voice.sample_rate
    ep = spec.get("episode") or Path(scene_path).parent.name
    cast = spec.get("cast", {})

    chars = {}
    for name in cast:
        d = project_root / CHARS_DIR / name
        if (d / "rig.json").exists():
            chars[name] = Character(d)

    work = project_root / "build" / ep
    (work / "audio").mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"; clips_dir.mkdir(parents=True, exist_ok=True)
    tts = KokoroTTSProvider()

    clip_paths, captions = [], []
    scene_offset = 0.0
    line_no = 0

    for si, scene in enumerate(spec.get("scenes", []), 1):
        bg = _bg(project_root, scene.get("background"), W, H)
        present = {c["id"]: c for c in scene.get("characters", [])}
        actions = _schedule(scene)

        # --- synth talk audio + finalize talk windows (auto-chained) ---
        talk_cursor = 0.0
        for a in actions:
            if a.get("do") == "talk":
                line_no += 1
                voice = cast.get(a["who"], "af_heart")
                wav = work / "audio" / f"line_{line_no:03d}.wav"
                tts.set_speaker(voice)
                tts.synthesize(a["text"], "", wav)
                ls = Lipsync(str(wav), fps)
                start = a["start"] if a.get("start") is not None else talk_cursor
                a["start"] = start
                a["end"] = start + ls.dur + 0.25
                a["_wav"] = str(wav); a["_ls"] = ls
                talk_cursor = a["end"] + 0.15
                captions.append((a["who"], a["text"], scene_offset + start, scene_offset + start + ls.dur))

        scene_dur = max([2.0] + [a["end"] for a in actions])

        # --- scene audio track ---
        track = np.zeros(int(scene_dur * sr) + sr, dtype="float32")
        for a in actions:
            if a.get("do") == "talk":
                w, _ = sf.read(a["_wav"])
                w = np.asarray(w, dtype="float32")
                st = int(a["start"] * sr)
                track[st:st + len(w)] += w[:len(track) - st]
        scene_wav = work / "audio" / f"scene_{si:03d}.wav"
        sf.write(str(scene_wav), track[:int(scene_dur * sr)], sr)

        # --- render frames ---
        total = int(scene_dur * fps)
        tmp = tempfile.mkdtemp()
        try:
            for f in range(total):
                t = f / fps
                frame = bg.copy()
                for cid, cinfo in present.items():
                    ch = chars.get(cid)
                    if ch is None:
                        continue
                    pos = cinfo.get("pos", [0.5, 0.96])
                    x_frac, ground_frac = float(pos[0]), float(pos[1])
                    ground_y = ground_frac * H
                    char_h = float(cinfo.get("scale", 1.0)) * 0.72 * H
                    facing = cinfo.get("facing", "right")
                    phase_off = (hash(cid) % 7) * 0.5

                    base = motion.idle(t, phase_off)
                    angles = dict(base["angles"]); bob = base["bob"]; mouth = "closed"
                    x_cur = x_frac

                    for a in actions:
                        if a.get("who") != cid:
                            continue
                        if not (a["start"] <= t < a.get("end", a["start"])):
                            continue
                        do = a.get("do"); lt = t - a["start"]
                        if do in ("walk", "enter"):
                            ph = lt * motion.WALK_RATE
                            w = motion.walk(ph); angles.update(w["angles"]); bob = w["bob"]
                            if do == "enter":
                                dur = max(0.3, a["end"] - a["start"])
                                frm = a.get("from", "left")
                                start_x = -0.18 if frm == "left" else 1.18
                                x_cur = start_x + (x_frac - start_x) * min(1.0, lt / dur)
                                facing = "right" if frm == "left" else "left"
                        elif do == "wave":
                            angles.update(motion.wave(lt))
                        elif do == "point":
                            angles.update(motion.point(a.get("side", "right")))
                        elif do == "jump":
                            dur = max(0.3, a["end"] - a["start"])
                            bob += motion.jump_bob(lt / dur)
                        elif do == "talk":
                            mouth = a["_ls"].mouth_at(lt)

                    eye = motion.blink_state(t + phase_off)
                    pose = {"angles": angles, "mouth": mouth, "eye": eye}
                    ch.place(frame, pose, x_cur, ground_y, char_h, facing=facing, bob=bob)
                frame.convert("RGB").save(Path(tmp) / f"f_{f:05d}.png")

            clip = clips_dir / f"clip_{si:03d}.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-framerate", str(fps), "-i", str(Path(tmp) / "f_%05d.png"),
                 "-i", str(scene_wav),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                 "-c:a", "aac", "-b:a", "192k", "-t", f"{scene_dur:.3f}", "-shortest",
                 "-movflags", "+faststart", str(clip)],
                check=True)
            clip_paths.append(clip)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        scene_offset += scene_dur
        print(f"[scene {si}] {scene_dur:.1f}s rendered")

    close = getattr(tts, "close", None)
    if close:
        close()

    out_path = Path(out) if out else (project_root / "dist" / f"{ep}.mp4")
    body = work / "body.mp4"
    concat_clips(clip_paths, body)
    music = (project_root / cfg.music.bed) if cfg.music.bed else None
    if music and music.exists():
        mix_music_bed(body, music, out_path, cfg.music.duck_db, sr)
    else:
        normalize_loudness(body, out_path, sr)

    srt = out_path.with_suffix(".srt")
    with open(srt, "w", encoding="utf-8") as fh:
        for i, (who, text, a, b) in enumerate(captions, 1):
            fh.write(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{text}\n\n")
    print(f"DONE -> {out_path}  (+ {srt.name})")
    return out_path
