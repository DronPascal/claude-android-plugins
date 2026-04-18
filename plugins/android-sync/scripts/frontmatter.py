"""Pure helpers for SKILL.md frontmatter manipulation.

Our SKILL.md format:
---
name: <skill-name>
description: >
  <trigger phrases...>
upstream:
  source: android/skills
  path: <upstream-path>
  commit: <sha>
  license: Apache-2.0
---

> Adapted from [android/skills](https://github.com/android/skills) (Apache 2.0).
> See [NOTICE.md](../../../../NOTICE.md).

<body...>
"""

import re
from typing import Tuple


def split(text: str) -> Tuple[str, str]:
    """Split SKILL.md text into (frontmatter_block, body).

    Frontmatter block includes the leading and trailing `---` lines.
    Body is everything after (including any attribution pointer).
    Raises ValueError if the file doesn't start with `---` on the first line
    or lacks a closing `---`.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        raise ValueError("SKILL.md must start with '---' line")
    # Find the closing '---' (second occurrence).
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == "---":
            fm = "".join(lines[: i + 1])
            body = "".join(lines[i + 1 :])
            return fm, body
    raise ValueError("SKILL.md frontmatter has no closing '---'")


def extract_body(text: str) -> str:
    """Return body (everything after the frontmatter's closing `---`)."""
    _, body = split(text)
    return body


def update_upstream_commit(text: str, new_sha: str) -> str:
    """Replace the `commit:` value inside the `upstream:` block.

    Only touches the first `commit:` line occurring AFTER the `upstream:` key.
    Preserves surrounding whitespace and indentation. Raises ValueError if
    no `upstream.commit` field is found.
    """
    fm, body = split(text)
    # Match: `upstream:` on its own line, then any lines, then `  commit: <sha>`.
    pattern = re.compile(
        r"(^upstream:\s*\n(?:[^\n]*\n)*?)(\s+commit:\s*)([^\s\n]+)",
        re.MULTILINE,
    )
    new_fm, n = pattern.subn(rf"\g<1>\g<2>{new_sha}", fm, count=1)
    if n == 0:
        raise ValueError("upstream.commit field not found in frontmatter")
    return new_fm + body


def attribution_pointer(plugin_depth: int = 4) -> str:
    """Return the 2-line attribution pointer block (with surrounding blank lines).

    Placed at the start of body in every ported SKILL.md. Required by
    Apache 2.0 — must survive upstream sync.
    """
    notice_rel = "../" * plugin_depth + "NOTICE.md"
    return (
        "\n"
        f"> Adapted from [android/skills](https://github.com/android/skills) (Apache 2.0).\n"
        f"> See [{notice_rel}]({notice_rel}).\n"
        "\n"
    )


def build(
    name: str,
    description: str,
    upstream_path: str,
    commit: str,
    plugin_depth: int = 4,
) -> str:
    """Build our full SKILL.md header (frontmatter + attribution pointer).

    `plugin_depth` = number of `../` steps from SKILL.md to marketplace root.
    For `plugins/<plugin>/skills/<skill>/SKILL.md` the depth is 4.

    Returns header ending with a trailing blank line; caller appends body.
    """
    return (
        "---\n"
        f"name: {name}\n"
        "description: >\n"
        + "".join(f"  {line}\n" for line in description.strip().splitlines())
        + "upstream:\n"
        f"  source: android/skills\n"
        f"  path: {upstream_path}\n"
        f"  commit: {commit}\n"
        f"  license: Apache-2.0\n"
        "---\n"
        + attribution_pointer(plugin_depth)
    )


# --- self-tests ---

def _run_self_tests() -> None:
    sample = (
        "---\n"
        "name: test-skill\n"
        "description: x\n"
        "upstream:\n"
        "  source: android/skills\n"
        "  path: a/b/c\n"
        "  commit: abc123\n"
        "  license: Apache-2.0\n"
        "---\n"
        "\n"
        "> Attribution line\n"
        "\n"
        "Body starts here.\n"
        "More body.\n"
    )

    fm, body = split(sample)
    assert fm.startswith("---\n") and fm.rstrip().endswith("---"), "split: bad fm"
    assert "Body starts here" in body, "split: bad body"

    assert extract_body(sample).startswith("\n> Attribution"), "extract_body"

    updated = update_upstream_commit(sample, "deadbeef")
    assert "commit: deadbeef" in updated, "update_upstream_commit: not replaced"
    assert "commit: abc123" not in updated, "update_upstream_commit: old sha left"
    # Body untouched:
    assert extract_body(updated) == extract_body(sample), "update: body changed"

    built = build(
        name="my-skill",
        description="line1\nline2",
        upstream_path="x/y/z",
        commit="cafebabe",
    )
    assert "name: my-skill" in built
    assert "  line1\n  line2\n" in built
    assert "  path: x/y/z\n" in built
    assert "  commit: cafebabe\n" in built
    assert "../../../../NOTICE.md" in built

    # attribution_pointer
    ptr = attribution_pointer()
    assert ptr.startswith("\n> Adapted from [android/skills]"), "pointer prefix"
    assert "../../../../NOTICE.md" in ptr
    assert ptr.endswith("\n\n"), "pointer trailing blank"
    # build() should include the pointer:
    assert ptr in built, "build() output must contain attribution_pointer"

    print("frontmatter.py: all self-tests passed")


if __name__ == "__main__":
    _run_self_tests()
