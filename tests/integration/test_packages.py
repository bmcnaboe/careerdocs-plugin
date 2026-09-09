"""Package verification: the repository is one plugin for every platform, free of applicant data.

Exercises the real files — the skills tree, every manifest, and the guards — not mocks.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_inventory as ci  # noqa: E402
import pii_guard  # noqa: E402


def test_inventory_has_zero_differences():
    # Skills tree vs. the Claude and Codex manifests, package hygiene, plus `claude plugin validate`.
    assert ci.run_check(ROOT) == []


def test_pii_guard_over_tracked_tree_is_clean():
    assert pii_guard.scan_repo(ROOT) == []


def test_claude_validate_when_available():
    # A no-op unless the Claude CLI is present; must not error when it is.
    assert ci.claude_validate(ROOT) == []
