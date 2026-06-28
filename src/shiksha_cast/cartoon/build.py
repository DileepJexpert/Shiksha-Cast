"""Cutout cartoon episode builder.

Parses a scenes.yaml, synthesizes per-line narration (local Kokoro, per-character
voice), schedules a timeline, renders frames (poses from the motion library +
amplitude lip-sync + blinks), encodes per-scene clips, then concatenates with the
music bed, masters to -14 LUFS, and writes captions. No GPU at runtime.
"""
from __future__ import annotations

import math
import os
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


def _is_adv(d: Path) -> bool:
    """Advanced skeletal rig = has separated 2-bone limb parts."""
    return (d / "upper_arm_left.png").exists()


def _lerp(a, b, t):
    return a + (b - a) * t


def _bg(project_root: Path, name, W, H):
    if name:
        p = Path(name)
        cand = p if (p.is_absolute() or p.exists()) else (project_root / BG_DIR / name)
        if cand.exists():
            return Image.open(cand).convert("RGBA").resize((W, H))
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


# ---- per-frame rendering (module-level so worker processes can pickle it) ----
def _mouth_from_levels(levels, fps, lt):
    i = int(lt * fps)
    if i < 0 or i >= len(levels):
        return "closed"
    v = levels[i]
    return "closed" if v < 0.12 else ("half" if v < 0.45 else "open")


def _viseme(levels, fps, lt):
    """Amplitude -> one of the 9 mouth visemes (X rest .. D wide)."""
    i = int(lt * fps)
    if i < 0 or i >= len(levels):
        return "X"
    v = levels[i]
    if v < 0.08:
        return "X"
    if v < 0.18:
        return "B"
    if v < 0.33:
        return "C"
    if v < 0.55:
        return "E"
    return "D"


def _adv_pose(cid, actions, t, fps, phase_off, x_frac, facing0):
    """Build a rig2 (skeletal) pose for an advanced character from active actions."""
    sway = math.sin(t * 1.4 + phase_off)
    pose = {"arm_left": (6 * sway, 0), "arm_right": (-6 * sway, 0),
            "leg_left": (0, 0), "leg_right": (0, 0), "head": 1.5 * sway,
            "eyes": "open", "mouth": "X", "brows": "neutral"}
    bob = 0.0; x_cur = x_frac; facing = facing0
    for a in actions:
        if a.get("who") != cid or not (a["start"] <= t < a.get("end", a["start"])):
            continue
        do = a.get("do"); lt = t - a["start"]
        if do == "talk":
            pose["mouth"] = _viseme(a["levels"], fps, lt)
        elif do == "wave":
            pose["arm_right"] = (150 + 6 * math.sin(lt * 9), 6); pose["eyes"] = "happy"; pose["brows"] = "happy"
        elif do == "point":
            if a.get("side") == "left":
                pose["arm_left"] = (-95, -6)
            else:
                pose["arm_right"] = (95, 6)
        elif do == "point_up":
            pose["arm_right"] = (150, 6)
        elif do == "cheer":
            pose["arm_left"] = (-150, -6); pose["arm_right"] = (150, 6)
            pose["eyes"] = "happy"; pose["brows"] = "happy"; pose["mouth"] = "D"
        elif do == "sad":
            pose["brows"] = "sad"
        elif do == "surprise":
            pose["brows"] = "surprised"
        elif do in ("enter", "walkto"):
            dur = max(0.3, a["end"] - a["start"])
            if do == "enter":
                frm = a.get("from", "left"); sx = -0.18 if frm == "left" else 1.18
                x_cur = sx + (x_frac - sx) * min(1.0, lt / dur); facing = "right" if frm == "left" else "left"
            else:
                to = float(a.get("to", x_frac)); x_cur = x_frac + (to - x_frac) * min(1.0, lt / dur)
                facing = "right" if to >= x_frac else "left"
            sw = 16 * math.sin(lt * 8)
            pose["leg_left"] = (sw, 0); pose["leg_right"] = (-sw, 0); bob = abs(math.sin(lt * 8)) * 7
        elif do == "jump":
            bob += motion.jump_bob(lt / max(0.3, a["end"] - a["start"])); pose["eyes"] = "happy"
    if pose["eyes"] == "open" and motion.blink_state(t + phase_off) == "closed":
        pose["eyes"] = "closed"
    return pose, x_cur, facing, bob


_PROP_CACHE: dict = {}


def _prop_img(path):
    im = _PROP_CACHE.get(path)
    if im is None:
        im = Image.open(path).convert("RGBA")
        _PROP_CACHE[path] = im
    return im


