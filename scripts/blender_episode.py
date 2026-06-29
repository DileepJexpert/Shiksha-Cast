"""Render an episode's 3D character frames (transparent, character only) from a job JSON.
One VRM import for the whole episode; per-frame pose (eased gestures) + lip-sync from
audio levels + blink/expression. Python side composites these over backgrounds.

job JSON:
{
  "vrm": "<path>", "fps": 30, "resolution": [720, 1280],
  "cam_back": 2.3, "cam_height": 0.52, "samples": 12,
  "out_root": "<dir>",                      # writes scene_%03d/f%05d.png
  "scenes": [ {"index": 1, "frames": 90, "actions": [ {do,start,end,side?,levels?} ] }, ... ]
}

Usage: blender -b --python scripts/blender_episode.py -- <job.json>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def smooth(e):
    e = 0.0 if e < 0 else (1.0 if e > 1 else e)
    return e * e * (3 - 2 * e)


def envelope(lt, dur, ramp=0.45):
    ramp = min(ramp, dur / 2.0) if dur > 0 else ramp
    return 1.0 if ramp <= 0 else min(smooth(lt / ramp), smooth((dur - lt) / ramp))


def mix(a, b, w):
    return a + (b - a) * w


# rest pose (degrees). Right arm: Z+ lowers, Z- raises. Left arm mirrored.
REST = {
    "J_Bip_R_UpperArm": [0, 0, 70], "J_Bip_L_UpperArm": [0, 0, -70],
    "J_Bip_R_LowerArm": [0, 0, -10], "J_Bip_L_LowerArm": [0, 0, 10],
}


def import_vrm(src):
    src = Path(src)
    glb = src
    if src.suffix.lower() == ".vrm":
        glb = src.with_suffix(".glb")
        if not glb.exists():
            shutil.copy(src, glb)
    bpy.ops.import_scene.gltf(filepath=str(glb))


def setup(res, samples):
    sc = bpy.context.scene
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    o = bpy.data.objects.get("Icosphere")
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.45
    s1 = bpy.data.lights.new("Sun", "SUN"); s1.energy = 1.8
    o1 = bpy.data.objects.new("Sun", s1); sc.collection.objects.link(o1)
    o1.rotation_euler = (math.radians(55), 0, math.radians(35))
    s2 = bpy.data.lights.new("Fill", "SUN"); s2.energy = 0.7
    o2 = bpy.data.objects.new("Fill", s2); sc.collection.objects.link(o2)
    o2.rotation_euler = (math.radians(75), 0, math.radians(210))


def bbox():
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type == "MESH":
            for c in o.bound_box:
                wv = o.matrix_world @ Vector(c)
                mn = Vector((min(mn[i], wv[i]) for i in range(3)))
                mx = Vector((max(mx[i], wv[i]) for i in range(3)))
    return mn, mx


def add_camera(back, height):
    mn, mx = bbox(); center = (mn + mx) * 0.5; h = mx.z - mn.z
    aim = Vector((center.x, center.y, mn.z + h * height))
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector((center.x, mn.y - h * back, aim.z + h * 0.03))
    cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 50; bpy.context.scene.camera = cam


def pose_for(actions, t):
    """Return (bones{name:[x,y,z]deg}, head[x,y,z], shapes{name:val})."""
    pose = {k: list(v) for k, v in REST.items()}
    breathe = math.sin(t * 1.5)
    pose["J_Bip_R_UpperArm"][2] += 2.5 * breathe
    pose["J_Bip_L_UpperArm"][2] -= 2.5 * breathe
    pose["J_Bip_C_Spine"] = [1.2 * breathe, 0, 0]
    head = [2.0 * math.sin(t * 0.8), 3.0 * math.sin(t * 0.5), 0]
    shapes = {}
    joy = 0.0
    for a in actions:
        s = a.get("start", 0.0); e = a.get("end", s)
        if not (s <= t < e):
            continue
        do = a.get("do"); lt = t - s; dur = max(0.3, e - s); env = envelope(lt, dur)
        if do == "talk":
            lv = a.get("levels") or []
            i = int(lt * a.get("fps", 30))
            level = lv[i] if 0 <= i < len(lv) else 0.0
            if level >= 0.08:
                shapes["Fcl_MTH_A"] = min(1.0, level * 1.5)
                shapes["Fcl_MTH_I"] = min(0.4, level * 0.4)
            else:
                shapes["Fcl_MTH_Close"] = 0.3
        elif do == "wave":
            sway = math.sin(lt * 3.2)
            pose["J_Bip_R_UpperArm"][2] = mix(70, -52 + 8 * sway, env)
            pose["J_Bip_R_UpperArm"][0] = mix(0, -12, env)
            pose["J_Bip_R_LowerArm"][2] = mix(-10, -35 + 18 * sway, env)
            joy = max(joy, 0.6 * env)
        elif do == "point":
            if a.get("side") == "left":
                pose["J_Bip_L_UpperArm"][2] = mix(-70, -4, env)
                pose["J_Bip_L_UpperArm"][0] = mix(0, -14, env)
            else:
                pose["J_Bip_R_UpperArm"][2] = mix(70, 4, env)
                pose["J_Bip_R_UpperArm"][0] = mix(0, -14, env)
        elif do == "point_up":
            pose["J_Bip_R_UpperArm"][2] = mix(70, -82, env)
        elif do == "cheer":
            lift = 6 * math.sin(lt * 3.0)
            pose["J_Bip_R_UpperArm"][2] = mix(70, -58 - lift, env)
            pose["J_Bip_L_UpperArm"][2] = mix(-70, 58 + lift, env)
            joy = max(joy, 0.8 * env)
        elif do in ("enter", "walkto"):
            stride = math.sin(lt * 5.0)
            pose["J_Bip_R_UpperLeg"] = [12 * stride, 0, 0]
            pose["J_Bip_L_UpperLeg"] = [-12 * stride, 0, 0]
            pose["J_Bip_R_UpperArm"][0] += 8 * stride
            pose["J_Bip_L_UpperArm"][0] -= 8 * stride
    if joy > 0:
        shapes["Fcl_ALL_Joy"] = joy
    # blink ~ every 2.7s
    if (t % 2.7) > 2.55:
        shapes["Fcl_EYE_Close"] = 1.0
    return pose, head, shapes


def apply(arm, face_kb, pose, head, shapes):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"; pb.rotation_euler = (0, 0, 0)
    for name, deg in pose.items():
        pb = arm.pose.bones.get(name)
        if pb:
            pb.rotation_euler = tuple(math.radians(d) for d in deg)
    hb = arm.pose.bones.get("J_Bip_C_Head")
    if hb:
        hb.rotation_mode = "XYZ"; hb.rotation_euler = tuple(math.radians(d) for d in head)
    if face_kb:
        for k in face_kb:
            if k.name != "Basis":
                k.value = 0.0
        for name, val in shapes.items():
            if name in face_kb:
                face_kb[name].value = float(val)


def main():
    job = json.loads(Path(argv()[0]).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_vrm(job["vrm"])
    setup(job.get("resolution", [720, 1280]), job.get("samples", 12))
    add_camera(job.get("cam_back", 2.3), job.get("cam_height", 0.52))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    fm = bpy.data.objects.get("Face")
    face_kb = fm.data.shape_keys.key_blocks if fm and fm.data.shape_keys else None
    fps = job.get("fps", 30)
    out_root = Path(job["out_root"]); out_root.mkdir(parents=True, exist_ok=True)

    for sc in job["scenes"]:
        si = sc["index"]; n = sc["frames"]
        for a in sc.get("actions", []):
            a.setdefault("fps", fps)
        sdir = out_root / f"scene_{si:03d}"; sdir.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            t = i / fps
            pose, head, shapes = pose_for(sc.get("actions", []), t)
            apply(arm, face_kb, pose, head, shapes)
            bpy.context.view_layer.update()
            bpy.context.scene.render.filepath = str(sdir / f"f{i:05d}.png")
            bpy.ops.render.render(write_still=True)
        print(f"SCENE_DONE {si} ({n} frames)")
    print("EPISODE_FRAMES_DONE")


if __name__ == "__main__":
    main()
