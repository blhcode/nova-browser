#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ANDROID="$ROOT/android"
DIST="$ROOT/dist"
ASSETS="$ANDROID/app/src/main/assets/ui"

echo "==> Syncing shared UI into Android assets"
rm -rf "$ASSETS"
mkdir -p "$ASSETS"
cp -a "$ROOT/shared/ui/." "$ASSETS/"

if ! command -v java >/dev/null 2>&1; then
  if [[ -d /usr/lib/jvm ]]; then
    export JAVA_HOME="$(find /usr/lib/jvm -maxdepth 1 -name 'java-*-openjdk-*' -type d | head -1)"
    export PATH="$JAVA_HOME/bin:$PATH"
  fi
fi

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java 17+ is required to build the APK."
  echo "Install OpenJDK, set JAVA_HOME, and ANDROID_HOME, then re-run."
  exit 1
fi

echo "==> Building release APK"
cd "$ANDROID"
chmod +x gradlew
./gradlew assembleRelease --no-daemon

mkdir -p "$DIST"
APK_SRC="$ANDROID/app/build/outputs/apk/release"
APK="$(find "$APK_SRC" -name '*-release.apk' ! -name '*-unsigned.apk' | head -1)"
if [[ -z "$APK" ]]; then
  APK="$(find "$APK_SRC" -name '*.apk' ! -name '*-unsigned.apk' | head -1)"
fi
if [[ -z "$APK" ]]; then
  echo "ERROR: Signed APK not found under $APK_SRC"
  echo "Tip: release builds must be signed. See android/app/build.gradle"
  exit 1
fi
cp "$APK" "$DIST/nova-browser.apk"
echo "==> APK ready: $DIST/nova-browser.apk"
