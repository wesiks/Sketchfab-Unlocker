const defaultModelThumb = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="8" fill="#141B26"/><path d="M32 14 L50 24 L50 44 L32 54 L14 44 L14 24 Z" stroke="#3B82F6" stroke-width="2"/><line x1="32" y1="14" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/><line x1="50" y1="24" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/><line x1="14" y1="24" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/></svg>`;

let queueState = [];

let isDownloadingQueue = false;

document.addEventListener("DOMContentLoaded", () => {
  setupLanguage();
  setupNavigation();
  setupSettingsSync();
  setupWindowControls();
  setupQueueActions();
  setupModalActions();
  renderQueue();
  updateCounters();
  initBackend();
});

function applyInitialState(state) {
  if (!state) return;
  if (state.default_output_dir) setOutputDirectory(state.default_output_dir);
  if (state.settings) applySettings(state.settings);
  if (state.language) {
    document.getElementById("selLanguage").value = state.language;
    setLanguage(state.language, false);
  }
}

function initBackend() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_initial_state().then(applyInitialState).catch(() => {});
  } else {
    window.addEventListener("pywebviewready", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_initial_state().then(applyInitialState).catch(() => {});
      }
    });
  }
}

const SETTING_FIELDS = {
  savePath: ["savePathInput", "value"],
  clean: ["chkCleanOutput", "checked"],
  textures: ["chkDownloadTextures", "checked"],
  autoOpen: ["chkAutoOpen", "checked"],
  materials: ["chkFormatMaterials", "checked"],
  format: ["selFormat", "value"],
  converter: ["selConverter", "value"],
  proxyEnabled: ["chkProxyEnabled", "checked"],
  proxyType: ["selProxyType", "value"],
  proxyHost: ["inpProxyHost", "value"],
  proxyPort: ["inpProxyPort", "value"],
  proxyUser: ["inpProxyUser", "value"],
  apiToken: ["inpApiToken", "value"],
};

function collectSettings() {
  const out = {};
  for (const [k, [id, prop]] of Object.entries(SETTING_FIELDS)) out[k] = document.getElementById(id)[prop];
  return out;
}

function applySettings(cfg) {
  for (const [k, [id, prop]] of Object.entries(SETTING_FIELDS)) {
    if (cfg[k] === undefined || cfg[k] === null) continue;
    if (k === "savePath") { setOutputDirectory(cfg[k]); continue; }
    document.getElementById(id)[prop] = cfg[k];
  }
  syncLinkedControls();
}

function syncLinkedControls() {
  document.getElementById("chkSettingsClean").checked = document.getElementById("chkCleanOutput").checked;
  document.getElementById("chkSettingsAutoOpen").checked = document.getElementById("chkAutoOpen").checked;
  document.getElementById("chkFormatTextures").checked = document.getElementById("chkDownloadTextures").checked;
}

let saveTimer = null;
function scheduleSaveSettings() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    if (window.pywebview && window.pywebview.api) window.pywebview.api.save_settings(collectSettings());
  }, 400);
}

function setupLanguage() {
  const sel = document.getElementById("selLanguage");
  sel.value = currentLang;
  sel.addEventListener("change", () => setLanguage(sel.value, true));
  applyI18n();
}

function onLanguageChanged() {
  renderQueue();
  setStatus(lastStatus.key, lastStatus.vars);
  document.getElementById("btnStartQueueText").textContent = t(isDownloadingQueue ? "download.stop" : "download.start");
  if (document.getElementById("pageModels").classList.contains("active")) loadMyModels();
}

function setOutputDirectory(dirPath) {
  document.getElementById("savePathInput").value = dirPath;
  document.getElementById("settingsPathInput").value = dirPath;
}

function showSettingsSection(name) {
  const map = { general: "secGeneral", network: "secNetwork", processing: "secProcessing" };
  for (const [key, id] of Object.entries(map)) {
    document.getElementById(id).style.display = key === name ? "flex" : "none";
  }
}

function setupNavigation() {
  const navDownload = document.getElementById("tabNavDownload");
  const navModels = document.getElementById("tabNavModels");
  const navSettings = document.getElementById("tabNavSettings");
  const pageDownload = document.getElementById("pageDownload");
  const pageModels = document.getElementById("pageModels");
  const settingsPanel = document.getElementById("settingsPanel");

  navDownload.addEventListener("click", () => {
    navDownload.classList.add("active");
    navModels.classList.remove("active");
    pageDownload.classList.add("active");
    pageModels.classList.remove("active");
  });

  navModels.addEventListener("click", () => {
    navModels.classList.add("active");
    navDownload.classList.remove("active");
    pageModels.classList.add("active");
    pageDownload.classList.remove("active");
    loadMyModels();
  });

  navSettings.addEventListener("click", () => {
    settingsPanel.classList.toggle("hidden");
  });

  showSettingsSection("general");
  const panelTabs = document.querySelectorAll(".panel-tab");
  panelTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      panelTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      showSettingsSection(tab.getAttribute("data-tab"));
    });
  });

  document.getElementById("btnRefreshModels").addEventListener("click", loadMyModels);
  document.getElementById("btnOpenSavedFolder").addEventListener("click", () => {
    const currentPath = document.getElementById("savePathInput").value;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_folder(currentPath);
    }
  });
}

function setupSettingsSync() {
  const saveInput = document.getElementById("savePathInput");
  const settingsInput = document.getElementById("settingsPathInput");

  const chkClean1 = document.getElementById("chkCleanOutput");
  const chkClean2 = document.getElementById("chkSettingsClean");
  chkClean1.addEventListener("change", () => { chkClean2.checked = chkClean1.checked; });
  chkClean2.addEventListener("change", () => { chkClean1.checked = chkClean2.checked; });

  const chkAuto1 = document.getElementById("chkAutoOpen");
  const chkAuto2 = document.getElementById("chkSettingsAutoOpen");
  chkAuto1.addEventListener("change", () => { chkAuto2.checked = chkAuto1.checked; });
  chkAuto2.addEventListener("change", () => { chkAuto1.checked = chkAuto2.checked; });

  const chkTex1 = document.getElementById("chkDownloadTextures");
  const chkTex2 = document.getElementById("chkFormatTextures");
  chkTex1.addEventListener("change", () => { chkTex2.checked = chkTex1.checked; });
  chkTex2.addEventListener("change", () => { chkTex1.checked = chkTex2.checked; });

  for (const [id] of Object.values(SETTING_FIELDS)) {
    document.getElementById(id).addEventListener("change", scheduleSaveSettings);
  }
  ["chkSettingsClean", "chkSettingsAutoOpen", "chkFormatTextures"].forEach(id =>
    document.getElementById(id).addEventListener("change", scheduleSaveSettings));

  const btnBrowse1 = document.getElementById("btnBrowseSaveDir");
  const btnBrowse2 = document.getElementById("btnSettingsBrowseDir");
  const handleBrowse = () => {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.select_folder(saveInput.value).then(res => {
        if (res) {
          setOutputDirectory(res);
          scheduleSaveSettings();
        }
      });
    }
  };
  btnBrowse1.addEventListener("click", handleBrowse);
  btnBrowse2.addEventListener("click", handleBrowse);

  document.getElementById("btnOpenSaveDir").addEventListener("click", () => {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_folder(saveInput.value);
    }
  });

  const eyeBtn = document.getElementById("btnTogglePassEye");
  const passInp = document.getElementById("inpProxyPass");
  eyeBtn.addEventListener("click", () => {
    passInp.type = passInp.type === "password" ? "text" : "password";
  });

  const tokenInp = document.getElementById("inpApiToken");
  document.getElementById("btnToggleTokenEye").addEventListener("click", () => {
    tokenInp.type = tokenInp.type === "password" ? "text" : "password";
  });
  document.getElementById("btnTokenHelp").addEventListener("click", () => {
    if (window.pywebview && window.pywebview.api) window.pywebview.api.open_url("https://sketchfab.com/settings#password");
  });

  document.getElementById("btnTestProxy").addEventListener("click", () => {
    const proxyData = {
      enabled: document.getElementById("chkProxyEnabled").checked,
      type: document.getElementById("selProxyType").value,
      host: document.getElementById("inpProxyHost").value.trim(),
      port: document.getElementById("inpProxyPort").value.trim(),
      user: document.getElementById("inpProxyUser").value.trim(),
      pass: document.getElementById("inpProxyPass").value.trim()
    };
    if (window.pywebview && window.pywebview.api) {
      setStatus("status.proxy_testing");
      window.pywebview.api.test_proxy(proxyData).then(res => {
        if (res && res.success) {
          setStatus("status.proxy_ok");
          alert(t("status.proxy_ok_alert"));
        } else {
          setStatus("status.proxy_fail");
          alert(t("status.proxy_fail_alert") + (res ? (res.errorKey ? t(res.errorKey) : res.error) : t("status.error")));
        }
      });
    }
  });
}

function setupWindowControls() {
  const btnMin = document.getElementById("btnMinimizeApp");
  if (btnMin) {
    btnMin.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.minimize_window();
      }
    });
  }
  const btnMax = document.getElementById("btnMaximizeApp");
  if (btnMax) {
    btnMax.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.maximize_window();
      }
    });
  }
  const titlebar = document.querySelector(".titlebar");
  if (titlebar) {
    titlebar.addEventListener("dblclick", (e) => {
      if (!e.target.closest("button") && btnMax) btnMax.click();
    });
  }
  const btnClose = document.getElementById("btnCloseApp");
  if (btnClose) {
    btnClose.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.close_window();
      }
    });
  }
}

function setupQueueActions() {
  const urlInput = document.getElementById("urlInput");
  const btnPaste = document.getElementById("btnPasteClip");
  const btnAdd = document.getElementById("btnAddSingle");
  const btnStart = document.getElementById("btnStartQueue");

  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        urlInput.focus();
      }
    } catch {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_clipboard().then(clip => {
          if (clip) {
            urlInput.value = clip.trim();
            urlInput.focus();
          }
        });
      }
    }
  });

  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      btnAdd.click();
    }
  });

  btnAdd.addEventListener("click", () => {
    const val = urlInput.value.trim();
    if (!val) return;
    addInputToQueue(val);
    urlInput.value = "";
  });

  btnStart.addEventListener("click", () => {
    if (isDownloadingQueue) {
      cancelQueueDownload();
    } else {
      startQueueDownload();
    }
  });
}

function setupModalActions() {
  const modal = document.getElementById("batchModal");
  const btnOpen = document.getElementById("btnOpenBatch");
  const btnClose = document.getElementById("btnCloseBatchModal");
  const btnCancel = document.getElementById("btnCancelBatch");
  const btnConfirm = document.getElementById("btnConfirmBatch");
  const textarea = document.getElementById("batchTextarea");

  btnOpen.addEventListener("click", () => {
    modal.classList.add("active");
    textarea.value = "";
    textarea.focus();
  });

  const closeModal = () => modal.classList.remove("active");
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
  document.getElementById("btnClearDone").addEventListener("click", clearCompleted);
  btnClose.addEventListener("click", closeModal);
  btnCancel.addEventListener("click", closeModal);

  btnConfirm.addEventListener("click", () => {
    const lines = textarea.value.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    lines.forEach(line => addInputToQueue(line));
    closeModal();
  });
}

function extractUid(raw) {
  const match = raw.match(/([a-f0-9]{32})/i);
  return match ? match[1].toLowerCase() : null;
}

function addInputToQueue(inputStr) {
  const uid = extractUid(inputStr);
  if (uid && queueState.some(i => i.uid === uid && i.status !== "error")) {
    setStatus("queue.duplicate");
    return;
  }
  const fallbackUid = uid || Math.random().toString(16).substring(2, 10).padEnd(32, "0");
  const shortUid = fallbackUid.substring(0, 8);
  const newItem = {
    id: "item_" + Date.now() + "_" + Math.random().toString(36).substr(2, 5),
    uid: fallbackUid,
    name: "Model_" + shortUid + "...",
    url: inputStr.startsWith("http") ? inputStr : ("https://sketchfab.com/3d-models/" + fallbackUid),
    status: "queued",
    statusKey: "status.queued",
    subText: "",
    subKey: null,
    percent: 0,
    thumbSvg: defaultModelThumb,
    path: ""
  };
  queueState.push(newItem);
  renderQueue();
  updateCounters();
}

function removeQueueItem(id) {
  queueState = queueState.filter(item => item.id !== id);
  renderQueue();
  updateCounters();
}

function renderQueue() {
  const container = document.getElementById("queueList");
  container.innerHTML = "";

  queueState.forEach(item => {
    const el = document.createElement("div");
    el.className = "queue-item";
    el.id = "queue_dom_" + item.id;

    const statusLabel = item.statusKey ? t(item.statusKey, item.statusParams) : (item.statusText || "");
    const subLabel = item.subKey ? t(item.subKey, item.subParams)
      : (item.subText || "").replace("{files}", t("models.files"));

    let statusHtml = "";
    if (item.status === "done") {
      statusHtml = `
        <div class="item-status-text green">
          <span class="badge-dot green"></span>
          <span>${statusLabel || t("status.done")}</span>
        </div>
        <div class="item-subtext">${subLabel}</div>
      `;
    } else if (item.status === "downloading") {
      statusHtml = `
        <div class="item-status-text blue">
          <span class="badge-dot blue"></span>
          <span>${statusLabel || t("status.downloading_pct", { pct: item.percent || 0 })}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${item.percent || 0}%;"></div>
        </div>
        <div class="item-subtext">${subLabel}</div>
      `;
    } else if (item.status === "error") {
      statusHtml = `
        <div class="item-status-text" style="color: #EF4444;">
          <span class="badge-dot" style="background: #EF4444;"></span>
          <span>${statusLabel || t("status.error")}</span>
        </div>
        <div class="item-subtext" title="${escapeHtml(subLabel)}">${escapeHtml(subLabel)}</div>
      `;
    } else {
      statusHtml = `
        <div class="item-status-text gray" style="margin-top: 1px;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 2px;">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>${t("status.queued")}</span>
        </div>
      `;
    }

    let actionsHtml = "";
    if (item.status === "done") {
      actionsHtml = `
        <button class="icon-btn btn-open-item" title="${t("download.open_folder")}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
        <button class="icon-btn btn-menu" title="${t('queue.options')}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="2"></circle>
            <circle cx="12" cy="12" r="2"></circle>
            <circle cx="12" cy="19" r="2"></circle>
          </svg>
        </button>
      `;
    } else if (item.status === "downloading") {
      actionsHtml = `
        <button class="icon-btn btn-remove" title="${t('queue.cancel')}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      `;
    } else {
      actionsHtml = `
        <button class="icon-btn btn-remove" title="${t('queue.remove')}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <button class="icon-btn btn-menu" title="${t('queue.options')}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="2"></circle>
            <circle cx="12" cy="12" r="2"></circle>
            <circle cx="12" cy="19" r="2"></circle>
          </svg>
        </button>
      `;
    }

    el.innerHTML = `
      <div class="item-thumb-box">
        ${item.thumbSvg || defaultModelThumb}
      </div>
      <div class="item-main-info">
        <span class="item-title">${item.name}</span>
        <span class="item-uid">UID: ${item.uid}</span>
      </div>
      <div class="item-status-col">
        ${statusHtml}
      </div>
      <div class="item-actions">
        ${actionsHtml}
      </div>
    `;

    const btnOpenItem = el.querySelector(".btn-open-item");
    if (btnOpenItem) {
      btnOpenItem.addEventListener("click", () => {
        if (item.path && window.pywebview && window.pywebview.api) {
          window.pywebview.api.open_folder(item.path);
        } else {
          const savePath = document.getElementById("savePathInput").value;
          if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.open_folder(savePath);
          }
        }
      });
    }

    const btnRemove = el.querySelector(".btn-remove");
    if (btnRemove) {
      btnRemove.addEventListener("click", () => {
        if (item.status === "downloading") cancelQueueDownload();
        else removeQueueItem(item.id);
      });
    }

    const btnMenu = el.querySelector(".btn-menu");
    if (btnMenu) {
      btnMenu.addEventListener("click", (e) => { e.stopPropagation(); showItemMenu(btnMenu, item); });
    }

    container.appendChild(el);
  });
}

