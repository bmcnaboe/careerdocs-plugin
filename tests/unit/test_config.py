"""Tests for the config module and its subcommands."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "careerdocs" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from careerdocs import cli, config  # noqa: E402
from careerdocs.errors import ConfigError  # noqa: E402


def test_default_config_validates_against_schema():
    config.validate_schema(config.default_config())


def test_resolve_missing_returns_defaults(tmp_path):
    resolved = config.resolve_config(tmp_path)
    assert resolved["providers"]["authoritative"] == "markdown"
    assert resolved["workflow"]["page_budget"]["resume"] == 2


def test_resolve_deep_merges_overrides(tmp_path):
    (tmp_path / "careerdocs.json").write_text(
        json.dumps({"version": "1", "workflow": {"positioning_default": "executive"}}),
        encoding="utf-8",
    )
    resolved = config.resolve_config(tmp_path)
    assert resolved["workflow"]["positioning_default"] == "executive"
    # Untouched nested defaults survive the merge.
    assert resolved["workflow"]["page_budget"]["cover_letter"] == 1


def test_forbidden_credential_key():
    problems = config.find_forbidden({"providers": {"token": "abc"}})
    assert any("token" in p for p in problems)


def test_forbidden_qualification_key():
    problems = config.find_forbidden({"entities": []})
    assert any("entities" in p for p in problems)


def test_forbidden_credential_value():
    problems = config.find_forbidden({"note": "my api_key is here"})
    assert any("credential-like value" in p for p in problems)


def test_check_forbidden_raises():
    with pytest.raises(ConfigError):
        config.check_forbidden({"version": "1", "secret": "x"})


def test_config_init_writes_default(tmp_path, capsys):
    assert cli.main(["config", "init", "--workspace", str(tmp_path)]) == 0
    written = json.loads((tmp_path / "careerdocs.json").read_text())
    assert written["version"] == "1"
    config.validate_schema(written)


def test_config_init_is_idempotent(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    before = (tmp_path / "careerdocs.json").read_text()
    assert cli.main(["config", "init", "--workspace", str(tmp_path)]) == 0
    assert (tmp_path / "careerdocs.json").read_text() == before


def test_config_validate_missing_is_ok(tmp_path, capsys):
    assert cli.main(["config", "validate", "--workspace", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["present"] is False


def test_config_validate_good(tmp_path):
    cli.main(["config", "init", "--workspace", str(tmp_path)])
    assert cli.main(["config", "validate", "--workspace", str(tmp_path)]) == 0


def test_config_validate_forbidden_exits_2(tmp_path):
    (tmp_path / "careerdocs.json").write_text(
        json.dumps({"version": "1", "api_key": "leak"}), encoding="utf-8"
    )
    assert cli.main(["config", "validate", "--workspace", str(tmp_path)]) == 2


def test_config_validate_schema_violation_exits_2(tmp_path):
    (tmp_path / "careerdocs.json").write_text(
        json.dumps({"version": "1", "providers": {"authoritative": "nope"}}),
        encoding="utf-8",
    )
    assert cli.main(["config", "validate", "--workspace", str(tmp_path)]) == 2


def test_file_name_pattern_is_configurable(tmp_path):
    from careerdocs import config as config_module

    assert config_module.default_config()["outputs"]["file_name"] == "{name}-{kind}"
    (tmp_path / "careerdocs.json").write_text(
        '{"version": "1", "outputs": {"file_name": "{name}-{kind}-{org}"}}', encoding="utf-8")
    assert config_module.resolve_config(tmp_path)["outputs"]["file_name"] == "{name}-{kind}-{org}"
