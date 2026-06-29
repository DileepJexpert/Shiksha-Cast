"""Import a VRoid VRM (as glTF) and render one or more still POSES to transparent PNGs.
Used both for calibration (find which axis raises an arm) and for final frame rendering.

Spec JSON:
{
  "resolution": [900, 1200],
  "samples": 16,
  "cam_back": 3.2,          # camera distance multiplier (optional)
  "cam_height": 0.55,       # fraction of char height to aim at (optional)
  "frames": [
    {"name": "rest", "bones": {}, "shapes": {}},
    {"name": "armX45", "bones": {"J_Bip_R_UpperArm": [45, 0, 0]}},
    ...
  ]
}
bones: degrees [x,y,z] applied as local euler. shapes: {"Fcl_MTH_A": 0.8, ...} 0..1.

Usage:
  blender -b --python scripts/blender_pose_render.py -- <vrm> <out_dir> <spec.json>
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


def import_vrm(src: Path):
    glb = src
    if src.suffix.lower() == ".vrm":
        glb = src.with_suffix(".glb")
        if not glb.exists():
            shutil.copy(src, glb)
    bpy.ops.import_scene.gltf(filepath=str(glb))


def scene_setup(res, samples):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in \
        [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    # remove stray helper objects
    for n in ("Icosphere",):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)


def add_lights_world():
    # soft bright world
    world = bpy.data.worlds.new("W") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1, 1, 1, 1)
        bg.inputs[1].default_value = 0.7
    # key sun
    sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_d); bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(55), 0, math.radians(30))
    # fill sun from front
    f_d = bpy.data.lights.new("Fill", "SUN"); f_d.energy = 1.2
    fill = bpy.data.objects.new("Fill", f_d); bpy.context.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(80), 0, math.radians(200))


def char_bbox():
    mins = Vector((1e9, 1e9, 1e9)); maxs = Vector((-1e9, -1e9, -1e9))
    for o in bpy.data.objects:
        if o.type == "MESH":
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                mins = Vector((min(mins[i], w[i]) for i in range(3)))
                maxs = Vector((max(maxs[i], w[i]) for i in range(3)))
    return mins, maxs


def add_camera(cam_back, cam_height):
    mins, maxs = char_bbox()
    center = (mins + maxs) * 0.5
    height = maxs.z - mins.z
    aim = Vector((center.x, center.y, mins.z + height * cam_height))
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
    # place in front (-Y) and slightly up
    dist = height * cam_back
    cam.location = Vector((center.x, mins.y - dist, aim.z + height * 0.04))
    # point at aim
    direction = aim - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = 50
    bpy.context.scene.camera = cam


def get_armature():
    return next(o for o in bpy.data.objects if o.type == "ARMATURE")


def face_mesh():
    m = bpy.data.objects.get("Face")
    return m if m and m.data.shape_keys else None


def apply_pose(arm, bones):
    # reset all pose bones
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    for name, deg in bones.items():
        pb = arm.pose.bones.get(name)
        if pb:
            pb.rotation_euler = tuple(math.radians(d) for d in deg)


def apply_shapes(shapes):
    fm = face_mesh()
    if not fm:
        return
    kb = fm.data.shape_keys.key_blocks
    for k in kb:
        if k.name != "Basis":
            k.value = 0.0
    for name, val in shapes.items():
        if name in kb:
            kb[name].value = float(val)


def main():
    a = argv()
    src, out_dir, spec_path = Path(a[0]).resolve(), Path(a[1]).resolve(), Path(a[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(spec_path).read_text())

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_vrm(src)
    scene_setup(spec.get("resolution", [900, 1200]), spec.get("samples", 16))
    add_lights_world()
    add_camera(spec.get("cam_back", 3.2), spec.get("cam_height", 0.55))
    arm = get_armature()

    for fr in spec["frames"]:
        apply_pose(arm, fr.get("bones", {}))
        apply_shapes(fr.get("shapes", {}))
        bpy.context.view_layer.update()
        fp = out_dir / (fr["name"] + ".png")
        bpy.context.scene.render.filepath = str(fp)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", fr["name"], "->", fp, "exists=", fp.exists())


if __name__ == "__main__":
    main()
