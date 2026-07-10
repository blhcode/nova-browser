let appData = Nova.loadData();

function refreshUI() {
  appData = Nova.loadData();
  NovaThemes.applyTheme(appData.theme);
  NovaSettings.updateOmnibarPlaceholder(appData);
  renderShortcuts();
  renderBookmarkList();
  NovaSettings.renderSettings(
    document.getElementById("settings-panel"),
    appData,
    (data) => {
      appData = data;
      Nova.saveData(data);
      NovaSettings.updateOmnibarPlaceholder(data);
    }
  );
}

function renderShortcuts() {
  const row = document.getElementById("shortcuts-row");
  const pinned = NovaBookmarks.getPinnedBookmarks(appData.bookmarks);

  if (pinned.length === 0) {
    row.innerHTML = "";
    document.getElementById("shortcuts-empty").classList.remove("hidden");
    return;
  }

  document.getElementById("shortcuts-empty").classList.add("hidden");
  row.innerHTML = "";

  pinned.forEach((bm) => {
    const el = document.createElement("div");
    el.className = "shortcut";

    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "shortcut-tile";
    tile.title = bm.title;
    tile.appendChild(NovaFavicon.createIconElement(bm, "tile"));
    tile.addEventListener("click", (e) => {
      if (e.target.closest(".shortcut-menu-btn")) return;
      Nova.getBridge().openUrl(bm.url);
    });

    const menuBtn = document.createElement("button");
    menuBtn.type = "button";
    menuBtn.className = "shortcut-menu-btn";
    menuBtn.textContent = "⋯";
    menuBtn.setAttribute("aria-label", "Menu");
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      NovaBookmarks.showContextMenu(e.clientX, e.clientY, bm, appData, refreshUI);
    });
    tile.appendChild(menuBtn);

    if (bm.pinned) {
      const badge = document.createElement("span");
      badge.className = "shortcut-badge";
      badge.textContent = "📌";
      badge.setAttribute("aria-label", "Pinned");
      tile.appendChild(badge);
    }

    const label = document.createElement("div");
    label.className = "shortcut-label";
    label.textContent = bm.title;

    el.appendChild(tile);
    el.appendChild(label);
    row.appendChild(el);
  });
}

function renderBookmarkList() {
  const list = document.getElementById("bookmarks-list");
  const all = [...appData.bookmarks].sort((a, b) =>
    (a.title || "").localeCompare(b.title || "")
  );

  if (all.length === 0) {
    list.innerHTML = `<div class="empty-state"><p>No bookmarks yet.</p><p>Tap + to add your first shortcut.</p></div>`;
    return;
  }

  list.innerHTML = "";
  all.forEach((bm) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "bookmark-item";

    const icon = NovaFavicon.createIconElement(bm, "list");
    const text = document.createElement("div");
    text.className = "bookmark-item-text";
    text.innerHTML = `
      <div class="bookmark-item-title">${escapeHtml(bm.title)}${bm.pinned ? " 📌" : ""}</div>
      <div class="bookmark-item-url">${escapeHtml(bm.url)}</div>
    `;

    btn.appendChild(icon);
    btn.appendChild(text);
    btn.addEventListener("click", () => Nova.getBridge().openUrl(bm.url));
    btn.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      NovaBookmarks.showContextMenu(e.clientX, e.clientY, bm, appData, refreshUI);
    });

    list.appendChild(btn);
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById("view-" + tab.dataset.view).classList.add("active");
    });
  });
}

function navigateFromOmnibar(raw) {
  const url = Nova.normalizeUrl(raw, appData);
  if (!url) return;
  Nova.getBridge().openUrl(url);
}

document.getElementById("omnibar-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("omnibar-input");
  navigateFromOmnibar(input.value);
  input.blur();
});

document.getElementById("fab-add").addEventListener("click", async () => {
  const bookmark = await NovaBookmarks.showBookmarkDialog({ title: "Add bookmark" });
  if (bookmark) {
    NovaBookmarks.upsertBookmark(appData, bookmark);
    refreshUI();
  }
});

document.getElementById("btn-settings").addEventListener("click", () => {
  document.querySelector('.tab[data-view="settings"]').click();
});

try {
  setupTabs();
  refreshUI();
} catch (err) {
  console.error(err);
  document.body.insertAdjacentHTML(
    "afterbegin",
    '<div style="margin:16px;padding:16px;background:#ff6b6b22;border:1px solid #ff6b6b;border-radius:12px;color:#fff;font-family:system-ui,sans-serif;">' +
      "<strong>Nova Browser failed to start.</strong><br>" +
      "Try clearing saved data: open devtools and run " +
      "<code>localStorage.removeItem('nova-browser-data')</code>, then reload." +
      "</div>"
  );
}
