"""The pyproject.toml is the version of record; it must parse and carry the version."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def test_pyproject_parses():
    data = _load()
    assert data["project"]["name"] == "careerdocs-plugin"


def test_pyproject_carries_version():
    data = _load()
    assert data["project"]["version"] == "0.1.0"


def test_requires_python_at_least_311():
    data = _load()
    assert data["project"]["requires-python"].replace(" ", "") == ">=3.11"


def test_dev_extra_declares_runtime_and_test_deps():
    data = _load()
    dev = set(data["project"]["optional-dependencies"]["dev"])
    for pkg in ("pytest", "jsonschema", "docxtpl", "python-docx", "pypdf",
                "pdfplumber", "pypdfium2", "python-dateutil", "reportlab"):
        assert pkg in dev, f"missing dev dependency: {pkg}"