function copyText(text) {
  // navigator.clipboard is rejected by Qt WebEngine; execCommand works from a user gesture
  const fallback = () => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0;";
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    ta.remove();
    if (!ok && window.pywebview && window.pywebview.api) window.pywebview.api.copy_to_clipboard(text);
    return ok;
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).catch(fallback);
  }
  fallback();
  return Promise.resolve();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function closeItemMenu() {
  const old = document.getElementById("itemMenu");
  if (old) old.remove();
}

function showItemMenu(anchor, item) {
  closeItemMenu();
  const menu = document.createElement("div");
  menu.id = "itemMenu";
  menu.style.cssText = "position:fixed;z-index:1000;background:var(--card-bg,#151922);border:1px solid var(--border-color,#252D3D);border-radius:8px;padding:4px;min-width:170px;box-shadow:0 8px 24px rgba(0,0,0,.45);";
  const entries = [[t("queue.copy_uid"), () => {
    copyText(item.uid).then(() => setStatus("status.copied"));
  }], [t("queue.open_web"), () => {
    if (window.pywebview && window.pywebview.api) window.pywebview.api.open_url(item.url);
  }]];
  if (item.status === "error") {
    entries.push([t("queue.copy_error"), () => {
      copyText(item.errorDetail || item.subText || "").then(() => setStatus("status.copied_text"));
    }]);
    entries.push([t("queue.retry"), () => {
      item.status = "queued"; item.statusKey = "status.queued"; item.subKey = null; item.subText = "";
      renderQueue(); updateCounters();
    }]);
  }
  entries.forEach(([label, fn]) => {
    const b = document.createElement("div");
    b.textContent = label;
    b.style.cssText = "padding:8px 12px;font-size:12px;cursor:pointer;border-radius:6px;color:var(--text-main,#F3F4F6);";
    b.addEventListener("mouseenter", () => { b.style.background = "rgba(255,255,255,.07)"; });
    b.addEventListener("mouseleave", () => { b.style.background = ""; });
    b.addEventListener("click", () => { closeItemMenu(); fn(); });
    menu.appendChild(b);
  });
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.top = Math.min(r.bottom + 4, window.innerHeight - menu.offsetHeight - 8) + "px";
  menu.style.left = Math.max(8, r.right - menu.offsetWidth) + "px";
}

