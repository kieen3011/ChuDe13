// ChuDe13 Group Expense Manager - Concurrency-Controlled Frontend (OCC)
const API_BASE_URL = "http://127.0.0.1:8000";
const STORAGE_KEY = "chude13_web_groups_v1";
const META_KEY = "chude13_sync_meta_v1";

const DEFAULT_GROUPS = [
  {
    id: "g1",
    name: "Nhóm Chủ Đề 13",
    members: ["Lương", "Kiên", "Lợi", "Thục", "Lộc"],
    balances: {
      "Lương": 150000,
      "Kiên": -50000,
      "Lợi": -40000,
      "Thục": -60000,
      "Lộc": 0,
    },
    expenses: [
      {
        title: "Ăn trưa team",
        amount: 250000,
        payer: "Lương",
        participants: ["Lương", "Kiên", "Lợi", "Thục", "Lộc"],
      },
    ],
  },
];

// Active in-memory state
let groups = [];
let selectedGroupId = "";

// Concurrency & Sync Architecture Variables
let isBackendOnline = false;
let confirmedServerVersion = 0; // Luôn lấy từ Backend, không tự ý tăng
let syncMode = "local-only"; // "synced" | "saving" | "pending" | "error" | "local-only" | "conflict"

// Serialized Write Pipeline State
let isPersisting = false;
let pendingStateToPersist = null;
let conflictDataHold = null; // Giữ server snapshot khi gặp 409

// ==========================================
// 1. HELPERS & LOCAL STORAGE UTILITIES
// ==========================================

function formatVND(amount) {
  return Math.round(amount).toLocaleString("vi-VN") + " đ";
}

function getCurrentGroup() {
  return groups.find((g) => g.id === selectedGroupId) || groups[0] || null;
}

function readLocalStorageRaw() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (e) {
    console.warn("Lỗi khi đọc localStorage:", e);
    return null;
  }
}

function parseLocalGroups() {
  try {
    const saved = readLocalStorageRaw();
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {
    console.warn("Dữ liệu localStorage không hợp lệ:", e);
  }
  return null;
}

function writeLocalStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    return true;
  } catch (e) {
    console.error("Lỗi khi ghi vào localStorage:", e);
    return false;
  }
}

function loadSyncMetadata() {
  try {
    const meta = localStorage.getItem(META_KEY);
    if (meta) {
      const parsed = JSON.parse(meta);
      confirmedServerVersion = typeof parsed.confirmedServerVersion === "number" ? parsed.confirmedServerVersion : 0;
      syncMode = parsed.syncMode || "local-only";
    }
  } catch (e) {
    console.warn("Không đọc được metadata đồng bộ:", e);
  }
}

function saveSyncMetadata() {
  try {
    const meta = {
      confirmedServerVersion,
      syncMode,
      updatedAt: new Date().toISOString()
    };
    localStorage.setItem(META_KEY, JSON.stringify(meta));
  } catch (e) {
    console.warn("Không lưu được metadata đồng bộ:", e);
  }
}

// Tạo bản sao lưu được xác thực nghiêm ngặt
function createVerifiedBackup() {
  const currentRaw = readLocalStorageRaw();
  if (!currentRaw) {
    return { success: true, backupKey: null };
  }

  const backupKey = `chude13_web_groups_backup_${Date.now()}`;
  try {
    localStorage.setItem(backupKey, currentRaw);
    const readBack = localStorage.getItem(backupKey);
    if (readBack === currentRaw) {
      console.log(`Đã tạo bản sao lưu thành công tại: ${backupKey}`);
      return { success: true, backupKey };
    } else {
      console.error("Xác minh bản sao lưu thất bại: dữ liệu không khớp.");
      return { success: false, error: "Xác minh sao lưu thất bại" };
    }
  } catch (e) {
    console.error("Không thể ghi bản sao lưu vào localStorage:", e);
    return { success: false, error: e.message };
  }
}

function updateSyncStatus(status, text) {
  syncMode = status;
  saveSyncMetadata();

  const badge = document.getElementById("sync-status");
  if (!badge) return;

  badge.className = "sync-status-badge";
  if (status === "saving") {
    badge.classList.add("saving");
    badge.textContent = text || "Đang lưu lên máy chủ...";
  } else if (status === "synced") {
    badge.classList.add("saved");
    badge.textContent = text || `Đã đồng bộ (v${confirmedServerVersion})`;
  } else if (status === "conflict") {
    badge.classList.add("conflict");
    badge.textContent = text || "Xung đột phiên bản (v" + confirmedServerVersion + ")";
  } else if (status === "error") {
    badge.classList.add("error");
    badge.textContent = text || "Lưu thất bại - Lỗi máy chủ";
  } else if (status === "local-only") {
    badge.classList.add("local");
    badge.textContent = text || "Chế độ xem Cục bộ";
  } else {
    badge.textContent = text || status;
  }
}

