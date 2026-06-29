#!/usr/bin/env python3
"""Unit test for sync_upstream.discover_unported.

Builds a fake upstream tree with several SKILL.md files (one nested under
references/, which must be ignored) and checks that discover_unported returns
exactly the skills whose path is absent from the ported set.

Run: python3 tests/test_discover_unported.py
"""

import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sync_upstream  # noqa: E402


def _make_skill(root: Path, rel: str) -> None:
    d = root / rel
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("---\nname: x\n---\nbody\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        up = Path(tmp)
        # Two already-ported skills.
        _make_skill(up, "system/edge-to-edge")
        _make_skill(up, "navigation/navigation-3")
        # Two NEW upstream skills.
        _make_skill(up, "camera/camera1-to-camerax")
        _make_skill(up, "wear/wear-compose-m3")
        # A SKILL.md nested under references/ must be ignored entirely.
        _make_skill(up, "navigation/navigation-3/references/sample")

        ported = {"system/edge-to-edge", "navigation/navigation-3"}
        result = sync_upstream.discover_unported(up, ported)

        expected = ["camera/camera1-to-camerax", "wear/wear-compose-m3"]
        assert result == expected, f"expected {expected}, got {result}"

        # All ported → empty.
        ported_all = ported | set(expected)
        assert sync_upstream.discover_unported(up, ported_all) == [], "all ported should yield []"

        # Trailing-slash tolerance: caller may pass paths with or without slash;
        # discover compares against the set as given, so the integration layer
        # must rstrip. Here we assert the function itself does exact matching.
        assert sync_upstream.discover_unported(up, set()) == sorted(
            ["camera/camera1-to-camerax", "navigation/navigation-3",
             "system/edge-to-edge", "wear/wear-compose-m3"]
        ), "empty ported should surface all four skills"

    print("test_discover_unported: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
