const thumbSoldier = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="8" fill="#141B26"/><circle cx="32" cy="22" r="12" fill="#2A374A"/><rect x="25" y="18" width="14" height="6" rx="3" fill="#10B981" fill-opacity="0.8"/><path d="M18 42 C18 32 46 32 46 42 L48 58 L16 58 Z" fill="#1E293B"/><path d="M26 36 L38 36 L36 46 L28 46 Z" fill="#334155"/><line x1="28" y1="40" x2="36" y2="40" stroke="#475569" stroke-width="1.5"/></svg>`;
const thumbCar = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="8" fill="#141B26"/><path d="M10 40 L18 28 L46 28 L54 40 L56 46 L8 46 Z" fill="#1E293B"/><path d="M19 30 L25 38 L42 38 L45 30 Z" fill="#0EA5E9" fill-opacity="0.8"/><rect x="8" y="44" width="48" height="6" rx="2" fill="#334155"/><circle cx="18" cy="46" r="6" fill="#0B0F19"/><circle cx="18" cy="46" r="3" fill="#64748B"/><circle cx="46" cy="46" r="6" fill="#0B0F19"/><circle cx="46" cy="46" r="3" fill="#64748B"/><line x1="50" y1="42" x2="54" y2="42" stroke="#38BDF8" stroke-width="2"/></svg>`;
const thumbBuilding = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="8" fill="#141B26"/><polygon points="12 28 32 14 52 28" fill="#475569"/><rect x="14" y="28" width="36" height="4" fill="#334155"/><rect x="16" y="32" width="4" height="18" fill="#64748B"/><rect x="24" y="32" width="4" height="18" fill="#64748B"/><rect x="36" y="32" width="4" height="18" fill="#64748B"/><rect x="44" y="32" width="4" height="18" fill="#64748B"/><rect x="10" y="50" width="44" height="6" fill="#334155"/></svg>`;
const defaultModelThumb = `<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="64" height="64" rx="8" fill="#141B26"/><path d="M32 14 L50 24 L50 44 L32 54 L14 44 L14 24 Z" stroke="#3B82F6" stroke-width="2"/><line x1="32" y1="14" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/><line x1="50" y1="24" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/><line x1="14" y1="24" x2="32" y2="34" stroke="#3B82F6" stroke-width="2"/></svg>`;

let queueState = [
  {
    id: "sample_1",
    uid: "8f31e7c4a6d2e9b3f1c7e5a9d4b2c6e8",
    name: "Model_8f31e7...",
    url: "https://sketchfab.com/3d-models/model-8f31e7c4a6d2e9b3f1c7e5a9d4b2c6e8",
    status: "done",
    statusText: "Готово",
    subText: "2.4 МБ · 3 файла",
    percent: 100,
    thumbSvg: thumbSoldier,
    path: ""
  },
  {
    id: "sample_2",
    uid: "12ac9f3e7b6c4d8a2f1e9c3d7b5a6e8f",
    name: "Model_12ac9f...",
    url: "https://sketchfab.com/3d-models/model-12ac9f3e7b6c4d8a2f1e9c3d7b5a6e8f",
    status: "downloading",
    statusText: "Загрузка... 67%",
    subText: "15.2 МБ / 22.8 МБ",
    percent: 67,
    thumbSvg: thumbCar,
    path: ""
  },
  {
    id: "sample_3",
    uid: "91de4c7b8f1a3d6e9c2b5f7a4d8e1c3",
    name: "Model_91de4c...",
    url: "https://sketchfab.com/3d-models/model-91de4c7b8f1a3d6e9c2b5f7a4d8e1c3",
    status: "queued",
    statusText: "В очереди",
    subText: "",
    percent: 0,
    thumbSvg: thumbBuilding,
    path: ""
  }
];

let isDownloadingQueue = false;

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupSettingsSync();
  setupWindowControls();
  setupQueueActions();
  setupModalActions();
  renderQueue();
  updateCounters();
  initBackend();
});

function initBackend() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_initial_state().then(state => {
      if (state && state.default_output_dir) {
        setOutputDirectory(state.default_output_dir);
      }
    }).catch(() => {});
  } else {
    window.addEventListener("pywebviewready", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_initial_state().then(state => {
          if (state && state.default_output_dir) {
            setOutputDirectory(state.default_output_dir);
          }
        }).catch(() => {});
      }
    });
  }
}

function setOutputDirectory(dirPath) {
  document.getElementById("savePathInput").value = dirPath;
  document.getElementById("settingsPathInput").value = dirPath;
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

  const panelTabs = document.querySelectorAll(".panel-tab");
  panelTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      panelTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.getAttribute("data-tab");
      const secGen = document.getElementById("secGeneral");
      const secNet = document.getElementById("secNetwork");
      const secProc = document.getElementById("secProcessing");
      if (target === "general") {
        secGen.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (target === "network") {
        secNet.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (target === "processing") {
        secProc.scrollIntoView({ behavior: "smooth", block: "start" });
      }
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

  const btnBrowse1 = document.getElementById("btnBrowseSaveDir");
  const btnBrowse2 = document.getElementById("btnSettingsBrowseDir");
  const handleBrowse = () => {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.select_folder(saveInput.value).then(res => {
        if (res) {
          setOutputDirectory(res);
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
      setStatus("Проверка прокси...");
      window.pywebview.api.test_proxy(proxyData).then(res => {
        if (res && res.success) {
          setStatus("Прокси работает корректно");
          alert("Соединение с прокси успешно установлено!");
        } else {
          setStatus("Ошибка подключения к прокси");
          alert("Не удалось подключиться к прокси: " + (res ? res.error : "Ошибка"));
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
  const fallbackUid = uid || Math.random().toString(16).substring(2, 10).padEnd(32, "0");
  const shortUid = fallbackUid.substring(0, 8);
  const newItem = {
    id: "item_" + Date.now() + "_" + Math.random().toString(36).substr(2, 5),
    uid: fallbackUid,
    name: "Model_" + shortUid + "...",
    url: inputStr.startsWith("http") ? inputStr : ("https://sketchfab.com/3d-models/" + fallbackUid),
    status: "queued",
    statusText: "В очереди",
    subText: "",
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

    let statusHtml = "";
    if (item.status === "done") {
      statusHtml = `
        <div class="item-status-text green">
          <span class="badge-dot green"></span>
          <span>${item.statusText || "Готово"}</span>
        </div>
        <div class="item-subtext">${item.subText || "2.4 МБ · 3 файла"}</div>
      `;
    } else if (item.status === "downloading") {
      statusHtml = `
        <div class="item-status-text blue">
          <span class="badge-dot blue"></span>
          <span>${item.statusText || ("Загрузка... " + (item.percent || 0) + "%")}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${item.percent || 0}%;"></div>
        </div>
        <div class="item-subtext">${item.subText || ""}</div>
      `;
    } else {
      statusHtml = `
        <div class="item-status-text gray" style="margin-top: 1px;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 2px;">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>В очереди</span>
        </div>
      `;
    }

    let actionsHtml = "";
    if (item.status === "done") {
      actionsHtml = `
        <button class="icon-btn btn-open-item" title="Открыть папку">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
        <button class="icon-btn btn-menu" title="Опции">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="2"></circle>
            <circle cx="12" cy="12" r="2"></circle>
            <circle cx="12" cy="19" r="2"></circle>
          </svg>
        </button>
      `;
    } else if (item.status === "downloading") {
      actionsHtml = `
        <button class="icon-btn btn-remove" title="Отмена">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      `;
    } else {
      actionsHtml = `
        <button class="icon-btn btn-remove" title="Удалить">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <button class="icon-btn btn-menu" title="Опции">
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
      btnRemove.addEventListener("click", () => removeQueueItem(item.id));
    }

    container.appendChild(el);
  });
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

