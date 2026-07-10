# Nova Browser

A lightweight mobile and desktop web browser with home-screen shortcuts, simple bookmarks, and customizable themes.

## Features

- Website shortcut tiles on the home screen (pin, edit, delete)
- One-tap bookmark saving from the URL bar
- Themes: White, Black, Space, and Custom (colors + background image)
- Android APK and Debian package for desktop Linux

## Build prerequisites

### Android APK

- JDK 17+
- Android SDK (API 34), with `ANDROID_HOME` set
- Copy `android/local.properties.example` to `android/local.properties` and set `sdk.dir`
- Gradle wrapper included under `android/`

```bash
./scripts/build-apk.sh
```

Output: `dist/nova-browser.apk`

### Debian package (desktop Linux)

- Python 3.10+
- `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-webkit-6.0` (or `gir1.2-webkit2-4.1` on older distros)
- `debhelper`, `dpkg-dev`

```bash
./scripts/build-deb.sh
```

Output: `dist/nova-browser_1.0.0_amd64.deb`

### Shared UI development

Use the project dev server (bundles CSS/JS into one page):

```bash
./scripts/dev-server.sh
```

This stops stale servers on port 8080 and opens **http://localhost:8765/** automatically.

Native Linux app:

```bash
./scripts/run-linux-dev.sh
```

If the page is still blank, clear saved data in the browser console:

```javascript
localStorage.removeItem("nova-browser-data");
location.reload();
```

## Project layout

```
shared/ui/     Shared web UI (home, settings, bookmarks)
android/       Kotlin WebView shell (APK)
linux/         PyGObject WebKitGTK app + debian packaging
assets/icon/   Nova logo
scripts/       build-apk.sh, build-deb.sh
```

## Install

**Android:** sideload `dist/nova-browser.apk`

**Debian/Ubuntu:**

```bash
sudo dpkg -i dist/nova-browser_1.0.0_amd64.deb
sudo apt-get install -f
```

Launch **Nova Browser** from your app menu.
