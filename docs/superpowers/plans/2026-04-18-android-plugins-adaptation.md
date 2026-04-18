# Android Plugins Adaptation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code marketplace `claude-android-plugins` with 3 content plugins (android-core, android-migrations, android-performance) ported from github.com/android/skills, plus a sync plugin (android-sync) with scripts that port and update skills from upstream.

**Architecture:** All sync/port logic lives in `plugins/android-sync/scripts/` (stdlib Python — no external deps). Content plugins are dumb data + our frontmatter. `NOTICE.md` at marketplace root is the single source of truth for the skill↔upstream mapping and last-synced SHAs.

**Tech Stack:** Python 3 (stdlib only), bash (smoke tests), git, rsync, Claude Code plugin system (SKILL.md, plugin.json, marketplace.json).

**Spec:** `docs/superpowers/specs/2026-04-18-android-plugins-adaptation-design.md`
**Marketplace root:** `/Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/`
**Upstream clone for bootstrapping:** `/tmp/android-skills-inspect/` (HEAD `b281881e3fbe044d29b4ea757de06758a4ca81ec`)

---

## File Structure (target state)

```
claude-android-plugins/
  .claude-plugin/marketplace.json        # 4 plugins registered
  LICENSE-upstream-android-skills.txt    # copy of Apache 2.0 from upstream
  NOTICE.md                              # attribution + ported skills table
  README.md                              # how to install + overview
  .gitignore

  plugins/
    android-sync/
      .claude-plugin/plugin.json
      skills/update/SKILL.md             # user-invocable /android-sync:update
      agents/upstream-diff-analyzer.md
      scripts/
        frontmatter.py                   # SKILL.md frontmatter helpers
        notice.py                        # NOTICE.md table helpers
        port_skill.py                    # one-shot port from upstream
        sync_upstream.py                 # full marketplace sync loop
      tests/
        smoke_port_skill.sh              # integration smoke test

    android-core/
      .claude-plugin/plugin.json
      CLAUDE.md
      skills/
        navigation-3/SKILL.md + references/
        edge-to-edge/SKILL.md

    android-migrations/
      .claude-plugin/plugin.json
      CLAUDE.md
      skills/
        migrate-xml-views-to-compose/SKILL.md + references/
        agp-9-upgrade/SKILL.md
        play-billing-upgrade/SKILL.md + references/

    android-performance/
      .claude-plugin/plugin.json
      CLAUDE.md
      skills/
        r8-analyzer/SKILL.md + references/

  docs/superpowers/{specs,plans}/        # design + this plan
```

**Responsibility separation:**
- `frontmatter.py`: pure functions for extracting/building/updating SKILL.md frontmatter. No I/O.
- `notice.py`: pure functions for parsing/updating the NOTICE.md table. No I/O beyond the passed-in text.
- `port_skill.py`: CLI wrapper — uses both helpers + does filesystem I/O (read upstream, write target, update NOTICE.md, cp references).
- `sync_upstream.py`: CLI wrapper — uses helpers + git + rsync to sync all ported skills.
- `SKILL.md update` body: short — delegates to `sync_upstream.py` via Bash tool and dispatches `upstream-diff-analyzer` agent in parallel for each changed skill.

---

## Task 1: Complete Marketplace Skeleton

**Files:**
- Create: `LICENSE-upstream-android-skills.txt`
- Create: `NOTICE.md`
- Create: `README.md`
- Create: `.gitignore`
- Modify: `.claude-plugin/marketplace.json` (already exists with empty plugins array — stays empty until plugins ship)

- [ ] **Step 1: Copy upstream Apache 2.0 license**

```bash
cp /tmp/android-skills-inspect/LICENSE.txt \
   /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/LICENSE-upstream-android-skills.txt
```

- [ ] **Step 2: Create NOTICE.md with empty ported-skills table**

Write `NOTICE.md`:

```markdown
# NOTICE

This marketplace contains skills adapted from [android/skills](https://github.com/android/skills) under the Apache License 2.0.

## Ported skills

<!-- table-start -->
| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
<!-- table-end -->

## Modifications from upstream

- Frontmatter rewritten for Claude Code skill API (auto-trigger phrases, `upstream` block).
- Directory layout flattened to `plugins/<plugin>/skills/<skill>/SKILL.md`.
- Body and `references/` preserved as-is from upstream.

Full upstream license: `LICENSE-upstream-android-skills.txt`
```

The `<!-- table-start -->` / `<!-- table-end -->` comments are **load-bearing** — `notice.py` uses them as anchors when parsing/updating the table.

- [ ] **Step 3: Create README.md**

Write `README.md`:

```markdown
# claude-android-plugins

Claude Code marketplace with Android-development skills ported from [android/skills](https://github.com/android/skills) (Apache 2.0, Google LLC).

## Plugins

- **android-core** — always-on: Navigation-3, edge-to-edge.
- **android-migrations** — on-demand: XML→Compose, AGP-9 upgrade, Play Billing upgrade.
- **android-performance** — R8 analyzer (more to come).
- **android-sync** — `/android-sync:update` keeps ported skills in sync with upstream.

## Install

```bash
/plugin marketplace add DronPascal/claude-android-plugins
/plugin install android-core@claude-android-plugins
/plugin install android-sync@claude-android-plugins
```

Install migration/performance plugins per-project as needed.

## Upstream sync

Run `/android-sync:update` to pull latest skill content from `android/skills`. Our frontmatter is preserved; body and references are refreshed.

## License

Our adaptations: MIT. Ported skill content: Apache 2.0 (see `NOTICE.md` and `LICENSE-upstream-android-skills.txt`).
```

- [ ] **Step 4: Create .gitignore**

Write `.gitignore`:

```
/tmp/
*.pyc
__pycache__/
.DS_Store
*.egg-info
.pytest_cache/
```

