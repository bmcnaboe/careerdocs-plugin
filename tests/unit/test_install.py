"""Tests for the OpenAI/Codex installer."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "openai"))

import install  # noqa: E402

MANIFEST = install.load_manifest()


def test_verify_real_repo_ok():
    assert install.verify(ROOT, MANIFEST) == []


def test_verify_detects_manifest_disagreement():
    bad = {"skills": MANIFEST["skills"] + [{"name": "ghost", "path": "skills/ghost"}]}
    assert install.verify(ROOT, bad) != []


def test_link_install_is_byte_identical(tmp_path):
    install.install(ROOT, MANIFEST, tmp_path, mode="link")
    target = install.target_base(tmp_path) / "careerdocs" / "SKILL.md"
    source = ROOT / "skills" / "careerdocs" / "SKILL.md"
    assert target.read_bytes() == source.read_bytes()
    assert (install.target_base(tmp_path) / "careerdocs").is_symlink()


def test_copy_install_is_byte_identical_and_real(tmp_path):
    install.install(ROOT, MANIFEST, tmp_path, mode="copy")
    installed = install.target_base(tmp_path) / "careerdocs"
    assert not installed.is_symlink()
    assert (installed / "SKILL.md").read_bytes() == (ROOT / "skills" / "careerdocs" / "SKILL.md").read_bytes()


def test_dry_run_changes_nothing(tmp_path):
    actions = install.install(ROOT, MANIFEST, tmp_path, mode="link", dry_run=True)
    assert actions
    assert not install.target_base(tmp_path).exists()


def test_install_then_uninstall(tmp_path):
    install.install(ROOT, MANIFEST, tmp_path, mode="copy")
    assert (install.target_base(tmp_path) / "careerdocs").exists()
    install.uninstall(MANIFEST, tmp_path)
    assert not (install.target_base(tmp_path) / "careerdocs").exists()


def test_reinstall_replaces_existing(tmp_path):
    install.install(ROOT, MANIFEST, tmp_path, mode="copy")
    install.install(ROOT, MANIFEST, tmp_path, mode="link")  # switch copy -> link
    assert (install.target_base(tmp_path) / "careerdocs").is_symlink()


def test_main_copy_and_uninstall(tmp_path, capsys):
    assert install.main(["--copy", "--home", str(tmp_path)]) == 0
    assert "ChatGPT upload" in capsys.readouterr().out
    assert (install.target_base(tmp_path) / "careerdocs").exists()
    assert install.main(["--uninstall", "--home", str(tmp_path)]) == 0
    assert not (install.target_base(tmp_path) / "careerdocs").exists()
