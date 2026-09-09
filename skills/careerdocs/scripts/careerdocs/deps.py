"""The CLI's runtime dependencies, and the first-run bootstrap that installs them.

The entry point declares these inline (PEP 723), so ``uv run`` provisions them. Where uv
is absent — Cowork's local VM, a bare sandbox, a plain ``python3`` — the entry point
calls :func:`ensure` before importing anything that needs them. It re-executes under
``uv`` when that is on PATH, otherwise installs the missing packages with pip (into the
user site-packages outside a virtual environment) and re-executes itself once so the new
packages are on the import path. Nothing in this module imports a third-party package.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys

# distribution name -> importable module
RUNTIME_DEPENDENCIES = {
    "docxtpl": "docxtpl",
    "pypdf": "pypdf",
    "pdfplumber": "pdfplumber",
    "pypdfium2": "pypdfium2",
    "jsonschema": "jsonschema",
    "python-dateutil": "dateutil",
}

# Set on the re-executed process so a failed install cannot loop.
BOOTSTRAPPED = "CAREERDOCS_BOOTSTRAPPED"


def status() -> dict[str, bool]:
    return {
        name: importlib.util.find_spec(module) is not None
        for name, module in RUNTIME_DEPENDENCIES.items()
    }


def missing() -> list[str]:
    return [name for name, present in status().items() if not present]


def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix


def pip_install_command(packages: list[str]) -> list[str]:
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", *packages]
    if not in_virtualenv():
        cmd.append("--user")
    return cmd


def ensure(entry: str, argv: list[str]) -> None:
    """Return once the runtime dependencies are importable; otherwise exit 2 with advice."""
    absent = missing()
    if not absent:
        return
    already = os.environ.get(BOOTSTRAPPED) == "1"
    env = {**os.environ, BOOTSTRAPPED: "1"}
    if shutil.which("uv") and not already:
        os.execvpe("uv", ["uv", "run", "--quiet", entry, *argv], env)
    cmd = pip_install_command(absent)
    if already:
        _fail(absent, cmd, "they are still missing after installing them")
    print(
        f"careerdocs: installing {', '.join(absent)} with pip (first run)",
        file=sys.stderr,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "externally-managed-environment" in result.stderr:
        result = subprocess.run([*cmd, "--break-system-packages"], capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout).strip().splitlines()
        _fail(absent, cmd, tail[-1] if tail else "pip failed")
    os.execve(sys.executable, [sys.executable, entry, *argv], env)


def _fail(absent: list[str], cmd: list[str], reason: str) -> None:
    print(
        f"careerdocs: cannot import {', '.join(absent)} ({reason}). Install uv "
        "(https://docs.astral.sh/uv/) so the CLI provisions them itself, or run:\n  "
        + " ".join(cmd),
        file=sys.stderr,
    )
    raise SystemExit(2)
