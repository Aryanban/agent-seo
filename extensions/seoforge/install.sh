#!/usr/bin/env bash
# SEOForge Extension Installer
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"

echo "Installing SEOForge extension for Claude SEO / Universal Agent Suite..."

# Link skill into main skills directory if not already linked
mkdir -p "${REPO_ROOT}/skills/seo-seoforge"
cp -R "${SCRIPT_DIR}/skills/seo-seoforge/"* "${REPO_ROOT}/skills/seo-seoforge/"

# Copy to Antigravity global skills if directory exists
if [[ -d "${HOME}/.gemini/config/skills" ]]; then
    mkdir -p "${HOME}/.gemini/config/skills/seo-seoforge"
    cp -R "${SCRIPT_DIR}/skills/seo-seoforge/"* "${HOME}/.gemini/config/skills/seo-seoforge/"
fi

echo "SEOForge extension installed successfully!"
