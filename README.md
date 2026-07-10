# Nova Browser

A lightweight cross-platform web browser for **Android** and **desktop Linux**, built around a shared home screen with shortcuts, bookmarks, and themes.

<p align="center">
  <img src="assets/icon/nova.svg" alt="Nova Browser logo" width="96" height="96">
</p>

## Features

- **Home screen shortcuts** — pin, edit, and delete website tiles
- **Bookmarks** — save any page from the URL bar in one tap
- **Themes** — White, Black, Space, and Custom (pick colors + background image)
- **Tabs** — multi-tab browsing on Android and Linux
- **Native shells** — Android WebView and Linux WebKitGTK, sharing one web UI

## Download

| Platform | How to install |
|----------|----------------|
| **Android** | Build `dist/nova-browser.apk` (see below) or install from your app store |
| **Linux (Debian/Ubuntu)** | Build `dist/nova-browser_*.deb` and run `sudo dpkg -i dist/nova-browser_*.deb` |

## Screenshots

The home screen shows your shortcut tiles and theme. The browser chrome includes back/forward, home, new tab, URL bar, and a tab strip.

## Building from source

### Android APK

**Requirements:** JDK 17+, Android SDK (API 34), `ANDROID_HOME` set

```bash
cp android/local.properties.example android/local.properties
# Edit local.properties and set sdk.dir to your Android SDK path

./scripts/build-apk.sh
```

Output: `dist/nova-browser.apk`

### Debian package (desktop Linux)

**Requirements:** Python 3.10+, `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-webkit-6.0` (or `gir1.2-webkit2-4.1` on older distros), `debhelper`, `dpkg-dev`

```bash
./scripts/build-deb.sh
```

Output: `dist/nova-browser_1.0.0_amd64.deb`

Install:

```bash
sudo dpkg -i dist/nova-browser_*.deb
sudo apt-get install -f
```

Launch **Nova Browser** from your app menu.

### Shared UI development

Preview the home screen and settings in a browser:

```bash
./scripts/dev-server.sh
```

Opens **http://localhost:8765/** automatically.

Run the native Linux app in dev mode:

```bash
./scripts/run-linux-dev.sh
```

If the page is blank after changes, reset saved data in the browser console:

```javascript
localStorage.removeItem("nova-browser-data");
location.reload();
```

## Project layout

```
shared/ui/     Shared web UI (home, settings, bookmarks)
android/       Kotlin WebView shell (APK)
linux/         PyGObject WebKitGTK app + Debian packaging
assets/icon/   Nova star logo
scripts/       build-apk.sh, build-deb.sh, dev helpers
```

## Tech stack

- **Shared UI:** HTML, CSS, JavaScript
- **Android:** Kotlin, Android WebView, JSON file storage
- **Linux:** Python, PyGObject, GTK 4, WebKitGTK 6

## Contributing

Issues and pull requests are welcome. Please open an issue before large changes so we can align on direction.

## Author

Isaiah Cannings ([@blhcode](https://github.com/blhcode))
