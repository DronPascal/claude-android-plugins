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
