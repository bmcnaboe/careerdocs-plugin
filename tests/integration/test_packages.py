"""US1 verification: both packages expose an identical, applicant-data-free inventory.

Exercises the real files — the skills tree, both manifests, the installer, and the
guards — not mocks.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "packages" / "openai"))

import check_inventory as ci  # noqa: E402
import install  # noqa: E402
import pii_guard  # noqa: E402

MANIFEST = install.load_manifest()


def test_inventory_has_zero_differences():
    # Skills tree vs. Claude manifests vs. OpenAI manifest, plus `claude plugin validate`.
    assert ci.run_check(ROOT) == []


def test_installer_links_byte_identical_skills(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "packages" / "openai" / "install.py"),
         "--link", "--home", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    base = tmp_path / ".agents" / "skills"
    for skill in MANIFEST["skills"]:
        installed = base / skill["name"] / "SKILL.md"
        source = ROOT / "skills" / skill["name"] / "SKILL.md"
        assert installed.read_bytes() == source.read_bytes()


def test_install_contains_no_applicant_data(tmp_path):
    subprocess.run(
        [sys.executable, str(ROOT / "packages" / "openai" / "install.py"),
         "--link", "--home", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    base = tmp_path / ".agents" / "skills"
    findings = []
    for skill in MANIFEST["skills"]:
        resolved = (base / skill["name"]).resolve()
        for path in resolved.rglob("*"):
            if path.is_file():
                findings += pii_guard.scan_file(path)
    assert findings == []


def test_pii_guard_over_tracked_tree_is_clean():
    assert pii_guard.scan_repo(ROOT) == []


def test_claude_validate_when_available():
    # A no-op unless the Claude CLI is present; must not error when it is.
    assert ci.claude_validate(ROOT) == []
