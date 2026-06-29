#!/bin/bash
# PreToolUse hook: warn if committing plugin changes without version bump
# Checks staged files before git commit runs

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
echo "$COMMAND" | grep -q "git commit" || exit 0

# Check staged files
STAGED=$(git diff --cached --name-only 2>/dev/null)
[ -z "$STAGED" ] && exit 0

# Any plugin content changes? (exclude version files themselves)
PLUGIN_CHANGES=$(echo "$STAGED" | grep "^plugins/" | grep -v "plugin\.json" | grep -v "marketplace\.json") || true
[ -z "$PLUGIN_CHANGES" ] && exit 0

# Plugin files staged — are version files also staged?
HAS_PLUGIN_JSON=$(echo "$STAGED" | grep "\.claude-plugin/plugin\.json") || true
HAS_MARKETPLACE=$(echo "$STAGED" | grep "marketplace\.json") || true

if [ -z "$HAS_PLUGIN_JSON" ] || [ -z "$HAS_MARKETPLACE" ]; then
    MISSING=""
    [ -z "$HAS_PLUGIN_JSON" ] && MISSING="plugin.json"
    [ -z "$HAS_MARKETPLACE" ] && MISSING="${MISSING:+$MISSING + }marketplace.json"
    echo "⚠️ BLOCKED: Plugin files changed but ${MISSING} not staged. Bump version before committing." >&2
    exit 2
fi

exit 0