document.addEventListener("click", closeItemMenu);

function clearCompleted() {
  queueState = queueState.filter(i => i.status !== "done");
  renderQueue();
  updateCounters();
}

function updateCounters() {
  const done = queueState.filter(i => i.status === "done").length;
  const active = queueState.filter(i => i.status === "downloading").length;
  const queued = queueState.filter(i => i.status === "queued").length;

  document.getElementById("countDone").innerText = done;
  document.getElementById("countActive").innerText = active;
  document.getElementById("countQueued").innerText = queued;

  document.getElementById("barDone").innerText = done;
  document.getElementById("barActive").innerText = active;
  document.getElementById("barQueued").innerText = queued;
}

let lastStatus = { key: "status.ready", vars: undefined };

function setStatus(key, vars) {
  lastStatus = { key, vars };
  document.getElementById("bottomStatusMsg").textContent = t(key, vars);
}

function startQueueDownload() {
  queueState.filter(i => i.status === "error").forEach(i => {
    i.status = "queued"; i.statusKey = "status.queued"; i.subKey = null; i.subText = "";
  });
  const pendingItems = queueState.filter(i => i.status === "queued");
  if (pendingItems.length === 0) {
    setStatus("status.queue_empty");
    return;
  }

  isDownloadingQueue = true;
  document.getElementById("btnStartQueueText").textContent = t("download.stop");
  setStatus("status.queue_downloading");

  const savePath = document.getElementById("savePathInput").value;
  const cleanOutput = document.getElementById("chkCleanOutput").checked;
  const proxyEnabled = document.getElementById("chkProxyEnabled").checked;
  const proxyType = document.getElementById("selProxyType").value;
  const proxyHost = document.getElementById("inpProxyHost").value.trim();
  const proxyPort = document.getElementById("inpProxyPort").value.trim();
  const proxyUser = document.getElementById("inpProxyUser").value.trim();
  const proxyPass = document.getElementById("inpProxyPass").value.trim();
  const autoOpen = document.getElementById("chkAutoOpen").checked;

  let proxyStr = null;
  if (proxyEnabled && proxyHost && proxyPort) {
    if (proxyUser && proxyPass) {
      proxyStr = `${proxyType.toLowerCase()}://${proxyUser}:${proxyPass}@${proxyHost}:${proxyPort}`;
    } else {
      proxyStr = `${proxyType.toLowerCase()}://${proxyHost}:${proxyPort}`;
    }
  }

  const payload = {
    items: pendingItems,
    savePath: savePath,
    cleanOutput: cleanOutput,
    proxy: proxyStr,
    autoOpen: autoOpen,
    downloadTextures: document.getElementById("chkDownloadTextures").checked,
    keepMaterials: document.getElementById("chkFormatMaterials").checked,
    apiToken: document.getElementById("inpApiToken").value.trim(),
    format: document.getElementById("selFormat").value,
    converter: document.getElementById("selConverter").value
  };

  renderQueue();
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.start_queue(payload);
  } else {
    isDownloadingQueue = false;
    document.getElementById("btnStartQueueText").textContent = t("download.start");
  }
}

