#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
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
``uv run`` after a skills-only install, with ``python3`` as a fallback when the
dependencies are already available. All logic lives in the ``careerdocs`` package next
to this file; this shim only makes that package importable and delegates to its CLI.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from careerdocs.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