- [ ] **Step 5: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add LICENSE-upstream-android-skills.txt NOTICE.md README.md .gitignore
git -c commit.gpgsign=false commit -m "chore: marketplace skeleton (LICENSE, NOTICE, README, gitignore)"
```

Expected: one commit, clean tree.

---

## Task 2: frontmatter.py — Pure Helpers

**Files:**
- Create: `plugins/android-sync/scripts/frontmatter.py`

The module has four pure functions (no I/O, no side effects):
- `split(text) -> (frontmatter_str, body_str)` — splits at second `---` line.
- `extract_body(text) -> str` — returns body (everything after second `---`).
- `update_upstream_commit(text, new_sha) -> str` — replaces the `commit:` value under `upstream:` block.
- `build(name, description, upstream_path, commit, plugin_path_depth=4) -> str` — assembles our frontmatter + attribution pointer.

- [ ] **Step 1: Write the file with embedded `if __name__ == '__main__'` self-tests**

Create `plugins/android-sync/scripts/frontmatter.py`:

```python
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
    notice_rel = "../" * plugin_depth + "NOTICE.md"
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
        "\n"
        f"> Adapted from [android/skills](https://github.com/android/skills) (Apache 2.0).\n"
        f"> See [{notice_rel}]({notice_rel}).\n"
        "\n"
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

    print("frontmatter.py: all self-tests passed")


if __name__ == "__main__":
    _run_self_tests()
```

- [ ] **Step 2: Run self-tests**

```bash
python3 /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/plugins/android-sync/scripts/frontmatter.py
```

Expected output:
```
frontmatter.py: all self-tests passed
```

- [ ] **Step 3: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-sync/scripts/frontmatter.py
git -c commit.gpgsign=false commit -m "feat(android-sync): frontmatter helpers with self-tests"
```

---

## Task 3: notice.py — NOTICE.md Table Helpers

**Files:**
- Create: `plugins/android-sync/scripts/notice.py`

Two functions operating on the markdown table between `<!-- table-start -->` and `<!-- table-end -->` markers:
- `parse(notice_text) -> list[dict]` — returns `[{plugin, skill, upstream_path, commit}, ...]`
- `upsert(notice_text, plugin, skill, upstream_path, commit) -> str` — adds/updates a row by (plugin, skill) key.

- [ ] **Step 1: Write the file**

Create `plugins/android-sync/scripts/notice.py`:

```python
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
```

- [ ] **Step 2: Run self-tests**

```bash
python3 /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/plugins/android-sync/scripts/notice.py
```

Expected output:
```
notice.py: all self-tests passed
```

- [ ] **Step 3: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-sync/scripts/notice.py
git -c commit.gpgsign=false commit -m "feat(android-sync): NOTICE.md table helpers with self-tests"
```

---

## Task 4: port_skill.py + Smoke Test

**Files:**
- Create: `plugins/android-sync/scripts/port_skill.py`
- Create: `plugins/android-sync/tests/smoke_port_skill.sh`

`port_skill.py` is a CLI script that ports ONE upstream skill into our marketplace on first import. It's used during initial setup (Tasks 6, 7, 8) AND reusable by sync when a new skill is added upstream.

Contract:
```
python3 port_skill.py \
  --upstream <dir>         # local clone of android/skills
  --upstream-path <rel>    # e.g. navigation/navigation-3
  --target-plugin <name>   # e.g. android-core
  --name <skill-name>      # e.g. navigation-3
  --marketplace <dir>      # marketplace root
  [--description-stub "..."]  # optional; defaults to TODO placeholder
