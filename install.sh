#!/usr/bin/env bash
# Installe le skill suivi-module dans le projet courant (.claude/skills)
# ou pour tous vos projets avec --global (~/.claude/skills).
set -euo pipefail
REPO="${SUIVI_MODULE_REPO:-dav9fulldev/suivi-module-skill}"
REF="${SUIVI_MODULE_REF:-main}"
DEST=".claude/skills"
[ "${1:-}" = "--global" ] && DEST="$HOME/.claude/skills"

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
if [ -n "${SUIVI_MODULE_ARCHIVE:-}" ]; then
  tar -xzf "$SUIVI_MODULE_ARCHIVE" -C "$tmp"
else
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF" | tar -xz -C "$tmp"
fi
src="$(find "$tmp" -maxdepth 3 -type d -path '*/skills/suivi-module' | head -n 1)"
[ -f "$src/SKILL.md" ] || { echo "Skill introuvable dans l'archive de $REPO." >&2; exit 1; }

mkdir -p "$DEST"
rm -rf "$DEST/suivi-module"
cp -R "$src" "$DEST/"
echo "Skill suivi-module installé dans $DEST/suivi-module"
echo "Dans Claude Code, demandez par exemple : « crée le tableau de suivi de mon module »."
