"""Shared fixtures.

Workspace resolution reads the environment and the developer's own recorded default
(``~/.config/careerdocs/workspace``); neither may leak into a test.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolated_workspace_resolution(tmp_path, monkeypatch):
    monkeypatch.delenv("CAREERDOCS_WORKSPACE", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