```

Effects:
1. Reads upstream `<upstream>/<upstream-path>/SKILL.md`.
2. Gets upstream HEAD SHA via `git -C <upstream> rev-parse HEAD`.
3. Writes `<marketplace>/plugins/<target-plugin>/skills/<name>/SKILL.md` with our frontmatter + upstream body.
4. Copies upstream `references/` (if present) to target.
5. Updates `NOTICE.md` table row.
6. Prints instruction for manual description rewrite.

- [ ] **Step 1: Write port_skill.py**

Create `plugins/android-sync/scripts/port_skill.py`:

```python
#!/usr/bin/env python3
"""Port one upstream skill from android/skills into our marketplace.

Writes our frontmatter (with description stub) + upstream body + upstream
references. Updates NOTICE.md table. Prints a reminder to manually rewrite
the description for CC auto-triggering.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import frontmatter
import notice


DEFAULT_DESCRIPTION_STUB = (
    "TODO: rewrite as third-person CC trigger with 4-6 quoted phrases.\n"
    'Example: This skill should be used when the user asks to "do X",\n'
    '"do Y", or mentions topic Z.'
)


def get_upstream_sha(upstream_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(upstream_dir), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True, type=Path)
    ap.add_argument("--upstream-path", required=True)
    ap.add_argument("--target-plugin", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--marketplace", required=True, type=Path)
    ap.add_argument("--description-stub", default=DEFAULT_DESCRIPTION_STUB)
    args = ap.parse_args()

    upstream_dir: Path = args.upstream.resolve()
    marketplace: Path = args.marketplace.resolve()
    src_dir = upstream_dir / args.upstream_path
    src_skill = src_dir / "SKILL.md"
    if not src_skill.exists():
        print(f"ERROR: {src_skill} not found", file=sys.stderr)
        return 2

    tgt_skill_dir = marketplace / "plugins" / args.target_plugin / "skills" / args.name
    tgt_skill = tgt_skill_dir / "SKILL.md"
    if tgt_skill.exists():
        print(f"ERROR: {tgt_skill} already exists (would overwrite)", file=sys.stderr)
        return 2
    tgt_skill_dir.mkdir(parents=True, exist_ok=True)

    sha = get_upstream_sha(upstream_dir)

    # Extract body from upstream.
    upstream_text = src_skill.read_text(encoding="utf-8")
    body = frontmatter.extract_body(upstream_text)
    # Our frontmatter + attribution + upstream body.
    header = frontmatter.build(
        name=args.name,
        description=args.description_stub,
        upstream_path=args.upstream_path,
        commit=sha,
    )
    tgt_skill.write_text(header + body, encoding="utf-8")

    # Copy references/ if present.
    src_refs = src_dir / "references"
    if src_refs.is_dir():
        tgt_refs = tgt_skill_dir / "references"
        if tgt_refs.exists():
            shutil.rmtree(tgt_refs)
        shutil.copytree(src_refs, tgt_refs)

    # Update NOTICE.md.
    notice_path = marketplace / "NOTICE.md"
    notice_text = notice_path.read_text(encoding="utf-8")
    new_text = notice.upsert(
        notice_text,
        plugin=args.target_plugin,
        skill=args.name,
        upstream_path=args.upstream_path.rstrip("/") + "/",
        commit=sha,
    )
    notice_path.write_text(new_text, encoding="utf-8")

    # Summary.
    print(f"Ported: {args.upstream_path} → plugins/{args.target_plugin}/skills/{args.name}/")
    print(f"Commit: {sha}")
    print(f"Next: rewrite description in {tgt_skill.relative_to(marketplace)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write smoke test**

Create `plugins/android-sync/tests/smoke_port_skill.sh`:

```bash
#!/usr/bin/env bash
# Smoke test: port navigation-3 to a temp marketplace, verify structure.
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT_SKILL="$SCRIPT_DIR/../scripts/port_skill.py"
UPSTREAM="/tmp/android-skills-inspect"

# Ensure upstream is present.
if [ ! -d "$UPSTREAM/.git" ]; then
  echo "FAIL: upstream clone missing at $UPSTREAM"
  exit 1
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Set up fake marketplace with NOTICE.md.
mkdir -p "$TMP/.claude-plugin"
cat > "$TMP/NOTICE.md" <<'EOF'
# NOTICE

## Ported skills

<!-- table-start -->
| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
<!-- table-end -->
EOF

# Run port.
python3 "$PORT_SKILL" \
  --upstream "$UPSTREAM" \
  --upstream-path navigation/navigation-3 \
  --target-plugin android-core \
  --name navigation-3 \
  --marketplace "$TMP"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "FAIL: port_skill.py exited $rc"
  exit 1
fi

# Assertions.
SKILL="$TMP/plugins/android-core/skills/navigation-3/SKILL.md"
REFS="$TMP/plugins/android-core/skills/navigation-3/references"

[ -f "$SKILL" ]  || { echo "FAIL: SKILL.md missing"; exit 1; }
[ -d "$REFS" ]   || { echo "FAIL: references/ missing"; exit 1; }

grep -q '^name: navigation-3$'          "$SKILL" || { echo "FAIL: name frontmatter"; exit 1; }
grep -q '^  source: android/skills$'    "$SKILL" || { echo "FAIL: upstream.source"; exit 1; }
grep -q '^  path: navigation/navigation-3$' "$SKILL" || { echo "FAIL: upstream.path"; exit 1; }
grep -q '^  license: Apache-2.0$'       "$SKILL" || { echo "FAIL: license"; exit 1; }
grep -q 'Adapted from \[android/skills\]' "$SKILL" || { echo "FAIL: attribution"; exit 1; }

# Description stub present (TODO).
grep -q 'TODO: rewrite' "$SKILL" || { echo "FAIL: description stub missing"; exit 1; }

# NOTICE.md row added.
grep -q '| android-core | navigation-3 |' "$TMP/NOTICE.md" || { echo "FAIL: NOTICE row"; exit 1; }

# references non-empty.
[ "$(find "$REFS" -type f | wc -l)" -gt 0 ] || { echo "FAIL: references empty"; exit 1; }

echo "smoke_port_skill.sh: PASS"
```

Make executable:

```bash
chmod +x /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/plugins/android-sync/tests/smoke_port_skill.sh
```

- [ ] **Step 3: Run smoke test**

```bash
bash /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins/plugins/android-sync/tests/smoke_port_skill.sh
```

Expected final line:
```
smoke_port_skill.sh: PASS
```

- [ ] **Step 4: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-sync/scripts/port_skill.py plugins/android-sync/tests/smoke_port_skill.sh
git -c commit.gpgsign=false commit -m "feat(android-sync): port_skill.py + smoke test"
```

---

## Task 5: android-sync — plugin.json, SKILL.md, Agent

**Files:**
- Create: `plugins/android-sync/.claude-plugin/plugin.json`
- Create: `plugins/android-sync/skills/update/SKILL.md`
- Create: `plugins/android-sync/agents/upstream-diff-analyzer.md`

Note: `sync_upstream.py` is Task 9 (after all skills are ported — otherwise there's nothing to sync).

- [ ] **Step 1: Write plugin.json**

Create `plugins/android-sync/.claude-plugin/plugin.json`:

```json
{
  "name": "android-sync",
  "version": "0.1.0",
  "description": "Keeps android/skills-derived plugins in sync with upstream. Exposes /android-sync:update.",
  "author": { "name": "DronPascal" },
  "repository": {
    "type": "git",
    "url": "https://github.com/DronPascal/claude-android-plugins",
    "directory": "plugins/android-sync"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Write the /update skill**

Create `plugins/android-sync/skills/update/SKILL.md`:

```markdown
---
name: update
description: >
  This skill should be used when the user asks to "update android skills",
  "sync android plugins", "pull upstream android skills", "refresh android
  plugins from upstream", "обнови android плагины", or wants to refresh
  the content of android-core / android-migrations / android-performance
  plugins from github.com/android/skills.
user-invocable: true
argument-hint: "[--dry-run] [--plugin <name>]"
allowed-tools: [Bash, Read, Edit, Task]
---

Run the upstream sync for the claude-android-plugins marketplace.

## Steps

1. Locate the marketplace root by walking up from `${CLAUDE_PLUGIN_ROOT}` until a `.claude-plugin/marketplace.json` is found.
2. Invoke the sync script via Bash, forwarding user arguments:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_upstream.py \
     --marketplace <marketplace-root> $ARGUMENTS
   ```
3. Read `/tmp/android-sync-run-<timestamp>/summary.md` that the script writes. The timestamp is printed on stdout.
4. For each changed skill listed in `summary.md`, dispatch the `upstream-diff-analyzer` agent in parallel. Pass the agent the paths to `diff.patch`, old SKILL.md, new SKILL.md, and the upstream path.
5. Collect agent outputs into a consolidated changelog. Append it to `summary.md` or present it directly to the user.
6. Surface to the user: list of changed skills, plugins needing version bump (script already updates `plugin.json` in non-dry-run mode), per-skill changelogs.
7. Print the git review hint:
   ```
   Review with: git -C <marketplace> diff
   Commit with: git -C <marketplace> add -A && git commit -m "sync: update from upstream <short-sha>"
   ```

## Flags

- `--dry-run` — the script analyses and writes to `/tmp` only; no files in the marketplace are modified.
- `--plugin <name>` — sync only the named plugin's skills.
- `--force` — proceed even if the marketplace working tree is dirty.

## When NOT to run

- If the marketplace has uncommitted changes (script will abort unless `--force`).
- Without network access to github.com (clone/fetch will fail).
```

- [ ] **Step 3: Write the agent**

Create `plugins/android-sync/agents/upstream-diff-analyzer.md`:

```markdown
---
name: upstream-diff-analyzer
description: |
  Use this agent when a diff patch from the android/skills upstream needs
  to be summarised into a human-readable changelog for one specific skill.

  <example>
  Context: /android-sync:update detected body changes in the navigation-3 skill
  user: (triggered by the sync skill)
  assistant: "Launching upstream-diff-analyzer for navigation-3."
  <commentary>Sync flow delegates per-skill changelog to this agent.</commentary>
  </example>

  <example>
  Context: Multiple skills changed in upstream
  user: (triggered by the sync skill in parallel)
  assistant: "Launching upstream-diff-analyzer for edge-to-edge."
  <commentary>Agent runs in parallel, one instance per changed skill.</commentary>
  </example>
model: sonnet
color: cyan
tools: [Read, Bash]
---

You are a changelog author specialising in Android skills documentation adapted from google/android-skills.

**Inputs you will receive in the prompt:**
- Path to `diff.patch` (git diff between old and new upstream SHAs for this skill's upstream path).
- Path to the old SKILL.md (pre-sync snapshot).
- Path to the new SKILL.md (post-sync).
- The upstream path (e.g. `navigation/navigation-3`).

**Process:**
1. Read the diff patch and the new SKILL.md.
2. Identify the semantic changes: new guidance, deprecations, added/removed references, corrected API surface, changed sequencing of steps.
3. Ignore purely cosmetic changes (whitespace, wording polish) unless they alter the intent.
4. Consider: does the change likely require the skill's description to be revisited? (E.g. a renamed guidance section may deserve a new trigger phrase.)

**Output (markdown, 3-8 bullets):**
- Start each bullet with a verb: `Added ...`, `Clarified ...`, `Removed ...`, `Corrected ...`.
- Be Android-specific. Jargon allowed: Compose, Hilt, backstack, baseline profile, R8, edge-to-edge, insets.
- No file names, no line numbers, no diff mechanics.
- End with a single line: `Description review: yes` or `Description review: no` — flagging whether our trigger description probably needs a manual look.

**Size target:** under 200 words total.
```

- [ ] **Step 4: Register android-sync in marketplace.json**

Edit `.claude-plugin/marketplace.json` (replace the empty `"plugins": []` array):

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "claude-android-plugins",
  "description": "Claude Code plugins for Android development (Kotlin, Compose, KMP, Navigation, Performance)",
  "owner": {
    "name": "appascal"
  },
  "plugins": [
    {
      "name": "android-sync",
      "description": "Keeps android/skills-derived plugins in sync with upstream. Exposes /android-sync:update.",
      "version": "0.1.0",
      "author": { "name": "DronPascal" },
      "source": "./plugins/android-sync",
      "category": "productivity"
    }
  ]
}
```

- [ ] **Step 5: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-sync/.claude-plugin/plugin.json \
        plugins/android-sync/skills/update/SKILL.md \
        plugins/android-sync/agents/upstream-diff-analyzer.md \
        .claude-plugin/marketplace.json
git -c commit.gpgsign=false commit -m "feat(android-sync): plugin.json, /update skill, diff-analyzer agent"
```

---

## Task 6: Port android-core Skills (navigation-3, edge-to-edge)

**Files:**
- Create: `plugins/android-core/.claude-plugin/plugin.json`
- Create: `plugins/android-core/CLAUDE.md`
- Create: `plugins/android-core/skills/navigation-3/SKILL.md` + `references/` (via port_skill.py)
- Create: `plugins/android-core/skills/edge-to-edge/SKILL.md` (via port_skill.py)
- Modify: `.claude-plugin/marketplace.json` (add android-core entry)

- [ ] **Step 1: Create plugin.json**

Create `plugins/android-core/.claude-plugin/plugin.json`:

```json
{
  "name": "android-core",
  "version": "0.1.0",
  "description": "Always-on Android development skills: Navigation-3, edge-to-edge. Adapted from github.com/android/skills (Apache 2.0).",
  "author": { "name": "DronPascal" },
  "repository": {
    "type": "git",
    "url": "https://github.com/DronPascal/claude-android-plugins",
    "directory": "plugins/android-core"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Create plugin-level CLAUDE.md**

Create `plugins/android-core/CLAUDE.md`:

```markdown
# android-core

Always-on Android skills. Content ported from [android/skills](https://github.com/android/skills) under Apache 2.0.

Our frontmatter (trigger phrases + `upstream` block) is maintained manually; skill body and references are refreshed by `/android-sync:update`.
```

- [ ] **Step 3: Port navigation-3**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path navigation/navigation-3 \
  --target-plugin android-core \
  --name navigation-3 \
  --marketplace .
```

Expected output: `Ported: navigation/navigation-3 → plugins/android-core/skills/navigation-3/`.

- [ ] **Step 4: Rewrite navigation-3 description**

Edit `plugins/android-core/skills/navigation-3/SKILL.md`. Replace the `description: >` block (multiline after `description: >`, before `upstream:`) with:

```yaml
description: >
  This skill should be used when the user asks about "Navigation 3",
  "Nav3", "Compose navigation", "type-safe destinations", "back stack
  in Compose", "deep links", "multiple back stacks", "passing arguments
  between screens", or mentions Jetpack Navigation 3 APIs, saveable back
  stack, or migrating from Navigation 2 to Navigation 3.
```

Verify the surrounding fields (`name`, `upstream`) are untouched.

- [ ] **Step 5: Port edge-to-edge**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path system/edge-to-edge \
  --target-plugin android-core \
  --name edge-to-edge \
  --marketplace .
```

- [ ] **Step 6: Rewrite edge-to-edge description**

Edit `plugins/android-core/skills/edge-to-edge/SKILL.md`. Replace the `description: >` block with:

```yaml
description: >
  This skill should be used when the user asks about "edge-to-edge",
  "handle system bars", "status bar insets", "navigation bar insets",
  "WindowInsets", "enableEdgeToEdge", "drawing behind system bars",
  "Android 15 mandatory edge-to-edge", or mentions making a UI extend
  under status/navigation bars, Android 35 (API 35) edge-to-edge
  requirements, or safe-area handling in Compose.
```

- [ ] **Step 7: Register android-core in marketplace.json**

Edit `.claude-plugin/marketplace.json` — add this entry to the `plugins` array (after android-sync):

```json
    {
      "name": "android-core",
      "description": "Always-on Android skills: Navigation-3, edge-to-edge. Adapted from android/skills (Apache 2.0).",
      "version": "0.1.0",
      "author": { "name": "DronPascal" },
      "source": "./plugins/android-core",
      "category": "development"
    }
```

- [ ] **Step 8: Verify structure**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
find plugins/android-core -type f | sort
```

Expected: at minimum the `plugin.json`, `CLAUDE.md`, two `SKILL.md` files, and multiple files under both skills' `references/` directories.

```bash
grep -c 'TODO: rewrite' plugins/android-core/skills/*/SKILL.md
```

Expected: `0` for each file (both descriptions rewritten).

- [ ] **Step 9: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-core .claude-plugin/marketplace.json NOTICE.md
git -c commit.gpgsign=false commit -m "feat(android-core): port navigation-3 and edge-to-edge skills"
```

---

## Task 7: Port android-migrations Skills

**Files:**
- Create: `plugins/android-migrations/.claude-plugin/plugin.json`
- Create: `plugins/android-migrations/CLAUDE.md`
- Create: `plugins/android-migrations/skills/migrate-xml-views-to-compose/` (ported)
- Create: `plugins/android-migrations/skills/agp-9-upgrade/` (ported)
- Create: `plugins/android-migrations/skills/play-billing-upgrade/` (ported)
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create plugin.json**

Create `plugins/android-migrations/.claude-plugin/plugin.json`:

```json
{
  "name": "android-migrations",
  "version": "0.1.0",
  "description": "On-demand Android migration skills: XML→Compose, AGP-9 upgrade, Play Billing upgrade. Adapted from android/skills (Apache 2.0).",
  "author": { "name": "DronPascal" },
  "repository": {
    "type": "git",
    "url": "https://github.com/DronPascal/claude-android-plugins",
    "directory": "plugins/android-migrations"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Create plugin-level CLAUDE.md**

Create `plugins/android-migrations/CLAUDE.md`:

```markdown
# android-migrations

On-demand migration skills. Install this plugin on projects where you are actively migrating:
- XML Views → Jetpack Compose
- Android Gradle Plugin 8.x → 9.x
- Play Billing Library version upgrade

Content ported from [android/skills](https://github.com/android/skills) under Apache 2.0. `/android-sync:update` refreshes bodies and references.
```

- [ ] **Step 3: Port migrate-xml-views-to-compose**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path jetpack-compose/migration/migrate-xml-views-to-jetpack-compose \
  --target-plugin android-migrations \
  --name migrate-xml-views-to-compose \
  --marketplace .
```

- [ ] **Step 4: Rewrite migrate-xml-views-to-compose description**

Edit `plugins/android-migrations/skills/migrate-xml-views-to-compose/SKILL.md`. Replace `description: >` block with:

```yaml
description: >
  This skill should be used when the user asks to "migrate XML to Compose",
  "convert XML views to Jetpack Compose", "migrate legacy Views",
  "adopt Compose incrementally", "replace XML layouts with Compose",
  "Compose interop with View", or mentions XML-to-Compose migration,
  ComposeView, AndroidView, or incremental Compose adoption.
```

- [ ] **Step 5: Port agp-9-upgrade**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path build/agp/agp-9-upgrade \
  --target-plugin android-migrations \
  --name agp-9-upgrade \
  --marketplace .
```

- [ ] **Step 6: Rewrite agp-9-upgrade description**

Edit `plugins/android-migrations/skills/agp-9-upgrade/SKILL.md`. Replace `description: >` block with:

```yaml
description: >
  This skill should be used when the user asks to "upgrade AGP to 9",
  "migrate to Android Gradle Plugin 9", "AGP 9 upgrade", "Gradle 9
  migration", or mentions Android Gradle Plugin 8→9 migration, deprecated
  build configurations, namespaces in build.gradle, or AGP 9 breaking
  changes.
```

- [ ] **Step 7: Port play-billing-upgrade**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path play/play-billing-library-version-upgrade \
  --target-plugin android-migrations \
  --name play-billing-upgrade \
  --marketplace .
```

- [ ] **Step 8: Rewrite play-billing-upgrade description**

Edit `plugins/android-migrations/skills/play-billing-upgrade/SKILL.md`. Replace `description: >` block with:

```yaml
description: >
  This skill should be used when the user asks to "upgrade Play Billing",
  "migrate Play Billing Library", "Play Billing version upgrade",
  "BillingClient upgrade", or mentions migrating Google Play Billing
  between major versions, in-app subscription API changes, or
  ProductDetails/SkuDetails migration.
```

- [ ] **Step 9: Register android-migrations in marketplace.json**

Edit `.claude-plugin/marketplace.json` — add this entry:

```json
    {
      "name": "android-migrations",
      "description": "Android migration skills: XML→Compose, AGP-9, Play Billing. Adapted from android/skills (Apache 2.0).",
      "version": "0.1.0",
      "author": { "name": "DronPascal" },
      "source": "./plugins/android-migrations",
      "category": "development"
    }
```

- [ ] **Step 10: Verify**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
grep -c 'TODO: rewrite' plugins/android-migrations/skills/*/SKILL.md
```

Expected: `0` for each line (3 files, all zero).

- [ ] **Step 11: Commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git add plugins/android-migrations .claude-plugin/marketplace.json NOTICE.md
git -c commit.gpgsign=false commit -m "feat(android-migrations): port XML→Compose, AGP-9, Play Billing skills"
```

---

## Task 8: Port android-performance (r8-analyzer)

**Files:**
- Create: `plugins/android-performance/.claude-plugin/plugin.json`
- Create: `plugins/android-performance/CLAUDE.md`
- Create: `plugins/android-performance/skills/r8-analyzer/` (ported)
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create plugin.json**

Create `plugins/android-performance/.claude-plugin/plugin.json`:

```json
{
  "name": "android-performance",
  "version": "0.1.0",
  "description": "Android performance skills: R8 analyzer (more to come). Adapted from android/skills (Apache 2.0).",
  "author": { "name": "DronPascal" },
  "repository": {
    "type": "git",
    "url": "https://github.com/DronPascal/claude-android-plugins",
    "directory": "plugins/android-performance"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Create plugin-level CLAUDE.md**

Create `plugins/android-performance/CLAUDE.md`:

```markdown
# android-performance

Android performance skills. Currently ships with R8 analyzer; more skills (baseline profiles, profilers, macrobenchmarks) will be added over time.

Content ported from [android/skills](https://github.com/android/skills) under Apache 2.0.
```

- [ ] **Step 3: Port r8-analyzer**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/port_skill.py \
  --upstream /tmp/android-skills-inspect \
  --upstream-path performance/r8-analyzer \
  --target-plugin android-performance \
  --name r8-analyzer \
  --marketplace .
```

- [ ] **Step 4: Rewrite r8-analyzer description**

Edit `plugins/android-performance/skills/r8-analyzer/SKILL.md`. Replace `description: >` block with:

```yaml
description: >
  This skill should be used when the user asks about "R8 analyzer",
  "shrinking report", "analyze R8 output", "minification issues",
  "keep rules", "ProGuard rules debugging", "R8 diagnostics", or
  mentions missing classes in release builds, shrinker warnings,
  or investigating app size regressions.
```

- [ ] **Step 5: Register android-performance in marketplace.json**

Edit `.claude-plugin/marketplace.json` — add this entry:

```json
    {
      "name": "android-performance",
      "description": "Android performance skills (R8 analyzer). Adapted from android/skills (Apache 2.0).",
      "version": "0.1.0",
      "author": { "name": "DronPascal" },
      "source": "./plugins/android-performance",
      "category": "development"
    }
```

- [ ] **Step 6: Verify and commit**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
grep -c 'TODO: rewrite' plugins/android-performance/skills/r8-analyzer/SKILL.md
# Expected: 0
git add plugins/android-performance .claude-plugin/marketplace.json NOTICE.md
git -c commit.gpgsign=false commit -m "feat(android-performance): port r8-analyzer skill"
```

---

## Task 9: sync_upstream.py

**Files:**
- Create: `plugins/android-sync/scripts/sync_upstream.py`

Contract:
```
python3 sync_upstream.py --marketplace <dir> [--dry-run] [--plugin <name>] [--force]
```

Effects:
1. Aborts if marketplace git tree dirty (unless `--force` or `--dry-run`).
2. Clones/updates upstream at `/tmp/android-skills-upstream/`.
3. Parses NOTICE.md → list of ported skills.
4. For each skill (optionally filtered by `--plugin`):
   - If `last_commit` == upstream HEAD SHA → skip.
   - Else: compute `git diff <last_commit>..HEAD -- <upstream_path>`. If non-empty, replace our body with the upstream body, rsync references, update `upstream.commit` in our frontmatter, record diff patch.
5. Determines which plugins need a version bump.
6. Writes artifacts to `/tmp/android-sync-run-<ts>/` including `summary.md`.
7. In non-dry-run mode: bumps `plugin.json` version numbers, updates NOTICE.md SHAs.
8. Prints summary.

- [ ] **Step 1: Write sync_upstream.py**

Create `plugins/android-sync/scripts/sync_upstream.py`:

```python
#!/usr/bin/env python3
"""Sync ported skills in claude-android-plugins from android/skills upstream.

