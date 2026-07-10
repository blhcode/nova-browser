function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function letterColor(url) {
  const hues = [210, 175, 145, 260, 320, 190, 30];
  const hue = hues[hashString(url) % hues.length];
  return `hsl(${hue}, 55%, 45%)`;
}

function getDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch (_) {
    return url;
  }
}

function getLetter(title, url) {
  const source = (title || getDomain(url) || "?").trim();
  return source.charAt(0).toUpperCase();
}

function faviconUrl(url) {
  const domain = getDomain(url);
  return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
}

function createIconElement(bookmark, size) {
  const wrap = document.createElement("div");
  if (size === "tile") {
    wrap.className = "shortcut-letter";
  } else {
    wrap.className = "bookmark-item-icon";
  }

  const img = document.createElement("img");
  img.alt = "";
  img.src = faviconUrl(bookmark.url);
  img.onerror = () => {
    img.remove();
    const letter = document.createElement("div");
    letter.className = size === "tile" ? "shortcut-letter" : "";
    if (size !== "tile") {
      letter.style.cssText =
        "width:100%;height:100%;display:flex;align-items:center;justify-content:center;border-radius:10px;font-weight:700;color:#fff;";
    }
    letter.style.background = letterColor(bookmark.url);
    letter.textContent = getLetter(bookmark.title, bookmark.url);
    wrap.appendChild(letter);
  };

  if (size === "tile") {
    wrap.appendChild(img);
    return wrap;
  }

  const inner = document.createElement("div");
  inner.className = "bookmark-item-icon";
  inner.appendChild(img);
  return inner;
}

window.NovaFavicon = {
  hashString,
  letterColor,
  getDomain,
  getLetter,
  faviconUrl,
  createIconElement,
};
