#!/usr/bin/env bash
# Build Nova Browser Flatpak locally.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${ROOT}/flatpak/io.github.blhcode.NovaBrowser.yml"
BUILD_DIR="${ROOT}/.flatpak-builder"
REPO="${ROOT}/.flatpak-repo"

if ! command -v flatpak-builder &>/dev/null; then
    echo "Error: flatpak-builder not found."
    echo "Install: sudo apt-get install flatpak-builder"
    exit 1
fi

flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --or-update --user -y flathub org.gnome.Platform//48 org.gnome.Sdk//48

flatpak-builder \
    --force-clean \
    --repo="${REPO}" \
    --install \
    --user \
    "${BUILD_DIR}" \
    "${MANIFEST}"

echo ""
echo "Run: flatpak run io.github.blhcode.NovaBrowser"
