"""Run inside Blender to dump a VRM/glB character's armature bones, mesh shape keys
(blendshapes) and material/texture info, so we can target them for posing + lip-sync.

Usage (from a normal shell):
  blender --background --python scripts/blender_inspect.py -- <path-to.vrm-or-.glb> <out.txt>

A .vrm is glTF under the hood; we copy/rename to .glb and use Blender's built-in importer
(no VRM add-on needed).
"""
import sys
import shutil
from pathlib import Path

import bpy


def argv_after_dashes():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main():
    args = argv_after_dashes()
    src = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else (src.with_suffix(".inspect.txt"))

    # fresh scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # vrm -> glb so the gltf importer accepts the extension
    glb = src
    if src.suffix.lower() == ".vrm":
        glb = src.with_suffix(".glb")
        if not glb.exists():
            shutil.copy(src, glb)
    bpy.ops.import_scene.gltf(filepath=str(glb))

    lines = []
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    lines.append(f"OBJECTS: {[o.name for o in bpy.data.objects]}")
    lines.append(f"ARMATURES: {[a.name for a in arms]}")
    for a in arms:
        lines.append(f"\n=== ARMATURE {a.name} bones ({len(a.data.bones)}) ===")
        for b in a.data.bones:
            lines.append(f"  {b.name}")
    lines.append(f"\nMESHES ({len(meshes)}):")
    for m in meshes:
        lines.append(f"  {m.name}  verts={len(m.data.vertices)}")
        sk = m.data.shape_keys
        if sk:
            lines.append(f"    shape_keys ({len(sk.key_blocks)}):")
            for kb in sk.key_blocks:
                lines.append(f"      {kb.name}")
        mats = [ms.material.name for ms in m.material_slots if ms.material]
        if mats:
            lines.append(f"    materials: {mats}")

    out.write_text("\n".join(lines), encoding="utf-8")
    print("WROTE_INSPECT:", out)


if __name__ == "__main__":
    main()