function cancelQueueDownload() {
  isDownloadingQueue = false;
  document.getElementById("btnStartQueueText").textContent = t("download.start");
  setStatus("status.queue_stopping");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.cancel_queue();
  }
}

window.onQueueProgress = function(data) {
  if (!data) return;
  const item = queueState.find(i => i.id === data.id || i.uid === data.uid);
  if (item) {
    item.status = data.status || item.status;
    if (data.statusKey) {
      item.statusKey = data.statusKey;
      item.statusParams = data.statusParams;
      item.statusText = "";
    }
    if (data.subKey) {
      item.subKey = data.subKey;
      item.subParams = data.subParams;
      item.subText = "";
    } else if (data.subText !== undefined) {
      item.subKey = null;
      item.subText = data.subText;
    }
    item.percent = data.percent !== undefined ? data.percent : item.percent;
    if (data.errorDetail) item.errorDetail = data.errorDetail;
    if (data.name) item.name = data.name;
    if (data.path) item.path = data.path;
  }
  renderQueue();
  updateCounters();
};

window.onQueueFinish = function(result) {
  isDownloadingQueue = false;
  document.getElementById("btnStartQueueText").textContent = t("download.start");
  if (result && result.messageKey) setStatus(result.messageKey, result.messageParams);
  else setStatus("status.ready");
  renderQueue();
  updateCounters();
};

