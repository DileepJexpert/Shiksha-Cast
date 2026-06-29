"""Render a short ANIMATED test of the VRoid character (idle breathing + eased wave +
talking mouth + blink) to transparent PNG frames. Proves the 3D motion pipeline.

Usage:
  blender -b --python scripts/blender_animate.py -- <vrm> <out_frames_dir> <fps> <seconds>
"""
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


def envelope(lt, dur, ramp=0.5):
    ramp = min(ramp, dur / 2.0) if dur > 0 else ramp
    if ramp <= 0:
        return 1.0
    return min(smooth(lt / ramp), smooth((dur - lt) / ramp))


def import_vrm(src):
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
    # softer, balanced lighting (no more wash-out)
    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1, 1, 1, 1)
        bg.inputs[1].default_value = 0.45
    s1 = bpy.data.lights.new("Sun", "SUN"); s1.energy = 1.8
    o1 = bpy.data.objects.new("Sun", s1); bpy.context.collection.objects.link(o1)
    o1.rotation_euler = (math.radians(55), 0, math.radians(35))
    s2 = bpy.data.lights.new("Fill", "SUN"); s2.energy = 0.7
    o2 = bpy.data.objects.new("Fill", s2); bpy.context.collection.objects.link(o2)
    o2.rotation_euler = (math.radians(75), 0, math.radians(210))


def bbox():
    mins = Vector((1e9,) * 3); maxs = Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type == "MESH":
            for c in o.bound_box:
                wv = o.matrix_world @ Vector(c)
                mins = Vector((min(mins[i], wv[i]) for i in range(3)))
                maxs = Vector((max(maxs[i], wv[i]) for i in range(3)))
    return mins, maxs


def add_camera(back=2.9, height=0.55):
    mins, maxs = bbox()
    center = (mins + maxs) * 0.5
    h = maxs.z - mins.z
    aim = Vector((center.x, center.y, mins.z + h * height))
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = Vector((center.x, mins.y - h * back, aim.z + h * 0.03))
    cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 50
    bpy.context.scene.camera = cam


def get_arm():
    return next(o for o in bpy.data.objects if o.type == "ARMATURE")


def face():
    m = bpy.data.objects.get("Face")
    return m if m and m.data.shape_keys else None


# rest pose: arms down at sides (from T-pose). R arm Z+ lowers; L arm mirror Z-.
REST = {
    "J_Bip_R_UpperArm": (0, 0, 70), "J_Bip_L_UpperArm": (0, 0, -70),
    "J_Bip_R_LowerArm": (0, 0, -10), "J_Bip_L_LowerArm": (0, 0, 10),
}


def set_pose(arm, t, fps):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
    pose = {k: list(v) for k, v in REST.items()}
    breathe = math.sin(t * 1.5)
    # gentle idle sway + breathing on arms/spine
    pose["J_Bip_R_UpperArm"][2] += 2.5 * breathe
    pose["J_Bip_L_UpperArm"][2] -= 2.5 * breathe
    pose.setdefault("J_Bip_C_Spine", [0, 0, 0])
    pose["J_Bip_C_Spine"][0] += 1.2 * breathe
    head = [2.0 * math.sin(t * 0.8), 3.0 * math.sin(t * 0.5), 0]
    # WAVE on the right arm from 1.0s..3.5s
    ws, we = 1.0, 3.5
    if ws <= t < we:
        e = envelope(t - ws, we - ws)
        sway = math.sin((t - ws) * 3.2)
        # raise: Z from +70 down-pose toward -55 up-pose; add hand wave on lower arm
        up_z = -55 + 8 * sway
        pose["J_Bip_R_UpperArm"][2] = 70 + (up_z - 70) * e
        pose["J_Bip_R_UpperArm"][0] = -10 * e
        pose["J_Bip_R_LowerArm"] = [0, 0, -10 + (-35 + 18 * sway) * e]
    for name, deg in pose.items():
        pb = arm.pose.bones.get(name)
        if pb:
            pb.rotation_euler = tuple(math.radians(d) for d in deg)
    return head


def set_face(t):
    fm = face()
    if not fm:
        return
    kb = fm.data.shape_keys.key_blocks
    for k in kb:
        if k.name != "Basis":
            k.value = 0.0
    # talking: open/close mouth on a lively pattern; happy expression during wave
    talk = max(0.0, math.sin(t * 9.0)) * 0.85
    if "Fcl_MTH_A" in kb:
        kb["Fcl_MTH_A"].value = talk
    if "Fcl_ALL_Joy" in kb:
        kb["Fcl_ALL_Joy"].value = 0.5
    # blink: quick close ~ every 2.7s
    ph = (t % 2.7)
    if ph > 2.55 and "Fcl_EYE_Close" in kb:
        kb["Fcl_EYE_Close"].value = 1.0


def main():
    a = argv()
    src = Path(a[0]).resolve(); out = Path(a[1]).resolve()
    fps = int(a[2]) if len(a) > 2 else 24
    secs = float(a[3]) if len(a) > 3 else 4.0
    out.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_vrm(src)
    setup([720, 960], 12)
    add_camera()
    arm = get_arm()
    head_bone = arm.pose.bones.get("J_Bip_C_Head")

    n = int(fps * secs)
    for i in range(n):
        t = i / fps
        head = set_pose(arm, t, fps)
        if head_bone:
            head_bone.rotation_mode = "XYZ"
            head_bone.rotation_euler = tuple(math.radians(d) for d in head)
        set_face(t)
        bpy.context.view_layer.update()
        bpy.context.scene.render.filepath = str(out / f"f{i:04d}.png")
        bpy.ops.render.render(write_still=True)
        if i % 10 == 0:
            print("FRAME", i, "/", n)
    print("DONE_FRAMES", n)


if __name__ == "__main__":
    main()
