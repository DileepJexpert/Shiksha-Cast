"""3D cartoon episode builder. Same scenes.yaml + TTS + audio + captions + music as the
2D builder, but the CHARACTER is a VRoid VRM rendered in Blender (posed + lip-synced),
composited over the 2D backgrounds. One Blender invocation renders all scene frames.

A character id is 3D if assets/cartoon/characters3d/<id>/*.vrm exists.

CLI: cartoon-build-3d -c <episode>
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from PIL import Image

from shiksha_cast.assemble import concat_clips, mix_music_bed, normalize_loudness
from shiksha_cast.cartoon.build import (_bg, _schedule, _srt_time, _lerp)
from shiksha_cast.cartoon.lipsync import Lipsync
from shiksha_cast.config import load_channel_config
from shiksha_cast.tts.kokoro import KokoroTTSProvider

CHARS3D = "assets/cartoon/characters3d"


def find_vrm(project_root: Path, cid: str):
    d = project_root / CHARS3D / cid
    if d.is_dir():
        for p in sorted(d.glob("*.vrm")):
            return p
    return None


def blender_exe():
    for base in (Path("C:/Users/dileepkm/BlenderPortable"),
                 Path("C:/Program Files/Blender Foundation")):
        if base.exists():
            for p in base.rglob("blender.exe"):
                return str(p)
    return "blender"


def _smooth(e):
    e = 0.0 if e < 0 else (1.0 if e > 1 else e)
    return e * e * (3 - 2 * e)


def x_at(actions, t, base_x):
    x = base_x
    for a in actions:
        s = a.get("start", 0.0); e = a.get("end", s)
        if not (s <= t < e):
            continue
        do = a.get("do"); dur = max(0.3, e - s); p = _smooth(min(1.0, (t - s) / dur))
        if do == "enter":
            sx = -0.2 if a.get("from", "left") == "left" else 1.2
            x = sx + (base_x - sx) * p
        elif do == "walkto":
            to = float(a.get("to", base_x)); x = base_x + (to - base_x) * p
    return x


def ref_feet(frame0_path):
    im = Image.open(frame0_path).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if not bb:
        return im.width / 2, im.height, im.height * 0.8, im.size
    l, top, r, bot = bb
    return (l + r) / 2, bot, (bot - top), im.size


def build_episode_3d(scene_path: str, project_root: Path, out: str | None = None) -> Path:
    spec = yaml.safe_load(open(scene_path, encoding="utf-8"))
    cfg = load_channel_config(project_root)
    W, H = cfg.resolution
    fps = int(spec.get("fps", cfg.fps))
    sr = cfg.voice.sample_rate
    ep = spec.get("episode") or Path(scene_path).parent.name
    cast = spec.get("cast", {})

    # one 3D character supported (the first cast id with a .vrm)
    cid = next(iter(cast), None)
    vrm = find_vrm(project_root, cid) if cid else None
    if not vrm:
        raise SystemExit(f"No VRM for cast id '{cid}' under {CHARS3D}/{cid}/")

    work = project_root / "build" / ep
    (work / "audio").mkdir(parents=True, exist_ok=True)
    clips_dir = work / "clips"; clips_dir.mkdir(parents=True, exist_ok=True)
    char_root = work / "char3d"
    if char_root.exists():
        shutil.rmtree(char_root, ignore_errors=True)
    tts = KokoroTTSProvider()

    captions = []
    scene_offset = 0.0
    line_no = 0
    scenes_meta = []   # per scene: dict for compositing
    job_scenes = []    # per scene: for blender

    for si, scene in enumerate(spec.get("scenes", []), 1):
        actions = _schedule(scene)
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
                a["start"] = start; a["end"] = start + ls.dur + 0.25
                a["_wav"] = str(wav); a["_ls"] = ls
                talk_cursor = a["end"] + 0.15
                captions.append((a["who"], a["text"], scene_offset + start, scene_offset + start + ls.dur))
        scene_dur = max([2.0] + [a["end"] for a in actions])
        n = int(scene_dur * fps)

        track = np.zeros(int(scene_dur * sr) + sr, dtype="float32")
        for a in actions:
            if a.get("do") == "talk":
                w, _ = sf.read(a["_wav"]); w = np.asarray(w, dtype="float32")
                st = int(a["start"] * sr); track[st:st + len(w)] += w[:len(track) - st]
        scene_wav = work / "audio" / f"scene_{si:03d}.wav"
        sf.write(str(scene_wav), track[:int(scene_dur * sr)], sr)

        # serialize actions for blender (only this char's actions)
        bactions = []
        for a in actions:
            if a.get("who") not in (None, cid):
                continue
            ba = {"do": a.get("do"), "start": float(a.get("start", 0.0)),
                  "end": float(a.get("end", a.get("start", 0.0)))}
            if a.get("side"):
                ba["side"] = a["side"]
            if a.get("from"):
                ba["from"] = a["from"]
            if a.get("do") == "talk":
                ba["levels"] = a["_ls"].levels.tolist()
            bactions.append(ba)
        job_scenes.append({"index": si, "frames": n, "actions": bactions})

        cinfo = next((c for c in scene.get("characters", []) if c["id"] == cid),
                     {"pos": [0.3, 0.99], "scale": 1.0})
        scenes_meta.append({
            "index": si, "frames": n, "dur": scene_dur, "scene_wav": str(scene_wav),
            "bg": scene.get("background"), "pos": cinfo.get("pos", [0.3, 0.99]),
            "scale": float(cinfo.get("scale", 1.0)), "cam": scene.get("camera") or {},
            "transition": scene.get("transition") or {}, "props": scene.get("props", []),
            "actions": actions,
        })
        scene_offset += scene_dur

    close = getattr(tts, "close", None)
    if close:
        close()

    # --- render ALL character frames in one Blender run ---
    job = {"vrm": str(vrm), "fps": fps, "resolution": [720, 1280],
           "cam_back": 2.25, "cam_height": 0.5, "samples": 12,
           "out_root": str(char_root), "scenes": job_scenes}
    job_path = work / "blender_job.json"
    job_path.write_text(json.dumps(job))
    print(f"[3d] rendering {sum(s['frames'] for s in job_scenes)} character frames in Blender...")
    subprocess.run([blender_exe(), "-b", "--python",
                    str(project_root / "scripts" / "blender_episode.py"), "--", str(job_path)],
                   check=True)

    # --- composite per scene + encode clips ---
    clip_paths = []
    for sm in scenes_meta:
        si = sm["index"]
        bg = _bg(project_root, sm["bg"], W, H)
        sdir = char_root / f"scene_{si:03d}"
        f0 = sdir / "f00000.png"
        fcx, fbot, fch, fsize = ref_feet(f0)
        target_h = sm["scale"] * 0.92 * H
        s = target_h / max(1.0, fch)
        base_x = float(sm["pos"][0]); ground_y = float(sm["pos"][1]) * H
        tmp = tempfile.mkdtemp()
        try:
            for i in range(sm["frames"]):
                t = i / fps
                frame = bg.copy()
                self_draw_props(frame, project_root, sm["props"], t, sm["dur"], W, H, "back")
                ch = Image.open(sdir / f"f{i:05d}.png").convert("RGBA")
                chs = ch.resize((max(1, int(ch.width * s)), max(1, int(ch.height * s))), Image.LANCZOS)
                xc = x_at(sm["actions"], t, base_x)
                px = int(xc * W - fcx * s)
                py = int(ground_y - fbot * s)
                frame.alpha_composite(chs, (px, py))
                self_draw_props(frame, project_root, sm["props"], t, sm["dur"], W, H, "front")
                cam = sm["cam"]
                if cam:
                    pr = t / sm["dur"] if sm["dur"] else 0.0
                    z = _lerp(cam["zoom"][0], cam["zoom"][1], pr) if cam.get("zoom") else 1.0
                    panx = _lerp(cam["pan"][0], cam["pan"][1], pr) if cam.get("pan") else 0.0
                    if z != 1.0 or panx:
                        cw, chh = W / z, H / z
                        x0 = min(max((W - cw) / 2 + panx * W, 0), W - cw); y0 = (H - chh) / 2
                        frame = frame.crop((int(x0), int(y0), int(x0 + cw), int(y0 + chh))).resize((W, H), Image.LANCZOS)
                frame.convert("RGB").save(str(Path(tmp) / f"f_{i:05d}.png"))

            clip = clips_dir / f"clip_{si:03d}.mp4"
            trans = sm["transition"]; vf = []
            if trans.get("in"):
                vf.append(f"fade=t=in:st=0:d={float(trans['in'])}")
            if trans.get("out"):
                vf.append(f"fade=t=out:st={max(0.0, sm['dur'] - float(trans['out'])):.3f}:d={float(trans['out'])}")
            cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-framerate", str(fps), "-i", str(Path(tmp) / "f_%05d.png"), "-i", sm["scene_wav"]]
            if vf:
                cmd += ["-vf", ",".join(vf)]
            cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{sm['dur']:.3f}", "-shortest",
                    "-movflags", "+faststart", str(clip)]
            subprocess.run(cmd, check=True)
            clip_paths.append(clip)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"[scene {si}] {sm['dur']:.1f}s composited")

    out_path = Path(out) if out else (project_root / "dist" / f"{ep}.3d.mp4")
    body = work / "body3d.mp4"
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


_PROPS3D: dict = {}


def self_draw_props(frame, project_root, props, t, dur, W, H, which):
    import math
    for p in props:
        if p.get("z", "front") != which:
            continue
        start = float(p.get("start", 0.0)); end = float(p.get("end", dur))
        if not (start <= t < end):
            continue
        ap = Path(p["asset"])
        path = ap if (ap.is_absolute() or ap.exists()) else (project_root / "assets" / "cartoon" / "props" / p["asset"])
        if not path.exists():
            continue
        im = _PROPS3D.get(str(path))
        if im is None:
            im = Image.open(path).convert("RGBA"); _PROPS3D[str(path)] = im
        lt = t - start
        sc = float(p.get("scale", 0.12)) * H / im.height
        if p.get("anim") == "pop":
            sc *= min(1.0, lt / 0.3)
        w_, h_ = max(1, int(im.width * sc)), max(1, int(im.height * sc))
        pim = im.resize((w_, h_), Image.LANCZOS)
        px = int(p["pos"][0] * W - w_ / 2); py = int(p["pos"][1] * H - h_ / 2)
        if p.get("anim") in ("float", "bob"):
            py += int(8 * math.sin(lt * 3))
        frame.alpha_composite(pim, (px, py))
