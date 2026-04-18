"""Parse and update the ported-skills table inside NOTICE.md.

Table is bounded by `<!-- table-start -->` and `<!-- table-end -->` comments.
Header rows (column names + separator) are always the first two rows of the
table block. Data rows follow.
"""

import re
from typing import List, Dict


TABLE_START = "<!-- table-start -->"
TABLE_END = "<!-- table-end -->"
HEADER = "| Plugin | Skill | Upstream path | Last synced commit |"
SEPARATOR = "|---|---|---|---|"


def _split_blocks(text: str) -> tuple:
    """Return (before_block, block_lines_list, after_block).

    block_lines_list is the lines strictly between the start/end markers,
    excluding the marker lines themselves.
    """
    lines = text.splitlines()
    try:
        i_start = lines.index(TABLE_START)
        i_end = lines.index(TABLE_END)
    except ValueError as e:
        raise ValueError(f"NOTICE.md missing table markers: {e}")
    if i_end <= i_start:
        raise ValueError("NOTICE.md: table-end before table-start")
    before = "\n".join(lines[: i_start + 1]) + "\n"
    block = lines[i_start + 1 : i_end]
    after = "\n".join(lines[i_end:]) + ("\n" if text.endswith("\n") else "")
    return before, block, after


def parse(notice_text: str) -> List[Dict[str, str]]:
    """Return list of {plugin, skill, upstream_path, commit} dicts."""
    _, block, _ = _split_blocks(notice_text)
    rows: List[Dict[str, str]] = []
    for line in block:
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        if line == HEADER or line == SEPARATOR:
            continue
        # "| a | b | c | d |" → ["a", "b", "c", "d"]
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        rows.append({
            "plugin": cells[0],
            "skill": cells[1],
            "upstream_path": cells[2],
            "commit": cells[3],
        })
    return rows


def upsert(
    notice_text: str,
    plugin: str,
    skill: str,
    upstream_path: str,
    commit: str,
) -> str:
    """Add or update row keyed by (plugin, skill). Returns new text."""
    before, block, after = _split_blocks(notice_text)

    # Collect existing data rows (skip header/separator).
    data_rows: List[Dict[str, str]] = parse(notice_text)

    # Update or append.
    key = (plugin, skill)
    updated = False
    for row in data_rows:
        if (row["plugin"], row["skill"]) == key:
            row["upstream_path"] = upstream_path
            row["commit"] = commit
            updated = True
            break
    if not updated:
        data_rows.append({
            "plugin": plugin,
            "skill": skill,
            "upstream_path": upstream_path,
            "commit": commit,
        })

    # Sort stable: by (plugin, skill) for deterministic output.
    data_rows.sort(key=lambda r: (r["plugin"], r["skill"]))

    # Reassemble block.
    new_block_lines = [HEADER, SEPARATOR]
    for r in data_rows:
        new_block_lines.append(
            f"| {r['plugin']} | {r['skill']} | {r['upstream_path']} | {r['commit']} |"
        )
    new_block = "\n".join(new_block_lines) + "\n"
    return before + new_block + after


def _run_self_tests() -> None:
    sample = (
        "# NOTICE\n\n"
        "## Ported skills\n\n"
        f"{TABLE_START}\n"
        f"{HEADER}\n"
        f"{SEPARATOR}\n"
        f"{TABLE_END}\n"
        "\ntrailing\n"
    )

    assert parse(sample) == [], "empty parse"

    with_row = upsert(sample, "android-core", "navigation-3", "navigation/navigation-3/", "aaa111")
    assert "| android-core | navigation-3 |" in with_row
    parsed = parse(with_row)
    assert len(parsed) == 1 and parsed[0]["commit"] == "aaa111"

    # Add a second row.
    with_two = upsert(with_row, "android-core", "edge-to-edge", "system/edge-to-edge/", "bbb222")
    assert len(parse(with_two)) == 2

    # Update existing row.
    updated = upsert(with_two, "android-core", "navigation-3", "navigation/navigation-3/", "ccc333")
    parsed = parse(updated)
    nav = next(r for r in parsed if r["skill"] == "navigation-3")
    assert nav["commit"] == "ccc333", f"expected ccc333, got {nav['commit']}"
    assert len(parsed) == 2, "upsert should not add duplicate"

    # Trailing content preserved.
    assert "trailing" in updated

    print("notice.py: all self-tests passed")


if __name__ == "__main__":
    _run_self_tests()
