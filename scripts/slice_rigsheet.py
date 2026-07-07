"""Slice a Kinnu rig sheet into named transparent part PNGs — automatically.

The sheet is a grid of character parts on a light/checkerboard background, each with
a small text label beneath it. Instead of hardcoded pixel coordinates (which break
whenever the sheet is regenerated), this detects the part rows and the parts within
each row from the image itself, and assigns the canonical names by position.

The only assumption is the canonical *order* of parts (see NAMES) — which the
KINNU_ART_WORKFLOW.md generation prompt locks in — and that each part has a little
whitespace between it and its text label (so labels fall in their own thin bands).

Usage:
    python scripts/slice_rigsheet.py [SHEET.png] [OUT_DIR]

Output: <OUT_DIR>/<name>.png  +  parts_montage.png  +  parts_detected.png (debug)
Default OUT_DIR: assets/cartoon/source/parts
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "cartoon" / "source" / "kinnu_rigsheet.png"
PARTS = ROOT / "assets" / "cartoon" / "source" / "parts"

# Canonical layout: one list per part-row, parts in left-to-right order. Detection
# finds the boxes; these names are assigned by position. Keep in sync with the
# generation prompt in KINNU_ART_WORKFLOW.md and with cartoon/rig2.py.
NAMES: list[list[str]] = [
    ["torso", "head", "upper_arm_left", "forearm_left", "upper_arm_right", "forearm_right"],
    ["brows_neutral", "brows_happy", "brows_sad", "brows_surprised",
     "eyes_open", "eyes_closed", "eyes_happy"],
    ["mouth_A", "mouth_B", "mouth_C", "mouth_D", "mouth_E",
     "mouth_F", "mouth_G", "mouth_H", "mouth_X"],
    ["thigh_left", "shin_left", "thigh_right", "shin_right"],
]

# How many separate ink blobs each part is drawn with. Brows and eyes come as a
# left+right PAIR (2 blobs); everything else is a single connected shape. This lets
# a row be split by consuming blobs left-to-right, which is immune to how wide the
# gap inside a pair is (the failure mode of pure gap-merging).
COUNTS: list[list[int]] = [
    [1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 2, 2],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1],
]


def key_background(im: Image.Image) -> np.ndarray:
    """Return an RGBA array with the flat, bright, low-saturation background keyed to
    alpha=0. Anything connected to the image border is treated as background, so an
    interior white (e.g. an eye) is kept."""
    rgb = np.asarray(im.convert("RGB")).astype(np.int16)
    bright = rgb.max(2)
    sat = rgb.max(2) - rgb.min(2)
    bg_cand = (bright > 170) & (sat < 48)
    lbl, _ = ndimage.label(bg_cand)
    border = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
    border.discard(0)
    bg = np.isin(lbl, list(border))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    return np.dstack([np.asarray(im.convert("RGB")), alpha])


def _bands(present: np.ndarray) -> list[list[int]]:
    """Maximal runs of True in a 1-D boolean array, as [start, end) pairs."""
    runs: list[list[int]] = []
    i, n = 0, len(present)
    while i < n:
        if present[i]:
            j = i
            while j < n and present[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    return runs


def _merge_x_overlap(blobs):
    """Union blobs whose x-ranges overlap. Parts are laid out left-to-right with
    whitespace between them, so x-overlap can only mean two vertically-stacked pieces
    of the SAME part (e.g. an eye's iris + its highlight dot, drawn as separate
    shapes). This collapses those to one blob so the per-part blob count is stable."""
    blobs = sorted(blobs, key=lambda b: b[0])
    out: list[list[int]] = []
    for b in blobs:
        if out and b[0] <= out[-1][2]:  # overlaps/touches current group in x
            g = out[-1]
            g[0], g[1] = min(g[0], b[0]), min(g[1], b[1])
            g[2], g[3] = max(g[2], b[2]), max(g[3], b[3])
        else:
            out.append(list(b))
    return [tuple(g) for g in out]


def _row_blobs(alpha: np.ndarray, ry0: int, ry1: int) -> list[tuple[int, int, int, int]]:
    """Ink blobs within a row band, as tight (x0,y0,x1,y1) boxes sorted left-to-right.
    Tiny specks (keying noise) are dropped; vertically-stacked pieces of one part are
    merged by x-overlap."""
    band = alpha[ry0:ry1, :] > 0
    lbl, n = ndimage.label(band)
    if n == 0:
        return []
    row_area = (ry1 - ry0) * alpha.shape[1]
    min_area = max(20, int(row_area * 0.0006))
    blobs = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lbl == i)
        if len(xs) < min_area:
            continue
        blobs.append((int(xs.min()), int(ry0 + ys.min()),
                      int(xs.max() + 1), int(ry0 + ys.max() + 1)))
    return _merge_x_overlap(blobs)


def _union(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _group_by_count(blobs, counts):
    """Assign blobs to parts left-to-right, consuming `counts[i]` blobs for part i."""
    groups, k = [], 0
    for c in counts:
        groups.append(blobs[k:k + c])
        k += c
    return groups


def _group_by_gaps(blobs, k):
    """Fallback for rows whose blob count differs from the expected (e.g. open eyes
    carry separate highlight dots). Split the x-sorted blobs into k groups at the k-1
    widest *edge* gaps (whitespace between one blob's right edge and the next's left
    edge). Edge gaps — unlike centre gaps — are small or negative for overlapping
    blobs (a highlight over an eye), so those never cause a cut; only the real
    between-part whitespace does."""
    if len(blobs) <= k:
        return [[b] for b in blobs] + [[] for _ in range(k - len(blobs))]
    edge_gap = [blobs[i + 1][0] - blobs[i][2] for i in range(len(blobs) - 1)]
    cuts = sorted(sorted(range(len(edge_gap)), key=lambda i: edge_gap[i], reverse=True)[:k - 1])
    groups, start = [], 0
    for cut in cuts:
        groups.append(blobs[start:cut + 1])
        start = cut + 1
    groups.append(blobs[start:])
    return groups


def slice_sheet(src: Path, out_dir: Path) -> dict[str, tuple[int, int, int, int]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = out_dir.parent  # keyed/montage/overlay live next to the parts folder
    rgba = key_background(Image.open(src))
    Image.fromarray(rgba, "RGBA").save(debug_dir / f"{src.stem}_keyed.png")
    alpha = rgba[..., 3]
    h, w = alpha.shape

    # --- rows: horizontal bands of content; the tallest len(NAMES) are the part rows
    row_present = alpha.sum(axis=1) > (0.01 * 255 * w)
    row_bands = _bands(row_present)
    if len(row_bands) < len(NAMES):
        raise SystemExit(
            f"[error] found only {len(row_bands)} content rows, need {len(NAMES)}. "
            "Is the sheet background flat/bright and are the rows separated?"
        )
    part_rows = sorted(sorted(row_bands, key=lambda b: b[1] - b[0], reverse=True)[:len(NAMES)])

    saved: dict[str, tuple[int, int, int, int]] = {}
    boxes: list[tuple[str, tuple[int, int, int, int]]] = []
    for (ry0, ry1), names, counts in zip(part_rows, NAMES, COUNTS):
        blobs = _row_blobs(alpha, ry0, ry1)
        expected = sum(counts)
        if len(blobs) == expected:
            groups = _group_by_count(blobs, counts)
        else:
            print(f"[warn] row {ry0}-{ry1}: found {len(blobs)} blobs, expected {expected} "
                  f"({names[0]}…{names[-1]}). Falling back to gap split.")
            groups = _group_by_gaps(blobs, len(names))
        for group, name in zip(groups, names):
            if not group:
                print(f"[warn] {name}: empty")
                continue
            x0, y0, x1, y1 = _union(group)
            Image.fromarray(rgba[y0:y1, x0:x1], "RGBA").save(out_dir / f"{name}.png")
            saved[name] = (x0, y0, x1, y1)
            boxes.append((name, (x0, y0, x1, y1)))

    _write_debug_overlay(rgba, boxes, debug_dir / "parts_detected.png")
    _write_montage(out_dir, list(saved), debug_dir / "parts_montage.png")
    return saved


def _write_debug_overlay(rgba, boxes, path: Path) -> None:
    """Draw the detected boxes + assigned names over the keyed sheet, so a bad crop
    is obvious at a glance."""
    im = Image.fromarray(rgba, "RGBA").convert("RGB")
    d = ImageDraw.Draw(im)
    for name, (x0, y0, x1, y1) in boxes:
        d.rectangle([x0, y0, x1, y1], outline=(230, 30, 120), width=3)
        d.text((x0 + 3, y0 + 3), name, fill=(230, 30, 120))
    im.save(path)
    print(f"debug overlay -> {path.name}")


def _write_montage(out_dir: Path, names: list[str], path: Path) -> None:
    cols, cell = 7, 220
    rows = (len(names) + cols - 1) // cols
    mont = Image.new("RGBA", (cols * cell, rows * (cell + 24)), (240, 240, 245, 255))
    d = ImageDraw.Draw(mont)
    for i, name in enumerate(names):
        im = Image.open(out_dir / f"{name}.png")
        im.thumbnail((cell - 20, cell - 20))
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 24)
        mont.alpha_composite(im, (cx + (cell - im.width) // 2, cy + (cell - im.height) // 2))
        d.text((cx + 6, cy + cell), name, fill=(20, 20, 30))
    mont.convert("RGB").save(path)
    print(f"montage -> {path.name}")


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else PARTS
    if not src.exists():
        raise SystemExit(f"[error] sheet not found: {src}")
    saved = slice_sheet(src, out_dir)
    expected = sum(len(r) for r in NAMES)
    print(f"saved {len(saved)}/{expected} parts -> {out_dir}")
    missing = [n for row in NAMES for n in row if n not in saved]
    if missing:
        print(f"[warn] missing parts: {', '.join(missing)} — check parts_detected.png")


if __name__ == "__main__":
    main()
