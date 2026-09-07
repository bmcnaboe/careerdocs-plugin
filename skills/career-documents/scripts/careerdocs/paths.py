"""Locations inside the installed skill, relative to this package.

The package lives at ``<skill-root>/scripts/careerdocs/``; shipped assets (the JSON
schemas) live under ``<skill-root>/assets/``. Resolving from ``__file__`` keeps the CLI
working whether the skill is used in place or installed (linked/copied) elsewhere.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_DIR.parent
SKILL_ROOT = SCRIPTS_DIR.parent
ASSETS_DIR = SKILL_ROOT / "assets"
SCHEMAS_DIR = ASSETS_DIR / "schemas"