function loadMyModels() {
  const grid = document.getElementById("modelsGrid");
  const savePath = document.getElementById("savePathInput").value;
  grid.innerHTML = `<div style='color: var(--text-muted); font-size: 13px; padding: 20px;'>${t('models.loading')}</div>`;

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_my_models(savePath).then(models => {
      grid.innerHTML = "";
      if (!models || models.length === 0) {
        grid.innerHTML = `<div style='color: var(--text-muted); font-size: 13px; padding: 20px;'>${t('models.empty')}</div>`;
        return;
      }
      models.forEach(m => {
        const card = document.createElement("div");
        card.className = "model-card";
        card.innerHTML = `
          <div class="model-card-thumb">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" color="#64748B">
              <path d="M21 16V8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
          </div>
          <span class="model-card-title" title="${m.name}">${m.name}</span>
          <span class="model-card-info">${m.size} · ${m.files} ${t("models.files")}</span>
          <div class="model-card-actions">
            <button class="icon-btn btn-open-model-dir" title="${t('models.open_folder')}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button class="btn-secondary btn-view-file" style="padding: 6px 12px; font-size: 11px;">${t("models.open_3d")}</button>
          </div>
        `;
        card.querySelector(".btn-open-model-dir").addEventListener("click", () => {
          window.pywebview.api.open_folder(m.path);
        });
        card.querySelector(".btn-view-file").addEventListener("click", () => {
          window.pywebview.api.open_model_file(m.path);
        });
        grid.appendChild(card);
      });
    });
  }
}