def _draw_props(frame, ctx, t, which):
    W, H = ctx["W"], ctx["H"]
    for p in ctx.get("props", []):
        if p.get("z", "front") != which or not (p["start"] <= t < p["end"]):
            continue
        im = _prop_img(p["path"]); lt = t - p["start"]
        sc = p.get("scale", 0.12) * H / im.height
        if p.get("anim") == "pop":
            sc *= min(1.0, lt / 0.3)
        w_, h_ = max(1, int(im.width * sc)), max(1, int(im.height * sc))
        pim = im.resize((w_, h_), Image.LANCZOS)
        px = int(p["pos"][0] * W - w_ / 2)
        py = int(p["pos"][1] * H - h_ / 2)
        if p.get("anim") == "float":
            py += int(8 * math.sin(lt * 3))
        frame.alpha_composite(pim, (px, py))


def _build_frame(t, ctx, cache):
    W, H, fps, scene_dur = ctx["W"], ctx["H"], ctx["fps"], ctx["scene_dur"]
    frame = cache["_bg"].copy()
    _draw_props(frame, ctx, t, "back")
    adv = set(ctx.get("adv", []))
    for cinfo in ctx["present"]:
        cid = cinfo["id"]; ch = cache.get(cid)
        if ch is None:
            continue
        pos = cinfo.get("pos", [0.5, 0.96])
        x_frac, ground_y = float(pos[0]), float(pos[1]) * H
        char_h = float(cinfo.get("scale", 1.0)) * 0.72 * H
        facing = cinfo.get("facing", "right"); phase_off = (hash(cid) % 7) * 0.5
        if cid in adv:
            pose, x_cur, facing, bob = _adv_pose(cid, ctx["actions"], t, fps, phase_off, x_frac, facing)
            ch.place(frame, pose, x_cur, ground_y, char_h, facing=facing, bob=bob)
            continue
        base = motion.idle(t, phase_off)
        angles = dict(base["angles"]); bob = base["bob"]; mouth = "closed"; x_cur = x_frac
        for a in ctx["actions"]:
            if a.get("who") != cid or not (a["start"] <= t < a.get("end", a["start"])):
                continue
            do = a.get("do"); lt = t - a["start"]
            if do in ("walk", "enter"):
                w = motion.walk(lt * motion.WALK_RATE); angles.update(w["angles"]); bob = w["bob"]
                if do == "enter":
                    dur = max(0.3, a["end"] - a["start"]); frm = a.get("from", "left")
                    sx = -0.18 if frm == "left" else 1.18
                    x_cur = sx + (x_frac - sx) * min(1.0, lt / dur)
                    facing = "right" if frm == "left" else "left"
            elif do == "wave":
                angles.update(motion.wave(lt))
            elif do == "point":
                angles.update(motion.point(a.get("side", "right")))
            elif do == "jump":
                bob += motion.jump_bob(lt / max(0.3, a["end"] - a["start"]))
            elif do == "cheer":
                angles.update(motion.cheer(lt))
            elif do == "hold":
                angles.update(motion.hold(a.get("side", "right")))
            elif do == "walkto":
                dur = max(0.3, a["end"] - a["start"])
                w = motion.walk(lt * motion.WALK_RATE); angles.update(w["angles"]); bob = w["bob"]
                to = float(a.get("to", x_frac))
                x_cur = x_frac + (to - x_frac) * min(1.0, lt / dur)
                facing = "right" if to >= x_frac else "left"
            elif do == "talk":
                mouth = _mouth_from_levels(a["levels"], fps, lt)
        eye = motion.blink_state(t + phase_off)
        ch.place(frame, {"angles": angles, "mouth": mouth, "eye": eye},
                 x_cur, ground_y, char_h, facing=facing, bob=bob)
    _draw_props(frame, ctx, t, "front")
    cam = ctx.get("cam") or {}
    if cam:
        pr = t / scene_dur if scene_dur else 0.0
        z = _lerp(cam["zoom"][0], cam["zoom"][1], pr) if cam.get("zoom") else 1.0
        panx = _lerp(cam["pan"][0], cam["pan"][1], pr) if cam.get("pan") else 0.0
        if z != 1.0 or panx:
            cw, chh = W / z, H / z
            x0 = min(max((W - cw) / 2 + panx * W, 0), W - cw); y0 = (H - chh) / 2
            frame = frame.crop((int(x0), int(y0), int(x0 + cw), int(y0 + chh))).resize((W, H), Image.LANCZOS)
    return frame


_WORK: dict = {}


def _worker_init(char_dirs, adv):
    from shiksha_cast.cartoon.character import Character
    from shiksha_cast.cartoon.rig2 import SkeletalCharacter
    _WORK["chars"] = {cid: (SkeletalCharacter(d) if cid in adv else Character(d))
                      for cid, d in char_dirs.items()}
    _WORK["bgs"] = {}


def _worker_frames(args):
    tmp, idxs, ctx = args
    bgp = ctx["bg_path"]
    bg = _WORK["bgs"].get(bgp)
    if bg is None:
        bg = Image.open(bgp).convert("RGBA")
        _WORK["bgs"][bgp] = bg
    cache = dict(_WORK["chars"])
    cache["_bg"] = bg
    for f in idxs:
        _build_frame(f / ctx["fps"], ctx, cache).convert("RGB").save(str(Path(tmp) / f"f_{f:05d}.png"))
    return len(idxs)