function setStatus(msg) {
  const label = document.getElementById("bottomStatusMsg");
  label.innerText = msg;
}

function startQueueDownload() {
  const pendingItems = queueState.filter(i => i.status === "queued");
  if (pendingItems.length === 0) {
    setStatus("Все модели уже загружены или очередь пуста");
    return;
  }

  isDownloadingQueue = true;
  document.getElementById("btnStartQueueText").innerText = "Остановить загрузку";
  setStatus("Загрузка очереди...");

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
    autoOpen: autoOpen
  };

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.start_queue(payload);
  }
}

function cancelQueueDownload() {
  isDownloadingQueue = false;
  document.getElementById("btnStartQueueText").innerText = "Начать загрузку";
  setStatus("Остановка загрузки...");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.cancel_queue();
  }
}

window.onQueueProgress = function(data) {
  if (!data) return;
  const item = queueState.find(i => i.id === data.id || i.uid === data.uid);
  if (item) {
    item.status = data.status || item.status;
    item.statusText = data.statusText || item.statusText;
    item.subText = data.subText !== undefined ? data.subText : item.subText;
    item.percent = data.percent !== undefined ? data.percent : item.percent;
    if (data.name) item.name = data.name;
    if (data.path) item.path = data.path;
  }
  renderQueue();
  updateCounters();
};

window.onQueueFinish = function(result) {
  isDownloadingQueue = false;
  document.getElementById("btnStartQueueText").innerText = "Начать загрузку";
  setStatus(result && result.message ? result.message : "Готов к работе");
  renderQueue();
  updateCounters();
};

function loadMyModels() {
  const grid = document.getElementById("modelsGrid");
  const savePath = document.getElementById("savePathInput").value;
  grid.innerHTML = "<div style='color: var(--text-muted); font-size: 13px; padding: 20px;'>Загрузка сохраненных моделей...</div>";

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_my_models(savePath).then(models => {
      grid.innerHTML = "";
      if (!models || models.length === 0) {
        grid.innerHTML = "<div style='color: var(--text-muted); font-size: 13px; padding: 20px;'>Папка пуста. Скачанные 3D-модели появятся здесь.</div>";
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
          <span class="model-card-info">${m.size} · ${m.files} файлов</span>
          <div class="model-card-actions">
            <button class="icon-btn btn-open-model-dir" title="Открыть папку">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button class="btn-secondary btn-view-file" style="padding: 6px 12px; font-size: 11px;">Открыть 3D</button>
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
