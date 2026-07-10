function getPinnedBookmarks(bookmarks) {
  return bookmarks
    .filter((b) => b.pinned)
    .sort((a, b) => (a.title || "").localeCompare(b.title || ""));
}

function getUnpinnedBookmarks(bookmarks) {
  return bookmarks
    .filter((b) => !b.pinned)
    .sort((a, b) => (a.title || "").localeCompare(b.title || ""));
}

function findBookmark(bookmarks, id) {
  return bookmarks.find((b) => b.id === id);
}

function upsertBookmark(data, bookmark) {
  const idx = data.bookmarks.findIndex((b) => b.id === bookmark.id);
  if (idx >= 0) {
    data.bookmarks[idx] = bookmark;
  } else {
    data.bookmarks.push(bookmark);
  }
  Nova.saveData(data);
  return data;
}

function deleteBookmark(data, id) {
  data.bookmarks = data.bookmarks.filter((b) => b.id !== id);
  Nova.saveData(data);
  return data;
}

function togglePin(data, id) {
  const bm = findBookmark(data.bookmarks, id);
  if (bm) {
    bm.pinned = !bm.pinned;
    Nova.saveData(data);
  }
  return data;
}

function isBookmarked(data, url) {
  const normalized = Nova.normalizeUrl(url);
  return data.bookmarks.some(
    (b) => Nova.normalizeUrl(b.url) === normalized
  );
}

function showBookmarkDialog(options = {}) {
  const existing = options.bookmark || {};
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.innerHTML = `
      <div class="dialog" role="dialog">
        <h2>${options.title || "Add bookmark"}</h2>
        <div class="form-row">
          <label for="bm-title">Title</label>
          <input id="bm-title" type="text" value="${escapeAttr(existing.title || "")}" placeholder="Site name">
        </div>
        <div class="form-row">
          <label for="bm-url">URL</label>
          <input id="bm-url" type="url" value="${escapeAttr(existing.url || "")}" placeholder="https://example.com">
        </div>
        <div class="checkbox-row">
          <input id="bm-pin" type="checkbox" ${existing.pinned !== false ? "checked" : ""}>
          <label for="bm-pin">Show on home screen</label>
        </div>
        <div class="form-actions">
          <button type="button" class="secondary-btn" data-action="cancel">Cancel</button>
          <button type="button" class="primary-btn" data-action="save">Save</button>
        </div>
      </div>
    `;

    function close(result) {
      overlay.remove();
      resolve(result);
    }

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close(null);
    });

    overlay.querySelector('[data-action="cancel"]').addEventListener("click", () => close(null));
    overlay.querySelector('[data-action="save"]').addEventListener("click", () => {
      const title = overlay.querySelector("#bm-title").value.trim();
      const url = Nova.normalizeUrl(overlay.querySelector("#bm-url").value);
      const pinned = overlay.querySelector("#bm-pin").checked;
      if (!url) return;
      close({
        id: existing.id || Nova.generateId(),
        title: title || NovaFavicon.getDomain(url),
        url,
        pinned,
      });
    });

    document.body.appendChild(overlay);
    overlay.querySelector("#bm-title").focus();
  });
}

function escapeAttr(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function showContextMenu(x, y, bookmark, data, onUpdate) {
  closeContextMenu();

  const menu = document.createElement("div");
  menu.className = "context-menu";
  menu.id = "shortcut-context-menu";
  menu.style.left = Math.min(x, window.innerWidth - 180) + "px";
  menu.style.top = Math.min(y, window.innerHeight - 220) + "px";

  const actions = [
    { label: "Open", action: () => Nova.getBridge().openUrl(bookmark.url) },
    {
      label: bookmark.pinned ? "Unpin" : "Pin to home",
      action: () => {
        togglePin(data, bookmark.id);
        onUpdate();
      },
    },
    {
      label: "Edit",
      action: async () => {
        const edited = await showBookmarkDialog({ bookmark, title: "Edit bookmark" });
        if (edited) {
          upsertBookmark(data, edited);
          onUpdate();
        }
      },
    },
    {
      label: "Delete",
      danger: true,
      action: () => {
        deleteBookmark(data, bookmark.id);
        onUpdate();
      },
    },
  ];

  actions.forEach(({ label, action, danger }) => {
    const btn = document.createElement("button");
    btn.textContent = label;
    if (danger) btn.classList.add("danger");
    btn.addEventListener("click", () => {
      closeContextMenu();
      action();
    });
    menu.appendChild(btn);
  });

  document.body.appendChild(menu);

  setTimeout(() => {
    document.addEventListener(
      "click",
      closeContextMenu,
      { once: true }
    );
  }, 0);
}

function closeContextMenu() {
  const menu = document.getElementById("shortcut-context-menu");
  if (menu) menu.remove();
}

window.NovaBookmarks = {
  getPinnedBookmarks,
  getUnpinnedBookmarks,
  findBookmark,
  upsertBookmark,
  deleteBookmark,
  togglePin,
  isBookmarked,
  showBookmarkDialog,
  showContextMenu,
  closeContextMenu,
};
