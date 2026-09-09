"""Locating the applicant workspace.

Every command runs against one workspace directory. It is resolved once, in the CLI entry
point, in this order (first match wins):

1. ``--workspace <dir>`` on the command line;
2. the ``CAREERDOCS_WORKSPACE`` environment variable;
3. the nearest directory at or above the current one that holds ``careerdocs.json``;
4. the recorded default — one absolute path in ``$XDG_CONFIG_HOME/careerdocs/workspace``
   (``~/.config/careerdocs/workspace``), written by the installer or by
   ``config workspace <dir>``;
5. the current directory.

Only the last is *unestablished*: nothing marks that directory as a workspace, so
commands that would read or write applicant data there refuse (see
:func:`ensure_established`). Commands that set a workspace up, or never touch one, opt
out of that guard.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import WorkspaceError

CONFIG_FILENAME = "careerdocs.json"
ENV_VAR = "CAREERDOCS_WORKSPACE"

SOURCE_LABELS = {
    "flag": "--workspace",
    "env": ENV_VAR,
    "marker": f"{CONFIG_FILENAME} at or above the current directory",
    "pointer": "the recorded default",
    "cwd": "the current directory; no workspace is configured",
}


@dataclass(frozen=True)
class Resolution:
    path: Path
    source: str

    @property
    def established(self) -> bool:
        return self.source != "cwd"

    @property
    def label(self) -> str:
        return SOURCE_LABELS[self.source]


def pointer_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "careerdocs" / "workspace"


def read_pointer() -> Path | None:
    path = pointer_path()
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return Path(text).expanduser() if text else None


def write_pointer(workspace: Path) -> Path:
    path = pointer_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{workspace}\n", encoding="utf-8")
    return path


def find_marker(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / CONFIG_FILENAME).is_file():
            return candidate
    return None


def resolve(explicit: str | None = None, *, cwd: Path | None = None) -> Resolution:
    cwd = (cwd or Path.cwd()).resolve()
    if explicit:
        return Resolution(Path(explicit).expanduser().resolve(), "flag")
    from_env = os.environ.get(ENV_VAR)
    if from_env:
        return Resolution(Path(from_env).expanduser().resolve(), "env")
    marker = find_marker(cwd)
    if marker is not None:
        return Resolution(marker, "marker")
    pointed = read_pointer()
    if pointed is not None:
        if not pointed.is_dir():
            raise WorkspaceError(
                f"the recorded default workspace {pointed} does not exist "
                f"(recorded in {pointer_path()}); re-run the installer or "
                "`careerdocs config workspace <dir>`"
            )
        return Resolution(pointed.resolve(), "pointer")
    return Resolution(cwd, "cwd")


def ensure_established(located: Resolution) -> None:
    if located.established:
        return
    raise WorkspaceError(
        f"no workspace: {located.path} has no {CONFIG_FILENAME} and no default is "
        "recorded. Pass --workspace <dir>, run `careerdocs config workspace <dir>` to "
        "record a default, or `careerdocs config init` to make this directory a workspace"
    )
