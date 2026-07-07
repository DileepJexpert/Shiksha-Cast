from __future__ import annotations

import argparse
import glob
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

import yaml

AssetKind = Literal["character", "background", "prop"]


@dataclass(frozen=True)
class AssetRequirement:
    kind: AssetKind
    name: str
    expected_path: Path
    source: str
    exists: bool

    @property
    def status(self) -> str:
        return "FOUND" if self.exists else "MISSING"


def find_project_root(start: Path | None = None) -> Path:
    cwd = (start or Path.cwd()).resolve()
    for directory in [cwd, *cwd.parents]:
        if (directory / "config" / "channel.yaml").exists():
            return directory
    raise FileNotFoundError(
        "Could not find project root. Run from inside Shiksha-Cast or pass --root."
    )


def find_scenes_yaml(project_root: Path, chapter: str) -> Path:
    pattern = str(project_root / "content" / "**" / chapter / "scenes.yaml")
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        raise FileNotFoundError(f"No scenes.yaml found for episode '{chapter}' under content/.")
    return Path(matches[0])


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _asset_name(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("asset", "id", "name", "path"):
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
    return None


def _expected_path(project_root: Path, kind: AssetKind, name: str) -> Path:
    if kind == "character":
        return project_root / "assets" / "cartoon" / "characters" / name
    if kind == "background":
        return project_root / "assets" / "cartoon" / "backgrounds" / name
    return project_root / "assets" / "cartoon" / "props" / name


def _kind_label(kind: AssetKind) -> str:
    return {"character": "characters", "background": "backgrounds", "prop": "props"}[kind]


def _add_requirement(
    seen: dict[tuple[AssetKind, str], AssetRequirement],
    project_root: Path,
    kind: AssetKind,
    name: str | None,
    source: str,
) -> None:
    if not name:
        return
    key = (kind, name)
    if key in seen:
        return
    expected = _expected_path(project_root, kind, name)
    seen[key] = AssetRequirement(
        kind=kind,
        name=name,
        expected_path=expected,
        source=source,
        exists=expected.exists(),
    )


def collect_required_assets(project_root: Path, scenes: dict[str, Any]) -> list[AssetRequirement]:
    seen: dict[tuple[AssetKind, str], AssetRequirement] = {}

    required = scenes.get("required_assets") or {}
    if isinstance(required, dict):
        for name in _as_list(required.get("characters")):
            _add_requirement(seen, project_root, "character", _asset_name(name), "required_assets.characters")
        for name in _as_list(required.get("backgrounds")):
            _add_requirement(seen, project_root, "background", _asset_name(name), "required_assets.backgrounds")
        for name in _as_list(required.get("props")):
            _add_requirement(seen, project_root, "prop", _asset_name(name), "required_assets.props")

    for scene_index, scene in enumerate(_as_list(scenes.get("scenes")), start=1):
        if not isinstance(scene, dict):
            continue
        scene_id = scene.get("id") or f"scene_{scene_index:03d}"
        _add_requirement(
            seen,
            project_root,
            "background",
            _asset_name(scene.get("background")),
            f"scenes[{scene_id}].background",
        )
        for char_index, char in enumerate(_as_list(scene.get("characters")), start=1):
            if isinstance(char, dict):
                _add_requirement(
                    seen,
                    project_root,
                    "character",
                    _asset_name(char.get("asset") or char.get("id")),
                    f"scenes[{scene_id}].characters[{char_index}]",
                )
        for prop_index, prop in enumerate(_as_list(scene.get("props")), start=1):
            if isinstance(prop, dict):
                _add_requirement(
                    seen,
                    project_root,
                    "prop",
                    _asset_name(prop.get("asset") or prop.get("id")),
                    f"scenes[{scene_id}].props[{prop_index}]",
                )
            else:
                _add_requirement(
                    seen,
                    project_root,
                    "prop",
                    _asset_name(prop),
                    f"scenes[{scene_id}].props[{prop_index}]",
                )

    return sorted(seen.values(), key=lambda item: (_kind_label(item.kind), item.name))


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def load_episode_assets(chapter: str, project_root: Path) -> tuple[Path, dict[str, Any], list[AssetRequirement]]:
    scenes_path = find_scenes_yaml(project_root, chapter)
    scenes = load_yaml(scenes_path)
    requirements = collect_required_assets(project_root, scenes)
    return scenes_path, scenes, requirements


def print_asset_report(chapter: str, project_root: Path, scenes_path: Path, requirements: Iterable[AssetRequirement]) -> int:
    requirements = list(requirements)
    missing = [item for item in requirements if not item.exists]
    found = [item for item in requirements if item.exists]

    print(f"Asset check: {chapter}")
    print(f"Scenes: {_rel(project_root, scenes_path)}")
    print()
    for item in requirements:
        print(f"{item.status:7} {_kind_label(item.kind)[:-1]:10} {item.name:28} -> {_rel(project_root, item.expected_path)}")
    print()
    print(f"Found: {len(found)}   Missing: {len(missing)}   Total: {len(requirements)}")
    if missing:
        print("\nCreate these missing assets:")
        for item in missing:
            print(f"- {_rel(project_root, item.expected_path)}")
    return len(missing)


def write_asset_todo(chapter: str, project_root: Path, scenes_path: Path, requirements: list[AssetRequirement]) -> Path:
    missing = [item for item in requirements if not item.exists]
    found = [item for item in requirements if item.exists]
    out_dir = project_root / "build" / chapter
    out_dir.mkdir(parents=True, exist_ok=True)
    todo_path = out_dir / "ASSET_TODO.md"

    lines: list[str] = [
        f"# Asset TODO: {chapter}",
        "",
        f"Scenes file: `{_rel(project_root, scenes_path)}`",
        "",
        "## Summary",
        "",
        f"- Found assets: {len(found)}",
        f"- Missing assets: {len(missing)}",
        f"- Total referenced assets: {len(requirements)}",
        "",
        "## Missing assets to create",
        "",
    ]
    if missing:
        for item in missing:
            lines.append(f"- [ ] `{_rel(project_root, item.expected_path)}` — {item.kind} `{item.name}` from `{item.source}`")
    else:
        lines.append("No missing assets. This episode is ready for cartoon-build.")

    lines.extend(["", "## Reusable assets already found", ""])
    if found:
        for item in found:
            lines.append(f"- [x] `{_rel(project_root, item.expected_path)}` — {item.kind} `{item.name}`")
    else:
        lines.append("No reusable assets were found yet.")

    lines.extend([
        "",
        "## Recommended next step",
        "",
        "Generate only the missing backgrounds and props. Keep reusable character rigs fixed for brand consistency.",
        "",
    ])
    todo_path.write_text("\n".join(lines), encoding="utf-8")
    return todo_path


def run_asset_check(chapter: str, root: Path | None = None) -> int:
    project_root = root or find_project_root()
    scenes_path, _scenes, requirements = load_episode_assets(chapter, project_root)
    missing_count = print_asset_report(chapter, project_root, scenes_path, requirements)
    return 1 if missing_count else 0


def run_asset_plan(chapter: str, root: Path | None = None) -> int:
    project_root = root or find_project_root()
    scenes_path, _scenes, requirements = load_episode_assets(chapter, project_root)
    print_asset_report(chapter, project_root, scenes_path, requirements)
    todo_path = write_asset_todo(chapter, project_root, scenes_path, requirements)
    print(f"\nAsset TODO written: {_rel(project_root, todo_path)}")
    return 0


def _parse_args(prog: str, argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("-c", "--chapter", required=True, help="Episode id, e.g. k05-forest-village-counting")
    parser.add_argument("-r", "--root", type=Path, default=None, help="Project root directory")
    return parser.parse_args(argv)


def asset_check_main(argv: list[str] | None = None) -> None:
    args = _parse_args("python -m shiksha_cast asset-check", sys.argv[1:] if argv is None else argv)
    raise SystemExit(run_asset_check(args.chapter, args.root))


def asset_plan_main(argv: list[str] | None = None) -> None:
    args = _parse_args("python -m shiksha_cast asset-plan", sys.argv[1:] if argv is None else argv)
    raise SystemExit(run_asset_plan(args.chapter, args.root))
