"""
Fail if any runtime code imports from services._deprecated.

Usage:
    PYTHONPATH=backend python3 scripts/check_no_deprecated_imports.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "backend"


def main() -> int:
    bad_hits = []
    for path in TARGET.rglob("*.py"):
        # Skip deprecated folder itself
        if "_deprecated" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "services._deprecated" in text or "services/_deprecated" in text:
            bad_hits.append(path.relative_to(ROOT))
    if bad_hits:
        print("❌ Found imports referencing services._deprecated:", file=sys.stderr)
        for hit in bad_hits:
            print(f" - {hit}", file=sys.stderr)
        return 1
    print("✅ No services._deprecated imports detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