def build_episode(scene_path: str, project_root: Path, out: str | None = None) -> Path:
    spec = yaml.safe_load(open(scene_path, encoding="utf-8"))
    cfg = load_channel_config(project_root)
    W, H = cfg.resolution
    fps = int(spec.get("fps", cfg.fps))
    sr = cfg.voice.sample_rate
    ep = spec.get("episode") or Path(scene_path).parent.name
    cast = spec.get("cast", {})

    chars = {}
    adv: set = set()
    for name in cast:
        d = project_root / CHARS_DIR / name
        if _is_adv(d):
            from shiksha_cast.cartoon.rig2 import SkeletalCharacter
            chars[name] = SkeletalCharacter(d); adv.add(name)
        elif (d / "rig.json").exists():
            chars[name] = Character(d)

    work = project_root / "build" / ep
    (work / "audio").mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"; clips_dir.mkdir(parents=True, exist_ok=True)
    tts = KokoroTTSProvider()

    clip_paths, captions = [], []
    scene_offset = 0.0
    line_no = 0

    # One persistent worker pool for the whole episode (loads the cast once).
    workers = min((os.cpu_count() or 2), 12)
    pool = None
    if workers >= 2:
        try:
            from concurrent.futures import ProcessPoolExecutor
            all_dirs = {cid: str(project_root / CHARS_DIR / cid) for cid in chars}
            pool = ProcessPoolExecutor(max_workers=workers, initializer=_worker_init, initargs=(all_dirs, adv))
        except Exception as e:  # noqa: BLE001
            print(f"[no parallel pool -> sequential: {e}]")
            pool = None

    for si, scene in enumerate(spec.get("scenes", []), 1):
        bg = _bg(project_root, scene.get("background"), W, H)
        present = {c["id"]: c for c in scene.get("characters", [])}
        actions = _schedule(scene)
        cam = scene.get("camera") or {}

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

        # --- render frames (multi-core when worthwhile, else sequential) ---
        char_dirs = {cid: str(project_root / CHARS_DIR / cid) for cid in present if cid in chars}
        bg_path = str(clips_dir / f"_bg_{si:03d}.png")
        bg.save(bg_path)
        actions_ser = []
        for a in actions:
            aa = {k: v for k, v in a.items() if not k.startswith("_")}
            if a.get("do") == "talk":
                aa["levels"] = a["_ls"].levels.tolist()
            actions_ser.append(aa)
        props_ser = []
        for p in scene.get("props", []):
            ap = Path(p["asset"])
            path = ap if (ap.is_absolute() or ap.exists()) else (project_root / "assets" / "cartoon" / "props" / p["asset"])
            if not path.exists():
                continue
            props_ser.append({"path": str(path), "pos": p.get("pos", [0.5, 0.5]),
                              "scale": float(p.get("scale", 0.12)), "anim": p.get("anim", "none"),
                              "z": p.get("z", "front"), "start": float(p.get("start", 0.0)),
                              "end": float(p.get("end", scene_dur))})
        ctx = {"present": [{**c} for c in scene.get("characters", []) if c["id"] in chars],
               "actions": actions_ser, "props": props_ser, "adv": list(adv), "W": W, "H": H, "fps": fps,
               "scene_dur": scene_dur, "cam": cam, "bg_path": bg_path}
        total = int(scene_dur * fps)
        tmp = tempfile.mkdtemp()
        try:
            rendered = False
            if pool is not None and total >= workers * 4:
                try:
                    chunks = [list(range(i, total, workers)) for i in range(workers)]
                    list(pool.map(_worker_frames, [(tmp, c, ctx) for c in chunks]))
                    rendered = True
                except Exception as e:  # noqa: BLE001
                    print(f"[parallel render failed -> sequential: {e}]")
            if not rendered:
                cache = {cid: chars[cid] for cid in char_dirs}
                cache["_bg"] = bg
                for f in range(total):
                    _build_frame(f / fps, ctx, cache).convert("RGB").save(str(Path(tmp) / f"f_{f:05d}.png"))

            clip = clips_dir / f"clip_{si:03d}.mp4"
            trans = scene.get("transition") or {}
            vf = []
            if trans.get("in"):
                vf.append(f"fade=t=in:st=0:d={float(trans['in'])}")
            if trans.get("out"):
                vf.append(f"fade=t=out:st={max(0.0, scene_dur - float(trans['out'])):.3f}:d={float(trans['out'])}")
            cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-framerate", str(fps), "-i", str(Path(tmp) / "f_%05d.png"),
                   "-i", str(scene_wav)]
            if vf:
                cmd += ["-vf", ",".join(vf)]
            cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{scene_dur:.3f}", "-shortest",
                    "-movflags", "+faststart", str(clip)]
            subprocess.run(cmd, check=True)
            clip_paths.append(clip)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        scene_offset += scene_dur
        print(f"[scene {si}] {scene_dur:.1f}s rendered")

    if pool is not None:
        pool.shutdown()
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
