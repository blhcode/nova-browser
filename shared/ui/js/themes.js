function applyTheme(theme) {
  const root = document.documentElement;
  const body = document.body;
  const mode = theme.mode || "space";

  root.dataset.theme = mode;
  body.dataset.theme = mode;

  if (mode === "custom") {
    const bg = theme.customBgColor || "#0a0a12";
    root.style.setProperty("--bg", bg);
    root.style.setProperty("--accent", theme.customAccentColor || "#6b8cff");
    const lightBg = isLightColor(bg);
    root.style.setProperty("--text", lightBg ? "#1a1a1a" : "#f0f0f5");
    root.style.setProperty(
      "--text-muted",
      lightBg ? "rgba(26, 26, 26, 0.6)" : "rgba(240, 240, 245, 0.65)"
    );
    root.style.setProperty(
      "--tile-bg",
      lightBg ? "rgba(240, 240, 245, 0.95)" : "rgba(30, 30, 30, 0.65)"
    );
    if (theme.customBgImage) {
      root.style.setProperty(
        "--bg-image",
        `url("${theme.customBgImage}")`
      );
    } else {
      root.style.setProperty("--bg-image", "none");
    }
  } else {
    root.style.removeProperty("--bg");
    root.style.removeProperty("--accent");
    root.style.removeProperty("--text");
    root.style.removeProperty("--text-muted");
    root.style.removeProperty("--tile-bg");
    root.style.setProperty("--bg-image", "none");
  }
}

function isLightColor(hex) {
  const match = String(hex || "").trim().match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
  if (!match) return false;
  const r = parseInt(match[1], 16) / 255;
  const g = parseInt(match[2], 16) / 255;
  const b = parseInt(match[3], 16) / 255;
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 0.62;
}

function renderThemeSettings(container, data, onChange) {
  const theme = data.theme;
  container.innerHTML = `
    <div class="theme-grid">
      ${["white", "black", "space", "custom"]
        .map(
          (mode) => `
        <button type="button" class="theme-card ${theme.mode === mode ? "selected" : ""}" data-theme="${mode}">
          <div class="theme-preview ${mode}"></div>
          <span>${mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
        </button>`
        )
        .join("")}
    </div>
    <div class="custom-theme-controls ${theme.mode === "custom" ? "" : "hidden"}" id="custom-controls">
      <div class="color-inputs">
        <div class="form-row">
          <label for="custom-bg">Background color</label>
          <input type="color" id="custom-bg" value="${theme.customBgColor || "#0a0a12"}">
        </div>
        <div class="form-row">
          <label for="custom-accent">Accent color</label>
          <input type="color" id="custom-accent" value="${theme.customAccentColor || "#6b8cff"}">
        </div>
      </div>
      <div class="image-controls">
        <button type="button" class="secondary-btn" id="pick-image">Choose image</button>
        <button type="button" class="secondary-btn" id="remove-image">Remove image</button>
      </div>
      <div class="image-preview ${theme.customBgImage ? "" : "hidden"}" id="image-preview"
        style="${theme.customBgImage ? `background-image:url('${theme.customBgImage}')` : ""}"></div>
    </div>
  `;

  container.querySelectorAll(".theme-card").forEach((card) => {
    card.addEventListener("click", () => {
      data.theme.mode = card.dataset.theme;
      applyTheme(data.theme);
      onChange(data);
      renderThemeSettings(container, data, onChange);
    });
  });

  const customControls = container.querySelector("#custom-controls");
  if (theme.mode !== "custom") return;

  const bgInput = customControls.querySelector("#custom-bg");
  const accentInput = customControls.querySelector("#custom-accent");
  const pickBtn = customControls.querySelector("#pick-image");
  const removeBtn = customControls.querySelector("#remove-image");
  const preview = customControls.querySelector("#image-preview");

  bgInput.addEventListener("input", () => {
    data.theme.customBgColor = bgInput.value;
    applyTheme(data.theme);
    onChange(data);
  });

  accentInput.addEventListener("input", () => {
    data.theme.customAccentColor = accentInput.value;
    applyTheme(data.theme);
    onChange(data);
  });

  pickBtn.addEventListener("click", async () => {
    const bridge = Nova.getBridge();
    let result = "";
    if (window.NovaBridge && typeof window.NovaBridge.pickImageWithCallback === "function") {
      result = await new Promise((resolve) => {
        window.__novaImageCallback = resolve;
        window.NovaBridge.pickImageWithCallback();
      });
    } else if (typeof bridge.pickImage === "function") {
      result = await bridge.pickImage();
    }
    if (result) {
      data.theme.customBgImage = result;
      preview.style.backgroundImage = `url('${result}')`;
      preview.classList.remove("hidden");
      applyTheme(data.theme);
      onChange(data);
    }
  });

  removeBtn.addEventListener("click", () => {
    data.theme.customBgImage = null;
    preview.style.backgroundImage = "";
    preview.classList.add("hidden");
    applyTheme(data.theme);
    onChange(data);
  });
}

window.NovaThemes = { applyTheme, renderThemeSettings };
