#!/usr/bin/env bash
# Installer for Cymbal Bank Capstone Antigravity Plugin (Agents, Skills, Rules & Scripts)

set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${1:-/workspace}"

echo "Installing Cymbal Bank Capstone Agents, Skills, and Rules..."

# 1. Install into /workspace/.gemini/ and /workspace/_agents/
mkdir -p "${WORKSPACE_DIR}/.gemini" "${WORKSPACE_DIR}/_agents"
cp -r "${BUNDLE_DIR}/agents" "${BUNDLE_DIR}/skills" "${BUNDLE_DIR}/rules" "${WORKSPACE_DIR}/.gemini/"
cp -r "${BUNDLE_DIR}/agents" "${BUNDLE_DIR}/skills" "${BUNDLE_DIR}/rules" "${WORKSPACE_DIR}/_agents/"
cp "${BUNDLE_DIR}/rules/AGENTS.md" "${WORKSPACE_DIR}/AGENTS.md"
chmod +x "${WORKSPACE_DIR}/.gemini/skills/"*/scripts/* 2>/dev/null || true

# 2. Install as a global Antigravity plugin in ~/.gemini/config/plugins/cymbal-capstone
mkdir -p "${HOME}/.gemini/config/plugins/cymbal-capstone"
cp -r "${BUNDLE_DIR}/"* "${HOME}/.gemini/config/plugins/cymbal-capstone/"
chmod +x "${HOME}/.gemini/config/plugins/cymbal-capstone/skills/"*/scripts/* 2>/dev/null || true

echo "Successfully installed Cymbal Bank Capstone bundle into:"
echo "  - ${WORKSPACE_DIR}/.gemini/{agents,skills,rules}"
echo "  - ${WORKSPACE_DIR}/AGENTS.md"
echo "  - ${HOME}/.gemini/config/plugins/cymbal-capstone"
