#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v brew >/dev/null 2>&1; then
  echo 'Install Homebrew from https://brew.sh, then run this script again.'
  exit 1
fi
# Reuse installed tools. A routine app setup must not upgrade other Homebrew apps.
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1
export HOMEBREW_NO_INSTALL_CLEANUP=1
for formula in python@3.12 ffmpeg; do
  if ! brew list --versions "$formula" >/dev/null 2>&1; then
    brew install "$formula"
  fi
done
REEF_PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
"$REEF_PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
echo 'Ready. Start with: .venv/bin/python -m reefwatch'
echo 'Then open http://127.0.0.1:8765 on this Mac.'
