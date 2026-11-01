#!/usr/bin/env bash
# Universal SEO & Antigravity Skills Installer
# Installs universal SEO skills and subagents for Google Antigravity & AI Agent harnesses.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
GLOBAL_TARGET="${HOME}/.gemini/config/skills"
LOCAL_TARGET="${REPO_DIR}/.agents/skills"

MODE="global"
if [[ "${1:-}" == "--local" ]]; then
    MODE="local"
fi

if [[ "$MODE" == "global" ]]; then
    TARGET_DIR="$GLOBAL_TARGET"
    echo "Installing Universal SEO skills globally into Antigravity: ${TARGET_DIR}..."
else
    TARGET_DIR="$LOCAL_TARGET"
    echo "Installing Universal SEO skills locally into workspace: ${TARGET_DIR}..."
fi

mkdir -p "$TARGET_DIR"

# Ensure launchers are executable
chmod +x "${REPO_DIR}/scripts/universal-seo" 2>/dev/null || true
chmod +x "${REPO_DIR}/scripts/claude-seo" 2>/dev/null || true
chmod +x "${REPO_DIR}/scripts/agy-seo" 2>/dev/null || true

# Copy skills
count=0
for skill_dir in "${REPO_DIR}/skills"/seo*; do
    if [[ -d "$skill_dir" ]]; then
        skill_name="$(basename "$skill_dir")"
        dest="${TARGET_DIR}/${skill_name}"
        rm -rf "$dest"
        cp -R "$skill_dir" "$dest"
        count=$((count + 1))
    fi
done

echo "Successfully installed ${count} SEO skills to ${TARGET_DIR}!"
echo "Antigravity and Gemini agents can now trigger all SEO skills automatically."
