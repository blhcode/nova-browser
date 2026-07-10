let browserData = Nova.loadData();
let currentUrl = "";
let currentTitle = "";

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name) || "";
}

function applyBrowserTheme() {
  NovaThemes.applyTheme(browserData.theme);
}

function updateStarButton() {
  const star = document.getElementById("btn-star");
  if (NovaBookmarks.isBookmarked(browserData, currentUrl)) {
    star.classList.add("starred");
    star.textContent = "★";
    star.title = "Bookmarked";
  } else {
    star.classList.remove("starred");
    star.textContent = "☆";
    star.title = "Add bookmark";
  }
}

function setUrlBar(url) {
  currentUrl = Nova.normalizeUrl(url);
  document.getElementById("url-input").value = currentUrl;
  updateStarButton();
}

function navigate(url) {
  const normalized = Nova.normalizeUrl(url);
  if (!normalized) return;
  setUrlBar(normalized);
  Nova.getBridge().navigateInBrowser(normalized);
}

document.getElementById("btn-back").addEventListener("click", () => {
  const bridge = Nova.getBridge();
  if (bridge.browserGoBack) bridge.browserGoBack();
});

document.getElementById("btn-forward").addEventListener("click", () => {
  const bridge = Nova.getBridge();
  if (bridge.browserGoForward) bridge.browserGoForward();
});

document.getElementById("btn-home").addEventListener("click", () => {
  Nova.getBridge().goHome();
});

document.getElementById("btn-reload").addEventListener("click", () => {
  if (currentUrl) {
    Nova.getBridge().navigateInBrowser(currentUrl);
  }
});

document.getElementById("btn-star").addEventListener("click", async () => {
  const existing = browserData.bookmarks.find(
    (b) => Nova.normalizeUrl(b.url) === Nova.normalizeUrl(currentUrl)
  );
  if (existing) {
    NovaBookmarks.togglePin(browserData, existing.id);
    browserData = Nova.loadData();
    updateStarButton();
    return;
  }
  const bookmark = await NovaBookmarks.showBookmarkDialog({
    title: "Add bookmark",
    bookmark: {
      title: currentTitle || NovaFavicon.getDomain(currentUrl),
      url: currentUrl,
      pinned: true,
    },
  });
  if (bookmark) {
    NovaBookmarks.upsertBookmark(browserData, bookmark);
    browserData = Nova.loadData();
    updateStarButton();
  }
});

document.getElementById("url-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    navigate(e.target.value);
  }
});

window.onBrowserPageLoaded = function (title, url) {
  currentTitle = title || "";
  if (url) setUrlBar(url);
};

const initialUrl = getQueryParam("url");
applyBrowserTheme();

if (initialUrl) {
  navigate(initialUrl);
} else {
  document.getElementById("browser-hint").classList.remove("hidden");
}
