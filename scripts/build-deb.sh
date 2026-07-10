#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LINUX="$ROOT/linux"
DIST="$ROOT/dist"
VERSION="1.1.0"
ARCH="all"
STAGING="$LINUX/build/deb/nova-browser_${VERSION}_${ARCH}"
PKGDIR="$STAGING/usr"

echo "==> Staging Debian package files"
rm -rf "$LINUX/build/deb"
mkdir -p "$PKGDIR/bin"
mkdir -p "$PKGDIR/lib/nova-browser/nova_browser"
mkdir -p "$PKGDIR/share/nova-browser/ui"
mkdir -p "$PKGDIR/share/applications"
mkdir -p "$PKGDIR/share/icons/hicolor/scalable/apps"
mkdir -p "$STAGING/DEBIAN"

install -m 755 "$LINUX/nova-browser" "$PKGDIR/bin/nova-browser"
cp -a "$LINUX/nova_browser/." "$PKGDIR/lib/nova-browser/nova_browser/"
cp -a "$ROOT/shared/ui/." "$PKGDIR/share/nova-browser/ui/"
install -m 644 "$LINUX/data/nova-browser.desktop" "$PKGDIR/share/applications/"
install -m 644 "$ROOT/assets/icon/nova.svg" "$PKGDIR/share/icons/hicolor/scalable/apps/nova-browser.svg"

cat > "$STAGING/DEBIAN/control" <<EOF
Package: nova-browser
Version: ${VERSION}
Section: web
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1
Maintainer: Isaiah Cannings <isaiahcannings@hotmail.com>
Description: Lightweight web browser with shortcuts and themes
 Nova Browser provides a simple home screen with website shortcuts,
 bookmarks, and customizable backgrounds (white, black, space, custom).
EOF

mkdir -p "$DIST"
OUT="$DIST/nova-browser_${VERSION}_${ARCH}.deb"
dpkg-deb --build "$STAGING" "$OUT"
echo "==> DEB ready: $OUT"
