const SEARCH_ENGINES = {
  google: { name: "Google", url: "https://www.google.com/search?q=" },
  duckduckgo: { name: "DuckDuckGo", url: "https://duckduckgo.com/?q=" },
  bing: { name: "Bing", url: "https://www.bing.com/search?q=" },
  brave: { name: "Brave Search", url: "https://search.brave.com/search?q=" },
};

const DEFAULT_SETTINGS = {
  searchEngine: "google",
  homepage: "",
  javascriptEnabled: true,
  desktopMode: false,
  blockThirdPartyCookies: true,
  zoomLevel: 100,
};

function getSettings(data) {
  const settings = data && data.settings ? data.settings : {};
  return { ...DEFAULT_SETTINGS, ...settings };
}

function getSearchEngine(data) {
  const id = getSettings(data).searchEngine;
  return SEARCH_ENGINES[id] || SEARCH_ENGINES.google;
}

function buildSearchUrl(query, data) {
  return getSearchEngine(data).url + encodeURIComponent(query);
}

function bindToggle(container, selector, data, key, onChange) {
  const el = container.querySelector(selector);
  if (!el) return;
  el.checked = !!getSettings(data)[key];
  el.addEventListener("change", () => {
    data.settings = { ...getSettings(data), [key]: el.checked };
    onChange(data);
  });
}

function bindInput(container, selector, data, key, onChange, parser) {
  const el = container.querySelector(selector);
  if (!el) return;
  el.value = getSettings(data)[key] != null ? getSettings(data)[key] : "";
  el.addEventListener("input", () => {
    const value = parser ? parser(el.value) : el.value;
    data.settings = { ...getSettings(data), [key]: value };
    onChange(data);
  });
}

function renderSettings(container, data, onChange) {
  const s = getSettings(data);
  const themeHost = document.createElement("div");
  themeHost.id = "theme-settings-host";

  container.innerHTML = `
    <section class="settings-section">
      <h3 class="settings-heading">General</h3>
      <div class="form-row">
        <label for="setting-homepage">Homepage</label>
        <input id="setting-homepage" type="url" placeholder="Leave blank for Nova home screen" value="${escapeAttr(s.homepage)}">
      </div>
      <p class="settings-desc">Optional URL to open when starting a new session. Leave empty to show shortcuts.</p>
      <p class="settings-desc">Default search engine</p>
      <div class="settings-options">
        ${Object.entries(SEARCH_ENGINES)
          .map(
            ([id, engine]) => `
          <label class="settings-option">
            <input type="radio" name="search-engine" value="${id}" ${s.searchEngine === id ? "checked" : ""}>
            <span>${engine.name}</span>
          </label>`
          )
          .join("")}
      </div>
      <div class="form-row" style="margin-top:12px">
        <label for="setting-zoom">Default zoom (${s.zoomLevel}%)</label>
        <input id="setting-zoom" type="range" min="75" max="150" step="25" value="${s.zoomLevel}">
      </div>
    </section>

    <section class="settings-section">
      <h3 class="settings-heading">Privacy &amp; security</h3>
      <label class="settings-option">
        <input type="checkbox" id="setting-javascript" ${s.javascriptEnabled ? "checked" : ""}>
        <span>Enable JavaScript</span>
      </label>
      <label class="settings-option">
        <input type="checkbox" id="setting-desktop" ${s.desktopMode ? "checked" : ""}>
        <span>Request desktop sites</span>
      </label>
      <label class="settings-option">
        <input type="checkbox" id="setting-cookies" ${s.blockThirdPartyCookies ? "checked" : ""}>
        <span>Block third-party cookies</span>
      </label>
      <button type="button" class="secondary-btn" id="setting-clear-data" style="margin-top:12px;width:100%">
        Clear browsing data
      </button>
      <p class="settings-desc">Removes cache, cookies, and site data from this device.</p>
    </section>

    <section class="settings-section">
      <h3 class="settings-heading">Appearance</h3>
      <p class="settings-desc">Home screen background theme.</p>
    </section>

    <section class="settings-section">
      <h3 class="settings-heading">About</h3>
      <p class="settings-desc">Nova Browser 1.0.0 — shortcuts, bookmarks, themes, and lightweight browsing.</p>
    </section>
  `;

  container.appendChild(themeHost);
  NovaThemes.renderThemeSettings(themeHost, data, onChange);

  container.querySelectorAll('input[name="search-engine"]').forEach((input) => {
    input.addEventListener("change", () => {
      if (!input.checked) return;
      data.settings = { ...getSettings(data), searchEngine: input.value };
      onChange(data);
      updateOmnibarPlaceholder(data);
    });
  });

  bindInput(container, "#setting-homepage", data, "homepage", onChange);
  bindToggle(container, "#setting-javascript", data, "javascriptEnabled", onChange);
  bindToggle(container, "#setting-desktop", data, "desktopMode", onChange);
  bindToggle(container, "#setting-cookies", data, "blockThirdPartyCookies", onChange);

  const zoom = container.querySelector("#setting-zoom");
  const zoomLabel = container.querySelector('label[for="setting-zoom"]');
  if (zoom) {
    zoom.addEventListener("input", () => {
      data.settings = { ...getSettings(data), zoomLevel: Number(zoom.value) };
      if (zoomLabel) zoomLabel.textContent = `Default zoom (${zoom.value}%)`;
      onChange(data);
    });
  }

  const clearBtn = container.querySelector("#setting-clear-data");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (window.NovaBridge && window.NovaBridge.clearBrowsingData) {
        window.NovaBridge.clearBrowsingData();
      } else {
        localStorage.removeItem("nova-browser-data");
        alert("Browsing data cleared. Reload to reset.");
      }
    });
  }
}

function escapeAttr(str) {
  return String(str != null ? str : "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function updateOmnibarPlaceholder(data) {
  const input = document.getElementById("omnibar-input");
  if (!input) return;
  input.placeholder = `Search ${getSearchEngine(data).name} or enter address`;
}

window.NovaSettings = {
  SEARCH_ENGINES,
  DEFAULT_SETTINGS,
  getSettings,
  getSearchEngine,
  buildSearchUrl,
  renderSettings,
  updateOmnibarPlaceholder,
};
