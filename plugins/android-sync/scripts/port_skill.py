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
