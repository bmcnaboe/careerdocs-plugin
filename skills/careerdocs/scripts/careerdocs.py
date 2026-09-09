#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "docxtpl",
#   "pypdf",
#   "pdfplumber",
#   "pypdfium2",
#   "jsonschema",
#   "python-dateutil",
# ]
# ///
"""careerdocs entry point.

Declares its runtime dependencies inline (PEP 723) so it runs standalone under
``uv run`` after a skills-only install. Under a plain ``python3`` it first makes sure
those dependencies are importable (re-executing under uv when available, else installing
them with pip once), so the first run works in a sandbox that has Python and PyPI but no
uv. All logic lives in the ``careerdocs`` package next to this file; this shim only makes
that package importable and delegates to its CLI.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from careerdocs import deps  # noqa: E402

if __name__ == "__main__":
    deps.ensure(os.path.abspath(__file__), sys.argv[1:])
    from careerdocs.cli import main

    raise SystemExit(main())
