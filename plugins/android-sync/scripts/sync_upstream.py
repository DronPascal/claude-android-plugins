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
