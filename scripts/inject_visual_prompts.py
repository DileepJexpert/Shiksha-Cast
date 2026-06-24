"""Add a `visual_prompt` to every slide in each episode's script.yaml, taken from
the "Visual:" line in its SLIDES.md. This enables the `ai-build` path (SDXL image
generation + Ken Burns / parallax motion) for richer, illustrated slides.

Standard `build` ignores visual_prompt, so this is safe — it just unlocks ai-build.

Usage:
  python scripts/inject_visual_prompts.py            # all episodes
  python scripts/inject_visual_prompts.py s06-yawning
"""
import glob
import os
import re
import sys

import yaml


def episodes():
    eps = [os.path.dirname(p) for p in glob.glob("content/**/script.yaml", recursive=True)]
    return sorted(
        e for e in eps
        if not any(part.startswith((".", "_")) for part in os.path.relpath(e, "content").split(os.sep))
    )


def parse_visuals(slides_md: str) -> list[str]:
    """One Visual: description per '## Slide N' section, in order."""
    txt = open(slides_md, encoding="utf-8").read()
    out = []
    for sec in re.split(r"\n##\s+Slide\s+\d+", txt)[1:]:
        m = re.search(r"Visual:\*\*\s*(.+)", sec)
        out.append(m.group(1).strip() if m else "")
    return out


STYLE = ("Educational science illustration for a teen audience, dark navy background, "
         "neon cyan and purple accents, clean vector diagram style, high detail, no text")


def inject(ep_dir: str) -> bool:
    smd = os.path.join(ep_dir, "SLIDES.md")
    scr_path = os.path.join(ep_dir, "script.yaml")
    if not os.path.exists(smd):
        return False
    visuals = parse_visuals(smd)
    data = yaml.safe_load(open(scr_path, encoding="utf-8")) or {}
    slides = data.get("slides", [])
    changed = 0
    for i, s in enumerate(slides):
        v = visuals[i] if i < len(visuals) else ""
        if v:
            s["visual_prompt"] = f"{v}. {STYLE}"
            changed += 1
    with open(scr_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=4000)
    return changed > 0


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    done = 0
    for ed in episodes():
        if only and os.path.basename(ed) != only:
            continue
        if inject(ed):
            done += 1
            print(f"  {os.path.basename(ed)}")
    print(f"DONE: visual_prompt added to {done} episode(s). Render with: shiksha-cast ai-build -c <ep>")


if __name__ == "__main__":
    main()
