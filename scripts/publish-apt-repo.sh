#!/usr/bin/env bash
# Build .deb and publish to the GitHub-hosted apt repository (gh-pages branch).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APT_ROOT="${ROOT}/apt-repo"
DIST="stable"
COMPONENT="main"
ARCH="all"

"${ROOT}/scripts/build-deb.sh"

VERSION="$(grep '^VERSION=' "${ROOT}/scripts/build-deb.sh" | cut -d'"' -f2)"
DEB="${ROOT}/dist/nova-browser_${VERSION}_${ARCH}.deb"

rm -rf "${APT_ROOT}"
mkdir -p "${APT_ROOT}/pool/main/n/nova-browser"
cp "${DEB}" "${APT_ROOT}/pool/main/n/nova-browser/"

cd "${APT_ROOT}"
mkdir -p "dists/${DIST}/${COMPONENT}/binary-${ARCH}"

dpkg-scanpackages --arch "${ARCH}" pool/ > "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages"
gzip -9 -k -f "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages"

cat > "dists/${DIST}/Release" <<EOF
Origin: Nova Browser
Label: Nova Browser
Suite: ${DIST}
Codename: ${DIST}
Architectures: ${ARCH} amd64
Components: ${COMPONENT}
Description: Nova Browser apt repository
Date: $(date -Ru)
EOF

apt-ftparchive release "dists/${DIST}" >> "dists/${DIST}/Release"

cat > README.md <<'EOF'
# Nova Browser apt repository

Add this repository on Debian/Ubuntu:

```bash
curl -fsSL https://blhcode.github.io/nova-browser-apt/install.sh | bash
```

Or manually:

```bash
echo 'deb [trusted=yes] https://blhcode.github.io/nova-browser-apt stable main' | sudo tee /etc/apt/sources.list.d/nova-browser.list
sudo apt update
sudo apt install nova-browser
```
EOF

cat > install.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo 'deb [trusted=yes] https://blhcode.github.io/nova-browser-apt stable main' | sudo tee /etc/apt/sources.list.d/nova-browser.list
sudo apt-get update
sudo apt-get install -y nova-browser
EOF
chmod +x install.sh

echo "==> Apt repo staged at ${APT_ROOT}"
echo "==> Package: $(basename "${DEB}")"
