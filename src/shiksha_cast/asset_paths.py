"""Asset path resolution for multiple video universes.

The first Kinnu renderer stored everything under ``assets/cartoon``. Newer
story channels need clearer folders, so explicit universe paths now live under
``assets/characters`` and ``assets/backgrounds`` while old bare ids keep using
the legacy locations.
"""
from __future__ import annotations

from pathlib import Path

LEGACY_CHARACTER_DIR = Path("assets/cartoon/characters")
LEGACY_BACKGROUND_DIR = Path("assets/cartoon/backgrounds")
CHARACTER_ROOT = Path("assets/characters")
BACKGROUND_ROOT = Path("assets/backgrounds")


def _as_candidate(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path


def resolve_character_dir(project_root: Path, character_id: str | Path) -> Path:
    """Resolve a character id to a rig folder.

    Bare ids preserve the historical cartoon-engine lookup order. Namespaced ids
    such as ``social/politician_hd`` or ``kinnu_universe/kinnu_hd`` resolve from
    the new universe-aware root.
    """
    cid = Path(character_id)
    direct = _as_candidate(project_root, cid)
    if cid.is_absolute() or cid.parts[0] == "assets":
        return direct

    if len(cid.parts) > 1:
        return project_root / CHARACTER_ROOT / cid

    legacy = project_root / LEGACY_CHARACTER_DIR / cid
    if legacy.exists():
        return legacy
    return project_root / CHARACTER_ROOT / cid


def resolve_background_path(project_root: Path, background: str | Path | None) -> Path | None:
    """Resolve a background image path.

    Bare filenames keep using ``assets/cartoon/backgrounds`` first. Namespaced
    backgrounds such as ``social/living_room.png`` resolve from
    ``assets/backgrounds``.
    """
    if not background:
        return None
    bg = Path(background)
    direct = _as_candidate(project_root, bg)
    if bg.is_absolute() or bg.parts[0] == "assets" or direct.exists():
        return direct

    if len(bg.parts) > 1:
        return project_root / BACKGROUND_ROOT / bg

    legacy = project_root / LEGACY_BACKGROUND_DIR / bg
    if legacy.exists():
        return legacy
    return project_root / BACKGROUND_ROOT / bg
