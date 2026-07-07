import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "slice_rigsheet", ROOT / "scripts" / "slice_rigsheet.py")
slice_rigsheet = importlib.util.module_from_spec(SPEC)
sys.modules["slice_rigsheet"] = slice_rigsheet
try:
    SPEC.loader.exec_module(slice_rigsheet)
    HAVE_DEPS = True
except ModuleNotFoundError:
    HAVE_DEPS = False  # numpy/scipy/PIL not installed in this env

pytestmark = pytest.mark.skipif(not HAVE_DEPS, reason="numpy/scipy/PIL required")


def test_merge_x_overlap_joins_stacked_pieces():
    # an eye (iris box) + its highlight dot sitting above it, overlapping in x
    eye = (788, 445, 862, 519)
    highlight = (803, 426, 852, 444)
    merged = slice_rigsheet._merge_x_overlap([highlight, eye])
    assert merged == [(788, 426, 862, 519)]


def test_merge_x_overlap_keeps_separated_parts():
    left = (39, 444, 95, 469)
    right = (135, 445, 191, 469)  # a gap in x -> different parts
    assert slice_rigsheet._merge_x_overlap([right, left]) == [left, right]


def test_group_by_count_consumes_left_to_right():
    blobs = [(i * 10, 0, i * 10 + 5, 5) for i in range(4)]
    groups = slice_rigsheet._group_by_count(blobs, [2, 1, 1])
    assert [len(g) for g in groups] == [2, 1, 1]


def test_group_by_gaps_splits_at_widest_edge_gaps():
    # three tight pairs separated by big gaps -> 3 groups of 2
    blobs = [(0, 0, 10, 5), (12, 0, 22, 5),      # pair 1
             (200, 0, 210, 5), (212, 0, 222, 5),  # pair 2
             (400, 0, 410, 5), (412, 0, 422, 5)]  # pair 3
    groups = slice_rigsheet._group_by_gaps(blobs, 3)
    assert [len(g) for g in groups] == [2, 2, 2]


def test_names_and_counts_line_up():
    for names, counts in zip(slice_rigsheet.NAMES, slice_rigsheet.COUNTS):
        assert len(names) == len(counts)


@pytest.mark.skipif(
    not (ROOT / "assets/cartoon/source/kinnu_rigsheet.png").exists(),
    reason="reference rig sheet not present")
def test_slices_reference_sheet_into_all_parts(tmp_path):
    src = ROOT / "assets/cartoon/source/kinnu_rigsheet.png"
    saved = slice_rigsheet.slice_sheet(src, tmp_path)
    expected = {n for row in slice_rigsheet.NAMES for n in row}
    assert set(saved) == expected  # all 26 named parts detected
    for name in expected:
        assert (tmp_path / f"{name}.png").exists()