// Deep comparison so sánh cấu trúc dữ liệu không phụ thuộc thứ tự key
function areGroupsEqual(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;

  const normalizeGroup = (g) => ({
    id: g.id,
    name: g.name,
    members: [...(g.members || [])].sort(),
    balances: g.balances || {},
    expenses: (g.expenses || []).map((e) => ({
      title: e.title,
      amount: e.amount,
      payer: e.payer,
      participants: [...(e.participants || [])].sort()
    }))
  });

  const normA = a.map(normalizeGroup).sort((x, y) => x.id.localeCompare(y.id));
  const normB = b.map(normalizeGroup).sort((x, y) => x.id.localeCompare(y.id));
  return JSON.stringify(normA) === JSON.stringify(normB);
}

// ==========================================
// 2. BACKEND API INTERACTIONS
// ==========================================

async function fetchBackendState() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/demo/state`, {
      method: "GET",
      headers: { "Accept": "application/json" }
    });
    if (res.ok) {
      const body = await res.json();
      return {
        success: true,
        version: typeof body.version === "number" ? body.version : 0,
        data: body.data?.groups || []
      };
    } else {
      return { success: false, status: res.status };
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}

async function putBackendStateWithVersion(groupsToSave, expectedVersion) {
  try {
    const payload = {
      expected_version: expectedVersion,
      data: {
        groups: groupsToSave
      }
    };
    const res = await fetch(`${API_BASE_URL}/api/demo/state`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const body = await res.json();
      return {
        success: true,
        status: 200,
        version: body.version,
        data: body.data?.groups || []
      };
    } else if (res.status === 409) {
      const errBody = await res.json().catch(() => ({}));
      return {
        success: false,
        status: 409,
        detail: errBody.detail || {}
      };
    } else {
      return { success: false, status: res.status };
    }
  } catch (err) {
    return { success: false, status: 0, error: err.message };
  }
}

// ==========================================
// 3. SINGLE SERIALIZED WRITE PIPELINE (OCC)
// ==========================================

function enqueuePersist(nextGroups) {
  // 1. Luôn ghi vào localStorage trước để bảo vệ dữ liệu cục bộ
  const localOk = writeLocalStorage(nextGroups);
  if (!localOk) {
    console.warn("Cảnh báo: Không thể ghi bản sao vào localStorage (quota hoặc lỗi lưu trữ).");
  }

  // Nếu đang ở chế độ local-only hoặc máy chủ offline, không gửi PUT tự động
  if (syncMode === "local-only" || !isBackendOnline) {
    updateSyncStatus("local-only", localOk ? "Chế độ Cục bộ (Chưa đồng bộ)" : "Cục bộ (Lỗi lưu bộ nhớ)");
    return;
  }

  // 2. Đưa snapshot mới nhất vào pipeline
  pendingStateToPersist = structuredClone(nextGroups);
  processPersistQueue();
}

async function processPersistQueue() {
  if (isPersisting) return;
  if (!pendingStateToPersist) return;
  if (syncMode === "conflict") {
    console.log("Pipeline đang dừng do có xung đột phiên bản chưa xử lý.");
    return;
  }

  isPersisting = true;
  updateSyncStatus("saving", "Đang lưu lên máy chủ...");

  const stateToSend = pendingStateToPersist;
  pendingStateToPersist = null; // lấy ra gửi

  const res = await putBackendStateWithVersion(stateToSend, confirmedServerVersion);

  if (res.success && res.status === 200) {
    // Thành công: Cập nhật phiên bản máy chủ đã xác nhận
    confirmedServerVersion = res.version;
    syncMode = "synced";
    saveSyncMetadata();

    if (!pendingStateToPersist) {
      updateSyncStatus("synced", `Đã lưu máy chủ (v${confirmedServerVersion})`);
    }
  } else if (res.status === 409) {
    // Xung đột phiên bản Optimistic Concurrency Control
    console.warn("Phát hiện xung đột phiên bản 409 Conflict:", res.detail);
    updateSyncStatus("conflict", "Xung đột dữ liệu với thiết bị khác!");

    // Tạm dừng gửi các snapshot tiếp theo
    pendingStateToPersist = null;

    // Lấy trạng thái mới nhất từ server và hiển thị giao diện giải quyết xung đột
    await handleVersionConflict(stateToSend);
  } else {
    // Lỗi mạng hoặc 500
    console.error("Lỗi khi gửi PUT /api/demo/state:", res);
    updateSyncStatus("error", "Lỗi lưu máy chủ - Dữ liệu an toàn ở Local");
  }

  isPersisting = false;

  // Nếu có mutation mới trong khi gửi và không bị conflict -> tiếp tục gửi
  if (pendingStateToPersist && syncMode !== "conflict") {
    processPersistQueue();
  }
}

// Xử lý khi gặp HTTP 409 Conflict từ Backend
async function handleVersionConflict(localAttemptedGroups) {
  const backendRes = await fetchBackendState();
  if (!backendRes.success) {
    alert("Xung đột phiên bản: Dữ liệu đã thay đổi trên máy chủ, nhưng không thể tải phiên bản mới để so sánh. Ứng dụng chuyển sang chế độ Cục bộ.");
    syncMode = "local-only";
    updateSyncStatus("local-only", "Chế độ Cục bộ (Sau xung đột)");
    return;
  }

  const serverGroups = backendRes.data;
  const currentServerVersion = backendRes.version;

  showConflictModal({
    title: "Xung đột dữ liệu (Phát hiện thiết bị khác vừa cập nhật)",
    desc: `Một thiết bị khác đã lưu phiên bản mới (v${currentServerVersion}) lên máy chủ trong khi bạn đang thao tác (phiên bản của bạn: v${confirmedServerVersion}). Hãy chọn cách xử lý:`,
    actions: [
      {
        label: "1. Sử dụng dữ liệu mới từ Máy chủ (Khuyến nghị)",
        desc: `Tạo bản sao lưu dữ liệu hiện tại và cập nhật dữ liệu phiên bản v${currentServerVersion} từ máy chủ.`,
        onClick: () => {
          const backup = createVerifiedBackup();
          if (!backup.success) {
            alert(`Không thể sao lưu: ${backup.error}. Hủy thao tác.`);
            return;
          }
          groups = serverGroups;
          selectedGroupId = groups[0]?.id || "";
          confirmedServerVersion = currentServerVersion;
          syncMode = "synced";
          writeLocalStorage(groups);
          saveSyncMetadata();
          updateSyncStatus("synced", `Đã cập nhật theo máy chủ (v${confirmedServerVersion})`);
          renderAll();
        }
      },
      {
        label: "2. Ghi đè Máy chủ bằng dữ liệu hiện tại của bạn",
        desc: `Lấy phiên bản v${currentServerVersion} làm mốc và đẩy toàn bộ dữ liệu của bạn lên máy chủ.`,
        onClick: async () => {
          const backup = createVerifiedBackup();
          if (!backup.success) {
            alert(`Không thể sao lưu: ${backup.error}. Hủy thao tác.`);
            return;
          }
          // Đặt confirmedServerVersion thành phiên bản server vừa lấy
          confirmedServerVersion = currentServerVersion;
          syncMode = "saving";
          updateSyncStatus("saving", "Đang ghi đè máy chủ...");
          const putRes = await putBackendStateWithVersion(localAttemptedGroups, confirmedServerVersion);
          if (putRes.success) {
            confirmedServerVersion = putRes.version;
            syncMode = "synced";
            groups = localAttemptedGroups;
            selectedGroupId = groups[0]?.id || "";
            writeLocalStorage(groups);
            saveSyncMetadata();
            updateSyncStatus("synced", `Đã ghi đè thành công (v${confirmedServerVersion})`);
            renderAll();
          } else if (putRes.status === 409) {
            alert("Máy chủ tiếp tục bị thay đổi bởi thiết bị khác trong lúc bạn xác nhận. Vui lòng thử lại.");
            await handleVersionConflict(localAttemptedGroups);
          } else {
            alert("Lỗi khi ghi đè lên máy chủ. Dữ liệu trên trình duyệt vẫn được giữ an toàn.");
            updateSyncStatus("error", "Lỗi ghi đè máy chủ");
          }
        }
      },
      {
        label: "3. Giữ nguyên trên Trình duyệt (Chuyển sang Cục bộ)",
        desc: "Không gửi dữ liệu lên máy chủ nữa, giữ nguyên trạng thái làm việc offline.",
        onClick: () => {
          syncMode = "local-only";
          saveSyncMetadata();
          updateSyncStatus("local-only", "Chế độ Cục bộ (Đã tắt đồng bộ)");
          renderAll();
        }
      }
    ]
  });
}

// ==========================================
// 4. CONFLICT & MIGRATION RESOLUTION (STARTUP)
// ==========================================

function showConflictModal({ title, desc, actions }) {
  const modal = document.getElementById("conflict-modal");
  document.getElementById("conflict-modal-title").textContent = title;
  document.getElementById("conflict-modal-desc").textContent = desc;

  const container = document.getElementById("conflict-actions");
  container.innerHTML = "";

  actions.forEach((act) => {
    const card = document.createElement("button");
    card.className = "action-card";

    const strong = document.createElement("strong");
    strong.textContent = act.label;

    const span = document.createElement("span");
    span.textContent = act.desc;

    card.appendChild(strong);
    card.appendChild(span);

    card.onclick = () => {
      modal.classList.add("hidden");
      act.onClick();
    };
    container.appendChild(card);
  });

  modal.classList.remove("hidden");
}

async function handleStartupResolution() {
  loadSyncMetadata();

  const localGroups = parseLocalGroups();
  const hasLocalData = Array.isArray(localGroups) && localGroups.length > 0;

  // Kiểm tra Backend
  const backendRes = await fetchBackendState();
  const pill = document.getElementById("backend-status");

  if (!backendRes.success) {
    // Backend không khả dụng
    isBackendOnline = false;
    pill.textContent = "Máy chủ ngoại tuyến";
    pill.className = "status-pill offline";
    updateSyncStatus("local-only", "Chế độ Cục bộ (Máy chủ offline)");

    groups = hasLocalData ? localGroups : [];
    selectedGroupId = groups[0]?.id || "";
    renderAll();
    return;
  }

  // Backend online
  isBackendOnline = true;
  pill.textContent = "Đã nối FastAPI :8000";
  pill.className = "status-pill online";

  const backendGroups = backendRes.data;
  const currentServerVer = backendRes.version;
  const hasBackendData = Array.isArray(backendGroups) && backendGroups.length > 0;

  // Nếu người dùng trước đó đã chọn local-only một cách chủ động
  if (syncMode === "local-only" && hasLocalData) {
    groups = localGroups;
    selectedGroupId = groups[0]?.id || "";
    updateSyncStatus("local-only", "Chế độ Cục bộ (Tùy chọn đã lưu)");
    renderAll();
    return;
  }

  // Case 1: Cả 2 đều rỗng (Database chưa có bản ghi, version = 0)
  if (!hasBackendData && !hasLocalData) {
    groups = [];
    selectedGroupId = "";
    confirmedServerVersion = currentServerVer;
    syncMode = "synced";
    updateSyncStatus("synced", "Máy chủ sẵn sàng (v" + confirmedServerVersion + ")");
    renderAll();
    return;
  }

  // Case 2: Backend rỗng (version 0), Local có dữ liệu -> Hỏi import
  if (!hasBackendData && hasLocalData) {
    showConflictModal({
      title: "Di chuyển dữ liệu lên Máy chủ",
      desc: `Phát hiện ${localGroups.length} nhóm dữ liệu có sẵn trên trình duyệt nhưng máy chủ Neon hiện đang trống. Bạn có muốn tải dữ liệu này lên máy chủ không?`,
      actions: [
        {
          label: "1. Tải dữ liệu lên Máy chủ (Khuyến nghị)",
          desc: "Tạo bản sao lưu và lưu toàn bộ dữ liệu này vào Neon PostgreSQL.",
          onClick: async () => {
            const backup = createVerifiedBackup();
            if (!backup.success) {
              alert(`Không thể tạo sao lưu: ${backup.error}. Hủy thao tác.`);
              groups = localGroups;
              selectedGroupId = groups[0]?.id || "";
              updateSyncStatus("local-only", "Chế độ Cục bộ (Hủy di chuyển)");
              renderAll();
              return;
            }
            updateSyncStatus("saving", "Đang chuyển dữ liệu lên Neon...");
            const putRes = await putBackendStateWithVersion(localGroups, 0);
            if (putRes.success) {
              confirmedServerVersion = putRes.version;
              syncMode = "synced";
              groups = localGroups;
              selectedGroupId = groups[0]?.id || "";
              saveSyncMetadata();
              updateSyncStatus("synced", `Đã di chuyển thành công (v${confirmedServerVersion})`);
            } else {
              alert("Lỗi khi tải dữ liệu lên máy chủ. Dữ liệu trên trình duyệt vẫn được giữ nguyên an toàn.");
              groups = localGroups;
              selectedGroupId = groups[0]?.id || "";
              updateSyncStatus("error", "Lỗi tải lên máy chủ");
            }
            renderAll();
          }
        },
        {
          label: "2. Giữ nguyên trên Trình duyệt (Chế độ Cục bộ)",
          desc: "Chỉ hiển thị dữ liệu cục bộ, không ghi vào cơ sở dữ liệu máy chủ.",
          onClick: () => {
            groups = localGroups;
            selectedGroupId = groups[0]?.id || "";
            syncMode = "local-only";
            saveSyncMetadata();
            updateSyncStatus("local-only", "Chế độ Cục bộ (Không đồng bộ)");
            renderAll();
          }
        }
      ]
    });
    return;
  }

  // Case 3: Backend có dữ liệu, Local rỗng -> Khôi phục từ Backend
  if (hasBackendData && !hasLocalData) {
    groups = backendGroups;
    confirmedServerVersion = currentServerVer;
    syncMode = "synced";
    selectedGroupId = groups[0]?.id || "";
    writeLocalStorage(groups);
    saveSyncMetadata();
    updateSyncStatus("synced", `Đã nạp dữ liệu máy chủ (v${confirmedServerVersion})`);
    renderAll();
    return;
  }

  // Case 4: Cả 2 có dữ liệu và GIỐNG HỆT NHAU
  if (hasBackendData && hasLocalData && areGroupsEqual(backendGroups, localGroups)) {
    groups = backendGroups;
    confirmedServerVersion = currentServerVer;
    syncMode = "synced";
    selectedGroupId = groups[0]?.id || "";
    saveSyncMetadata();
    updateSyncStatus("synced", `Đã đồng bộ (v${confirmedServerVersion})`);
    renderAll();
    return;
  }

  // Case 5: Cả 2 có dữ liệu nhưng KHÁC NHAU
  if (hasBackendData && hasLocalData && !areGroupsEqual(backendGroups, localGroups)) {
    showConflictModal({
      title: "Xung đột dữ liệu ban đầu",
      desc: `Dữ liệu trên máy chủ Neon (v${currentServerVer}) khác với dữ liệu đang lưu trong trình duyệt của bạn. Hãy chọn nguồn dữ liệu bạn muốn sử dụng:`,
      actions: [
        {
          label: "1. Sử dụng dữ liệu từ Máy chủ (Khuyến nghị)",
          desc: "Tạo bản sao lưu dữ liệu trình duyệt và nạp dữ liệu máy chủ vào màn hình.",
          onClick: () => {
            const backup = createVerifiedBackup();
            if (!backup.success) {
              alert(`Không thể sao lưu: ${backup.error}. Hủy thao tác.`);
              return;
            }
            groups = backendGroups;
            selectedGroupId = groups[0]?.id || "";
            confirmedServerVersion = currentServerVer;
            syncMode = "synced";
            writeLocalStorage(groups);
            saveSyncMetadata();
            updateSyncStatus("synced", `Đã nạp dữ liệu máy chủ (v${confirmedServerVersion})`);
            renderAll();
          }
        },
        {
          label: "2. Ghi đè Máy chủ bằng dữ liệu Trình duyệt",
          desc: `Tạo bản sao lưu và cập nhật dữ liệu của bạn lên máy chủ (đè lên v${currentServerVer}).`,
          onClick: async () => {
            const backup = createVerifiedBackup();
            if (!backup.success) {
              alert(`Không thể sao lưu: ${backup.error}. Hủy thao tác.`);
              return;
            }
            updateSyncStatus("saving", "Đang ghi đè lên máy chủ...");
            const putRes = await putBackendStateWithVersion(localGroups, currentServerVer);
            if (putRes.success) {
              groups = localGroups;
              selectedGroupId = groups[0]?.id || "";
              confirmedServerVersion = putRes.version;
              syncMode = "synced";
              saveSyncMetadata();
              updateSyncStatus("synced", `Đã ghi đè thành công (v${confirmedServerVersion})`);
            } else {
              alert("Lỗi khi ghi đè dữ liệu lên máy chủ. Dữ liệu trình duyệt vẫn an toàn.");
              groups = localGroups;
              selectedGroupId = groups[0]?.id || "";
              updateSyncStatus("error", "Lỗi ghi đè máy chủ");
            }
            renderAll();
          }
        },
        {
          label: "3. Giữ nguyên trên Trình duyệt (Chế độ Cục bộ)",
          desc: "Không thay đổi máy chủ, chuyển sang chế độ làm việc cục bộ an toàn.",
          onClick: () => {
            groups = localGroups;
            selectedGroupId = groups[0]?.id || "";
            syncMode = "local-only";
            saveSyncMetadata();
            updateSyncStatus("local-only", "Chế độ Cục bộ (Chưa đồng bộ)");
            renderAll();
          }
        }
      ]
    });
  }
}

// ==========================================
// 5. VIEW RENDERING & DOM MANIPULATION (XSS-SAFE)
// ==========================================

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  document.getElementById(`view-${viewName}`).classList.add("active");
  renderAll();
}

function renderDashboard() {
  const groupListEl = document.getElementById("group-list");
  groupListEl.innerHTML = "";

  if (groups.length === 0) {
    const emptyP = document.createElement("p");
    emptyP.className = "muted-text";
    emptyP.style.padding = "8px";
    emptyP.textContent = "Chưa có nhóm nào. Vui lòng tạo nhóm mới bên dưới.";
    groupListEl.appendChild(emptyP);

    document.getElementById("dash-group-title").textContent = "Chưa chọn nhóm";
    document.getElementById("dash-group-members").textContent = "";
    document.getElementById("balance-table-body").innerHTML = "";
    const histEl = document.getElementById("expense-history-list");
    histEl.innerHTML = "";
    const noExp = document.createElement("p");
    noExp.className = "muted-text";
    noExp.textContent = "Chưa có hóa đơn nào.";
    histEl.appendChild(noExp);
    return;
  }

  groups.forEach((g) => {
    const btn = document.createElement("button");
    btn.className = `group-item ${g.id === selectedGroupId ? "active" : ""}`;
    const spanName = document.createElement("span");
    spanName.textContent = g.name;

    const spanCount = document.createElement("span");
    spanCount.textContent = `(${g.members ? g.members.length : 0})`;

    btn.appendChild(spanName);
    btn.appendChild(spanCount);

    btn.onclick = () => {
      selectedGroupId = g.id;
      renderAll();
    };
    groupListEl.appendChild(btn);
  });

  const current = getCurrentGroup();
  if (!current) return;

  document.getElementById("dash-group-title").textContent = `Nhóm: ${current.name}`;
  document.getElementById("dash-group-members").textContent = `Thành viên: ${(current.members || []).join(", ")}`;

  const tbody = document.getElementById("balance-table-body");
  tbody.innerHTML = "";

  (current.members || []).forEach((member) => {
    const bal = Number(current.balances?.[member] || 0);
    let statusText = "Cân bằng";
    let cls = "text-neutral";
    let sign = "";

    if (bal > 0.5) {
      statusText = `Được nhận +${formatVND(bal)}`;
      cls = "text-pos";
      sign = "+";
    } else if (bal < -0.5) {
      statusText = `Nợ ${formatVND(Math.abs(bal))}`;
      cls = "text-neg";
    }

    const tr = document.createElement("tr");

    const tdName = document.createElement("td");
    const strongName = document.createElement("strong");
    strongName.textContent = member;
    tdName.appendChild(strongName);

    const tdBal = document.createElement("td");
    tdBal.className = cls;
    tdBal.textContent = `${sign}${formatVND(bal)}`;

    const tdStatus = document.createElement("td");
    tdStatus.className = cls;
    tdStatus.textContent = statusText;

    tr.appendChild(tdName);
    tr.appendChild(tdBal);
    tr.appendChild(tdStatus);
    tbody.appendChild(tr);
  });

  const historyEl = document.getElementById("expense-history-list");
  historyEl.innerHTML = "";
  if (!current.expenses || current.expenses.length === 0) {
    const p = document.createElement("p");
    p.className = "muted-text";
    p.textContent = "Chưa có hóa đơn nào trong nhóm này.";
    historyEl.appendChild(p);
    return;
  }

  [...current.expenses].reverse().forEach((exp) => {
    const div = document.createElement("div");
    div.className = "row-card";

    const left = document.createElement("div");
    const strongTitle = document.createElement("strong");
    strongTitle.textContent = exp.title;

    const pMeta = document.createElement("p");
    pMeta.className = "muted-text small";
    pMeta.textContent = `${exp.payer} trả • Chia cho ${exp.participants.length} người (${exp.participants.join(", ")})`;

    left.appendChild(strongTitle);
    left.appendChild(pMeta);

    const right = document.createElement("strong");
    right.className = "text-pos";
    right.textContent = formatVND(exp.amount);

    div.appendChild(left);
    div.appendChild(right);
    historyEl.appendChild(div);
  });
}

function renderExpenseForm() {
  const groupSelect = document.getElementById("exp-group");
  groupSelect.innerHTML = "";

  if (groups.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "-- Chưa có nhóm nào --";
    groupSelect.appendChild(opt);
    document.getElementById("exp-payer").innerHTML = "";
    document.getElementById("exp-participants").innerHTML = "";
    return;
  }

  groups.forEach((g) => {
    const opt = document.createElement("option");
    opt.value = g.id;
    opt.textContent = g.name;
    if (g.id === selectedGroupId) opt.selected = true;
    groupSelect.appendChild(opt);
  });

  updateExpenseMembers(groupSelect.value || groups[0].id);
}

function updateExpenseMembers(groupId) {
  const grp = groups.find((g) => g.id === groupId);
  if (!grp) return;

  const payerSelect = document.getElementById("exp-payer");
  payerSelect.innerHTML = "";
  (grp.members || []).forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    payerSelect.appendChild(opt);
  });

  const box = document.getElementById("exp-participants");
  box.innerHTML = "";
  (grp.members || []).forEach((m) => {
    const label = document.createElement("label");
    label.className = "checkbox-item";

    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.name = "participant";
    chk.value = m;
    chk.checked = true;

    const span = document.createElement("span");
    span.textContent = m;

    label.appendChild(chk);
    label.appendChild(span);
    box.appendChild(label);
  });
}

function computeSettlements(group) {
  if (!group || !group.balances) return [];
  const debtors = [];
  const creditors = [];

  Object.entries(group.balances).forEach(([person, bal]) => {
    if (bal < -0.5) debtors.push({ person, amount: -bal });
    else if (bal > 0.5) creditors.push({ person, amount: bal });
  });

  debtors.sort((a, b) => b.amount - a.amount);
  creditors.sort((a, b) => b.amount - a.amount);

  const transfers = [];
  let i = 0;
  let j = 0;

  while (i < debtors.length && j < creditors.length) {
    const pay = Math.min(debtors[i].amount, creditors[j].amount);
    transfers.push({
      from: debtors[i].person,
      to: creditors[j].person,
      amount: Math.round(pay),
    });
    debtors[i].amount -= pay;
    creditors[j].amount -= pay;
    if (debtors[i].amount <= 0.5) i++;
    if (creditors[j].amount <= 0.5) j++;
  }
  return transfers;
}

function renderSettlements() {
  const current = getCurrentGroup();
  if (!current) {
    document.getElementById("settle-title").textContent = "Kết quả tối ưu nợ";
    const listEl = document.getElementById("settlement-list");
    listEl.innerHTML = "";
    const row = document.createElement("div");
    row.className = "row-card";
    const p = document.createElement("p");
    p.textContent = "Chưa có nhóm nào được chọn.";
    row.appendChild(p);
    listEl.appendChild(row);
    return;
  }

  document.getElementById("settle-title").textContent = `Kết quả tối ưu nợ — ${current.name}`;
  const listEl = document.getElementById("settlement-list");
  listEl.innerHTML = "";
  const transfers = computeSettlements(current);

  if (transfers.length === 0) {
    const row = document.createElement("div");
    row.className = "row-card";
    const p = document.createElement("p");
    p.textContent = "Tất cả thành viên đã cân bằng, không cần chuyển khoản thêm.";
    row.appendChild(p);
    listEl.appendChild(row);
    return;
  }

  transfers.forEach((t) => {
    const row = document.createElement("div");
    row.className = "row-card";

    const left = document.createElement("div");
    const strongFrom = document.createElement("strong");
    strongFrom.textContent = t.from;
    const txtTo = document.createTextNode(" trả cho ");
    const strongTo = document.createElement("strong");
    strongTo.textContent = t.to;

    left.appendChild(strongFrom);
    left.appendChild(txtTo);
    left.appendChild(strongTo);

    const right = document.createElement("div");
    right.className = "header-actions";
    right.style.alignItems = "center";

    const strongAmount = document.createElement("strong");
    strongAmount.className = "text-pos";
    strongAmount.style.marginRight = "8px";
    strongAmount.textContent = formatVND(t.amount);

    const btn = document.createElement("button");
    btn.className = "btn btn-primary";
    btn.textContent = "VietQR";
    btn.onclick = () => openVietQR(t.from, t.to, t.amount);

    right.appendChild(strongAmount);
    right.appendChild(btn);

    row.appendChild(left);
    row.appendChild(right);
    listEl.appendChild(row);
  });
}

function openVietQR(sender, receiver, amount) {
  const modal = document.getElementById("qr-modal");
  const info = document.getElementById("qr-info");
  const img = document.getElementById("qr-image");

  const addInfo = encodeURIComponent(`${sender} tra ${receiver} ChuDe13`);
  const accountName = encodeURIComponent(receiver);
  img.src = `https://img.vietqr.io/image/MB-0000000000-compact2.png?amount=${amount}&addInfo=${addInfo}&accountName=${accountName}`;
  info.textContent = `${sender} → ${receiver}: ${formatVND(amount)}`;

  document.getElementById("settle-status").textContent = `Đang mở mã VietQR: ${sender} -> ${receiver} (${formatVND(amount)})`;
  modal.classList.remove("hidden");
}

