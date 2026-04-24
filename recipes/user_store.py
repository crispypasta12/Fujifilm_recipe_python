"""User recipe persistence — save, list, delete, and recently-used tracking.

User recipes live in  recipes/user/<slug>.json.
Insertion order is tracked in  recipes/user/_index.json.
Recently-used entries are stored in  recipes/user/_recent.json
  (capped at MAX_RECENT, most-recent first).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import fields
from pathlib import Path
from typing import Optional

from profile.preset_translate import PresetUIValues
from recipes.loader import Recipe

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

USER_DIR    = Path(__file__).resolve().parent / "user"
INDEX_FILE  = USER_DIR / "_index.json"
RECENT_FILE = USER_DIR / "_recent.json"
MAX_RECENT  = 10


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_index() -> list[str]:
    if not INDEX_FILE.exists():
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_index(slugs: list[str]) -> None:
    USER_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(slugs, indent=2), encoding="utf-8")


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "recipe"


def _unique_slug(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def _values_to_dict(values: PresetUIValues) -> dict:
    return {f.name: getattr(values, f.name) for f in fields(values)}


def _dict_to_values(d: dict) -> PresetUIValues:
    valid = {f.name for f in fields(PresetUIValues)}
    return PresetUIValues(**{k: v for k, v in d.items() if k in valid})


def _recipe_from_file(slug: str, sensor: str = "my-recipes") -> Optional[Recipe]:
    path = USER_DIR / f"{slug}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ui = _dict_to_values(data.get("params", {}))
        return Recipe(
            slug=slug,
            title=data.get("name", slug.replace("-", " ").title()),
            source="My Recipes",
            sensor=sensor,
            image_path=None,
            ui_values=ui,
        )
    except Exception:
        return None


def _read_recent_raw() -> list[dict]:
    if not RECENT_FILE.exists():
        return []
    try:
        return json.loads(RECENT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_recent(entries: list[dict]) -> None:
    USER_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_recipe(
    name: str,
    values: PresetUIValues,
    replace_slug: Optional[str] = None,
) -> str:
    """Save a user recipe. Returns the slug used to identify it.

    If replace_slug is given and exists in the index, the existing file is
    overwritten in-place (the slug stays the same even if the name changed).
    """
    USER_DIR.mkdir(parents=True, exist_ok=True)
    slugs = _read_index()

    if replace_slug and replace_slug in slugs:
        slug = replace_slug
    else:
        slug = _unique_slug(_slugify(name), set(slugs))
        slugs.append(slug)
        _write_index(slugs)

    path = USER_DIR / f"{slug}.json"
    payload = {"name": name, "params": _values_to_dict(values)}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return slug


def list_recipes() -> list[Recipe]:
    """Return all saved user recipes in insertion order."""
    recipes: list[Recipe] = []
    for slug in _read_index():
        r = _recipe_from_file(slug)
        if r:
            recipes.append(r)
    return recipes


def delete_recipe(slug: str) -> None:
    """Remove a user recipe from disk and from both indexes."""
    slugs = _read_index()
    if slug in slugs:
        slugs.remove(slug)
        _write_index(slugs)

    path = USER_DIR / f"{slug}.json"
    if path.exists():
        path.unlink()

    # Also purge from recently used
    recent = [r for r in _read_recent_raw() if r.get("slug") != slug]
    _write_recent(recent)


def record_used(slug: str, name: str, values: PresetUIValues) -> None:
    """Record a recipe as recently used (most-recent first, capped at MAX_RECENT)."""
    recent = [r for r in _read_recent_raw() if r.get("slug") != slug]
    recent.insert(0, {
        "slug": slug,
        "name": name,
        "params": _values_to_dict(values),
        "used_at": time.time(),
    })
    _write_recent(recent[:MAX_RECENT])


def load_recent() -> list[Recipe]:
    """Return up to MAX_RECENT recently used recipes, most-recent first."""
    recipes: list[Recipe] = []
    for entry in _read_recent_raw():
        try:
            slug = entry["slug"]
            name = entry.get("name", slug.replace("-", " ").title())
            ui = _dict_to_values(entry.get("params", {}))
            recipes.append(Recipe(
                slug=slug,
                title=name,
                source="Recently Used",
                sensor="recent",
                image_path=None,
                ui_values=ui,
            ))
        except Exception:
            pass
    return recipes
