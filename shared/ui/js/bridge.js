const STORAGE_KEY = "nova-browser-data";

const DEFAULT_DATA = {
  bookmarks: [],
  theme: {
    mode: "space",
    customBgColor: "#0a0a12",
    customAccentColor: "#6b8cff",
    customBgImage: null,
  },
  settings: {
    searchEngine: "google",
    homepage: "",
    javascriptEnabled: true,
    desktopMode: false,
    blockThirdPartyCookies: true,
    zoomLevel: 100,
  },
};

function cloneData(data) {
  return JSON.parse(JSON.stringify(data));
}

function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "id-" + Date.now() + "-" + Math.random().toString(36).slice(2, 9);
}

function createMockBridge() {
  let data = loadFromStorage();

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        return { ...DEFAULT_DATA, ...JSON.parse(raw) };
      }
    } catch (_) {
      /* ignore */
    }
    return cloneData(DEFAULT_DATA);
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  return {
    getData() {
      return JSON.stringify(data);
    },

    saveData(json) {
      const parsed = JSON.parse(json);
      data = { ...DEFAULT_DATA, ...parsed };
      if (parsed.theme) {
        data.theme = { ...DEFAULT_DATA.theme, ...parsed.theme };
      }
      if (parsed.settings) {
        data.settings = { ...DEFAULT_DATA.settings, ...parsed.settings };
      }
      persist();
    },

    openUrl(url) {
      window.location.href = "browser.html?url=" + encodeURIComponent(url);
    },

    goHome() {
      window.location.href = "index.html";
    },

    pickImage() {
      return new Promise((resolve) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.onchange = () => {
          const file = input.files && input.files[0];
          if (!file) {
            resolve("");
            return;
          }
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = () => resolve("");
          reader.readAsDataURL(file);
        };
        input.click();
      });
    },

    navigateInBrowser(url) {
      window.location.href =
        "browser.html?url=" + encodeURIComponent(normalizeUrl(url));
    },

    notifyPageLoaded(title, url) {
      /* mock: no-op */
    },
  };
}

function getBridge() {
  if (window.NovaBridge && typeof window.NovaBridge.getData === "function") {
    return window.NovaBridge;
  }
  if (!window._novaMockBridge) {
    window._novaMockBridge = createMockBridge();
  }
  return window._novaMockBridge;
}

function loadData() {
  const bridge = getBridge();
  try {
    const raw = bridge.getData();
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
    return { ...DEFAULT_DATA, ...parsed, theme: { ...DEFAULT_DATA.theme, ...(parsed.theme || {}) }, settings: { ...DEFAULT_DATA.settings, ...(parsed.settings || {}) } };
  } catch (_) {
    return cloneData(DEFAULT_DATA);
  }
}

function saveData(data) {
  getBridge().saveData(JSON.stringify(data));
}

function normalizeUrl(input, data) {
  const trimmed = (input || "").trim();
  if (!trimmed) return "";
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (trimmed.includes(".") && !trimmed.includes(" ")) {
    return "https://" + trimmed;
  }
  const appData = data || (window.Nova ? Nova.loadData() : DEFAULT_DATA);
  return NovaSettings.buildSearchUrl(trimmed, appData);
}

window.Nova = {
  getBridge,
  loadData,
  saveData,
  normalizeUrl,
  generateId,
  DEFAULT_DATA,
};