function exportReport(ext) {
  const current = getCurrentGroup();
  if (!current) return;
  const transfers = computeSettlements(current);

  let csv = "\uFEFFNhom,Nguoi tra,Nguoi nhan,So tien (VND)\n";
  transfers.forEach((t) => {
    csv += `"${current.name}","${t.from}","${t.to}",${t.amount}\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Bao_cao_toi_uu_no_${current.id}.${ext}`;
  a.click();
  URL.revokeObjectURL(url);

  document.getElementById("settle-status").textContent = `Đã tải xuống báo cáo dạng .${ext.toUpperCase()}`;
}

function renderAll() {
  renderDashboard();
  renderExpenseForm();
  renderSettlements();
}

// ==========================================
// 6. INITIALIZATION & EVENT LISTENERS
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
  handleStartupResolution();

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  // Tạo nhóm mới (Mutation Point 1)
  document.getElementById("create-group-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("new-group-name").value.trim();
    const members = document
      .getElementById("new-group-members")
      .value.split(",")
      .map((m) => m.trim())
      .filter(Boolean);

    if (!name || members.length === 0) return;

    const balances = {};
    members.forEach((m) => (balances[m] = 0));

    const newGrp = {
      id: `g${Date.now()}`,
      name,
      members,
      balances,
      expenses: [],
    };
    groups.push(newGrp);
    selectedGroupId = newGrp.id;

    // Chuyển sang pipeline lưu duy nhất
    enqueuePersist(groups);

    e.target.reset();
    renderAll();
  });

  // Chọn nhóm trong form chi tiêu
  document.getElementById("exp-group").addEventListener("change", (e) => {
    selectedGroupId = e.target.value;
    updateExpenseMembers(selectedGroupId);
  });

  // Toggle chọn tất cả thành viên
  document.getElementById("btn-toggle-all").addEventListener("click", () => {
    const boxes = [...document.querySelectorAll('input[name="participant"]')];
    const allChecked = boxes.every((b) => b.checked);
    boxes.forEach((b) => (b.checked = !allChecked));
  });

  // Thêm hóa đơn chi tiêu (Mutation Point 2)
  document.getElementById("expense-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const gid = document.getElementById("exp-group").value;
    const title = document.getElementById("exp-title").value.trim() || "Khoản chi";
    const amount = Number(document.getElementById("exp-amount").value);
    const payer = document.getElementById("exp-payer").value;
    const participants = [...document.querySelectorAll('input[name="participant"]:checked')].map((el) => el.value);
    const msgEl = document.getElementById("exp-message");

    const grp = groups.find((g) => g.id === gid);
    if (!grp || amount <= 0 || participants.length === 0) {
      msgEl.textContent = "Vui lòng nhập số tiền > 0 và chọn ít nhất 1 thành viên.";
      msgEl.style.color = "#c62828";
      return;
    }

    grp.expenses.push({ title, amount, payer, participants });
    const share = amount / participants.length;

    grp.members.forEach((m) => {
      grp.balances[m] = grp.balances[m] || 0;
      if (m === payer) grp.balances[m] += amount;
      if (participants.includes(m)) grp.balances[m] -= share;
    });

    selectedGroupId = gid;

    // Chuyển sang pipeline lưu duy nhất
    enqueuePersist(groups);

    document.getElementById("exp-title").value = "";
    document.getElementById("exp-amount").value = "";
    msgEl.textContent = "Đã ghi nhận hóa đơn!";
    msgEl.style.color = "#2e7d32";
    renderAll();
  });

  // Đóng modal VietQR
  document.getElementById("btn-close-qr").addEventListener("click", () => {
    document.getElementById("qr-modal").classList.add("hidden");
  });

  // Xuất file
  document.getElementById("btn-export-csv").addEventListener("click", () => exportReport("csv"));
  document.getElementById("btn-export-excel").addEventListener("click", () => exportReport("xls"));

  // Khôi phục dữ liệu mẫu (Mutation Point 3 - Reset)
  const resetModal = document.getElementById("reset-confirm-modal");
  const resetDesc = document.getElementById("reset-modal-desc");

  document.getElementById("btn-reset-demo").addEventListener("click", () => {
    if (isBackendOnline && syncMode !== "local-only") {
      resetDesc.textContent = `Thao tác này sẽ khôi phục dữ liệu mẫu mặc định trên CẢ Máy chủ Neon (phiên bản tiếp theo) và Trình duyệt của bạn. Bản sao lưu dữ liệu hiện tại sẽ được lưu an toàn.`;
    } else {
      resetDesc.textContent = "Bạn đang ở Chế độ Cục bộ hoặc Máy chủ ngoại tuyến. Thao tác này sẽ khôi phục dữ liệu mẫu CHỈ trên Trình duyệt này (Cục bộ). Bản sao lưu dữ liệu hiện tại sẽ được lưu an toàn.";
    }
    resetModal.classList.remove("hidden");
  });

  document.getElementById("btn-cancel-reset").addEventListener("click", () => {
    resetModal.classList.add("hidden");
  });

  document.getElementById("btn-confirm-reset").addEventListener("click", async () => {
    resetModal.classList.add("hidden");

    // 1. Tạo và xác minh sao lưu trước khi thực hiện hành động phá hủy
    const backup = createVerifiedBackup();
    if (!backup.success) {
      alert(`Không thể tạo bản sao lưu: ${backup.error}. Hủy thao tác khôi phục.`);
      return;
    }

    const resetData = structuredClone(DEFAULT_GROUPS);

    if (isBackendOnline && syncMode !== "local-only") {
      // Đưa qua pipeline lưu OCC duy nhất
      groups = resetData;
      selectedGroupId = groups[0].id;
      enqueuePersist(groups);
      renderAll();
    } else {
      // Offline hoặc Local-Only reset
      groups = resetData;
      selectedGroupId = groups[0].id;
      writeLocalStorage(groups);
      updateSyncStatus("local-only", "Đã khôi phục dữ liệu mẫu (Cục bộ)");
      renderAll();
    }
  });
});