See docs/superpowers/specs/2026-04-18-android-plugins-adaptation-design.md
for the algorithm.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import frontmatter
import notice


UPSTREAM_URL = "https://github.com/android/skills.git"
UPSTREAM_CLONE = Path("/tmp/android-skills-upstream")


def sh(cmd: List[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def ensure_upstream() -> str:
    """Clone or fetch upstream. Return HEAD SHA."""
    if not (UPSTREAM_CLONE / ".git").exists():
        if UPSTREAM_CLONE.exists():
            shutil.rmtree(UPSTREAM_CLONE)
        sh(["git", "clone", "--depth", "50", UPSTREAM_URL, str(UPSTREAM_CLONE)])
    else:
        sh(["git", "fetch", "--depth", "50", "origin"], cwd=UPSTREAM_CLONE)
        sh(["git", "reset", "--hard", "origin/main"], cwd=UPSTREAM_CLONE)
    return sh(["git", "rev-parse", "HEAD"], cwd=UPSTREAM_CLONE).stdout.strip()


def check_clean(marketplace: Path, force: bool) -> None:
    out = sh(["git", "-C", str(marketplace), "status", "--porcelain"]).stdout
    if out.strip() and not force:
        sys.exit(f"ERROR: marketplace working tree is dirty. Commit or use --force.\n{out}")


def compute_diff(old_sha: str, new_sha: str, upstream_path: str) -> str:
    """Return git diff between old..new limited to upstream_path. Empty string if equal."""
    if old_sha == new_sha:
        return ""
    result = sh(
        ["git", "diff", f"{old_sha}..{new_sha}", "--", upstream_path],
        cwd=UPSTREAM_CLONE,
        check=False,
    )
    return result.stdout


def refs_changed(old_sha: str, new_sha: str, upstream_path: str) -> bool:
    """Return True if the `references/` subtree changed between old_sha and new_sha."""
    if old_sha == new_sha:
        return False
    refs_subpath = f"{upstream_path.rstrip('/')}/references"
    result = sh(
        ["git", "diff", "--quiet", f"{old_sha}..{new_sha}", "--", refs_subpath],
        cwd=UPSTREAM_CLONE, check=False,
    )
    return result.returncode != 0  # non-zero means changed


def body_changed(old_sha: str, new_sha: str, upstream_path: str) -> bool:
    """Return True if SKILL.md body changed between old_sha and new_sha."""
    skill_subpath = f"{upstream_path.rstrip('/')}/SKILL.md"
    result = sh(
        ["git", "diff", "--quiet", f"{old_sha}..{new_sha}", "--", skill_subpath],
        cwd=UPSTREAM_CLONE, check=False,
    )
    return result.returncode != 0


def rsync_refs(src: Path, dst: Path) -> None:
    """rsync -a --delete src/ dst/ (both dirs). Skip if src missing."""
    if not src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        return
    dst.mkdir(parents=True, exist_ok=True)
    sh(["rsync", "-a", "--delete", f"{src}/", f"{dst}/"])


def bump_plugin_version(plugin_json_path: Path, level: str) -> Tuple[str, str]:
    """Bump version in plugin.json. level ∈ {patch, minor, major}. Returns (old, new)."""
    data = json.loads(plugin_json_path.read_text())
    old = data.get("version", "0.0.0")
    major, minor, patch = (int(x) for x in old.split("."))
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    data["version"] = new
    plugin_json_path.write_text(json.dumps(data, indent=2) + "\n")
    return old, new


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marketplace", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plugin", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    marketplace: Path = args.marketplace.resolve()
    check_clean(marketplace, force=args.force or args.dry_run)

    print(f"Upstream: {UPSTREAM_URL}")
    head_sha = ensure_upstream()
    print(f"Upstream HEAD: {head_sha}")

    notice_path = marketplace / "NOTICE.md"
    notice_text = notice_path.read_text()
    rows = notice.parse(notice_text)
    if args.plugin:
        rows = [r for r in rows if r["plugin"] == args.plugin]
    if not rows:
        print("No ported skills found (check NOTICE.md / --plugin filter).")
        return 0

    run_dir = Path(f"/tmp/android-sync-run-{int(time.time())}")
    run_dir.mkdir(parents=True, exist_ok=True)

    changed: List[Dict[str, str]] = []
    for row in rows:
        plugin = row["plugin"]
        skill = row["skill"]
        path = row["upstream_path"].rstrip("/")
        old_sha = row["commit"]

        if old_sha == head_sha:
            continue
        if not (body_changed(old_sha, head_sha, path) or refs_changed(old_sha, head_sha, path)):
            # Commits advanced but this skill didn't change — only SHA bump.
            changed.append({**row, "new_commit": head_sha, "body_changed": False, "refs_changed": False})
            continue

        bchanged = body_changed(old_sha, head_sha, path)
        rchanged = refs_changed(old_sha, head_sha, path)

        skill_dir_our = marketplace / "plugins" / plugin / "skills" / skill
        skill_md_our = skill_dir_our / "SKILL.md"

        # Save pre-sync snapshot for the agent.
        snapshot_old = run_dir / f"{plugin}__{skill}.old.SKILL.md"
        snapshot_old.write_text(skill_md_our.read_text())

        # Replace body using upstream at HEAD.
        upstream_skill = (UPSTREAM_CLONE / path / "SKILL.md").read_text()
        upstream_body = frontmatter.extract_body(upstream_skill)
        our_text = skill_md_our.read_text()
        our_fm, _ = frontmatter.split(our_text)
        our_text_new = our_fm + upstream_body
        # Update upstream.commit.
        our_text_new = frontmatter.update_upstream_commit(our_text_new, head_sha)

        if not args.dry_run:
            skill_md_our.write_text(our_text_new)
            if rchanged:
                rsync_refs(
                    UPSTREAM_CLONE / path / "references",
                    skill_dir_our / "references",
                )

        # Save diff and new snapshot.
        diff_text = compute_diff(old_sha, head_sha, path)
        (run_dir / f"{plugin}__{skill}.diff.patch").write_text(diff_text)
        (run_dir / f"{plugin}__{skill}.new.SKILL.md").write_text(our_text_new)

        changed.append({
            **row,
            "new_commit": head_sha,
            "body_changed": bchanged,
            "refs_changed": rchanged,
        })

    # Version bumps + NOTICE update (non-dry-run).
    bumps: Dict[str, Tuple[str, str]] = {}
    if changed and not args.dry_run:
        plugins_to_bump: Dict[str, str] = {}
        for c in changed:
            level = "minor" if c.get("body_changed") else "patch"
            prev = plugins_to_bump.get(c["plugin"])
            # minor wins over patch.
            if prev is None or (prev == "patch" and level == "minor"):
                plugins_to_bump[c["plugin"]] = level
        for plugin, level in plugins_to_bump.items():
            pj = marketplace / "plugins" / plugin / ".claude-plugin" / "plugin.json"
            old, new = bump_plugin_version(pj, level)
            bumps[plugin] = (old, new)
        for c in changed:
            notice_text = notice.upsert(
                notice_text,
                plugin=c["plugin"], skill=c["skill"],
                upstream_path=c["upstream_path"],
                commit=head_sha,
            )
        notice_path.write_text(notice_text)

    # Summary.
    summary_lines = [f"# Sync run @ {time.strftime('%Y-%m-%d %H:%M:%S')}",
                     f"Upstream HEAD: {head_sha}", ""]
    if args.dry_run:
        summary_lines.append("**Mode:** dry-run (no files written)")
    if not changed:
        summary_lines.append("No skills needed sync.")
    else:
        summary_lines.append(f"Changed skills ({len(changed)}):")
        for c in changed:
            flags = []
            if c.get("body_changed"):
                flags.append("body")
            if c.get("refs_changed"):
                flags.append("refs")
            if not flags:
                flags.append("sha-only")
            summary_lines.append(f"- `{c['plugin']}/{c['skill']}` ({', '.join(flags)})")
        if bumps:
            summary_lines.append("")
            summary_lines.append("Plugin bumps:")
            for plugin, (old, new) in bumps.items():
                summary_lines.append(f"- {plugin}: {old} → {new}")

    summary_path = run_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n")
    print(f"Artifacts: {run_dir}")
    print(f"Summary: {summary_path}")
    print("---")
    print("\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Quick smoke check — dry-run against the freshly ported state**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/sync_upstream.py --marketplace . --dry-run
```

Expected output ends with something like:
```
No skills needed sync.
```
…because we just ported everything at the same upstream HEAD SHA in Tasks 6-8.

- [ ] **Step 3: Commit**

```bash
git add plugins/android-sync/scripts/sync_upstream.py
git -c commit.gpgsign=false commit -m "feat(android-sync): sync_upstream.py — full marketplace sync"
```

---

## Task 10: End-to-End Sync Test (Artificial Rollback)

Verify that the sync pipeline actually replaces bodies / references and updates NOTICE + plugin.json correctly. We simulate upstream movement by rolling one of our `upstream.commit` fields back to an older SHA.

**Files (temporary edits, will be committed as sync result):**
- Modify: `plugins/android-core/skills/navigation-3/SKILL.md` (revert commit field)
- Sync will modify the body, refs, NOTICE.md, and android-core/plugin.json version.

- [ ] **Step 1: Find a predecessor commit in upstream**

```bash
cd /tmp/android-skills-upstream 2>/dev/null || cd /tmp/android-skills-inspect
git log --oneline -20 -- navigation/navigation-3/SKILL.md
```

Pick a SHA older than HEAD (or pick the commit before HEAD if only two exist). Record it as `OLD_SHA`.

- [ ] **Step 2: Artificially downgrade our navigation-3 commit**

Edit `plugins/android-core/skills/navigation-3/SKILL.md`:

Replace the `  commit: <current-sha>` line inside the `upstream:` block with `  commit: <OLD_SHA>` (use the SHA from Step 1).

- [ ] **Step 3: Run dry-run**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
python3 plugins/android-sync/scripts/sync_upstream.py --marketplace . --dry-run
```

Expected: summary lists `android-core/navigation-3 (body, refs)` or at least one of those tags. Working tree dirtiness check passes because `--dry-run` bypasses it.

- [ ] **Step 4: Restore the commit and run real sync**

Revert the edit from Step 2 with `git checkout -- plugins/android-core/skills/navigation-3/SKILL.md`. Then redo the downgrade (so tree is dirty with only that one-line change):

```bash
git checkout -- plugins/android-core/skills/navigation-3/SKILL.md
# redo the same edit as Step 2 (commit: <OLD_SHA>)
```

Now run with `--force` (tree is dirty):

```bash
python3 plugins/android-sync/scripts/sync_upstream.py --marketplace . --force
```

Expected:
- Summary shows the skill as changed.
- `android-core` plugin.json version bumped (0.1.0 → 0.1.1 for refs-only; 0.2.0 for body).
- NOTICE.md has the new SHA.

- [ ] **Step 5: Verify end state**

```bash
# Commit in frontmatter should be back to current HEAD.
grep 'commit:' plugins/android-core/skills/navigation-3/SKILL.md

# NOTICE updated.
grep 'navigation-3' NOTICE.md

# plugin.json bumped.
grep '"version"' plugins/android-core/.claude-plugin/plugin.json
```

- [ ] **Step 6: Reset to pre-test state**

The sync may leave `android-core/plugin.json` bumped and references/body refreshed unnecessarily (we just re-read what was already current). Revert:

```bash
git checkout -- plugins/android-core NOTICE.md
```

- [ ] **Step 7: Fix any bugs found, commit the fixes (if any)**

If Steps 3-5 surfaced bugs in `sync_upstream.py`, fix them, rerun the test, and commit:

```bash
git add plugins/android-sync/scripts/sync_upstream.py
git -c commit.gpgsign=false commit -m "fix(android-sync): <short description of fix>"
```

If no bugs found, skip this step.

---

## Task 11: Push + Marketplace Installation

**Files:**
- No new files. Git push + Claude Code installation.

- [ ] **Step 1: Final sanity check**

```bash
cd /Users/appascal/Personal/obsidian/pascal-vault/programs/claude-android-plugins
git status
git log --oneline
find plugins -name plugin.json | xargs -I {} python3 -c "import json; d=json.load(open('{}')); print('{}:', d['name'], d['version'])"
```

Expected: clean tree, all 4 plugins present with version 0.1.0, commits for each task.

- [ ] **Step 2: Push to GitHub**

```bash
git push -u origin main
```

Expected: push succeeds. If branch naming differs (`master` vs `main`), align with the remote's default — `git branch -M main` first.

- [ ] **Step 3: Verify repo is public**

Open `https://github.com/DronPascal/claude-android-plugins` in a browser. Must be accessible without authentication. If private, toggle to public in repo settings.

- [ ] **Step 4: Install in Claude Code**

Run in Claude Code:

```
/plugin marketplace add DronPascal/claude-android-plugins
/plugin install android-sync@claude-android-plugins
/plugin install android-core@claude-android-plugins
```

Expected: both plugins install cleanly.

- [ ] **Step 5: Trigger tests**

In a fresh Claude Code session, prompt:

> «Помоги настроить edge-to-edge в Compose»

Expected: the `edge-to-edge` skill description matches, Claude auto-invokes the skill.

Then:

> `/android-sync:update --dry-run`

Expected: summary prints "No skills needed sync."

- [ ] **Step 6: Done**

Marketplace live. No final commit needed (all work already committed). Document in the main claude-plugins repo README if desired — but that's a separate task.

---

## Self-Review Notes

**Spec coverage audit:**
- 4 plugins (android-core / -migrations / -performance / -sync): Tasks 5, 6, 7, 8.
- Frontmatter rewrite rules: Task 2 (`frontmatter.build`) + Tasks 6-8 Step N (manual description rewrite).
- NOTICE.md as source of truth: Tasks 1, 3, 4 (auto-updated by `port_skill.py` + `sync_upstream.py`).
- Attribution pointer in every SKILL.md: Task 2 (`frontmatter.build`) adds it.
- upstream-diff-analyzer agent: Task 5.
- `/android-sync:update` skill: Task 5.
- Artificial SHA-rollback e2e test: Task 10.
- Public repo + `/plugin marketplace add`: Task 11.

**Known simplifications vs spec:**
- Spec's agent-parallel changelog dispatch is described in the SKILL.md body (Task 5). The `sync_upstream.py` itself only writes diff artifacts; the skill invokes the agent. This keeps the script testable standalone.
- `--plugin <name>` and `--force` flags work; other edge cases (missing upstream_path, renamed skills) surface as Python exceptions rather than graceful warnings — acceptable for v0.1.0 personal tool.

**Out-of-scope (spec's "Open questions"):**
- CI / scheduled sync — not in this plan.
- Full bash test suite (insights-keeper-style) — `frontmatter.py` and `notice.py` self-tests + `smoke_port_skill.sh` + Task 10 e2e are sufficient for v0.1.0.
