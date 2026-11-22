// Địa chỉ Backend FastAPI của nhóm (nếu đang chạy backend/routers/main.py)
const API_BASE_URL = "http://127.0.0.1:8000";
const STORAGE_KEY = "chude13_web_groups_v1";

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

let groups = loadGroups();
let selectedGroupId = groups[0]?.id || "";

function loadGroups() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.warn("Không đọc được localStorage:", e);
  }
  return structuredClone(DEFAULT_GROUPS);
}

function saveGroups() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(groups));
}

function formatVND(amount) {
  return Math.round(amount).toLocaleString("vi-VN") + " đ";
}

function getCurrentGroup() {
  return groups.find((g) => g.id === selectedGroupId) || groups[0];
}

// Kiểm tra kết nối Backend FastAPI nếu nhóm đang bật server
async function checkBackendHealth() {
  const pill = document.getElementById("backend-status");
  try {
    const res = await fetch(`${API_BASE_URL}/docs`, { method: "HEAD" });
    if (res.ok) {
      pill.textContent = "Đã nối FastAPI :8000";
      pill.className = "status-pill online";
    }
  } catch {
    pill.textContent = "Chế độ Local Web";
    pill.className = "status-pill offline";
  }
}

// Chuyển tab màn hình
function switchView(viewName) {
  document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  document.getElementById(`view-${viewName}`).classList.add("active");
  renderAll();
}

// Render Dashboard
function renderDashboard() {
  const groupListEl = document.getElementById("group-list");
  groupListEl.innerHTML = "";

  groups.forEach((g) => {
    const btn = document.createElement("button");
    btn.className = `group-item ${g.id === selectedGroupId ? "active" : ""}`;
    btn.innerHTML = `<span>${g.name}</span><span>(${g.members.length})</span>`;
    btn.onclick = () => {
      selectedGroupId = g.id;
      renderAll();
    };
    groupListEl.appendChild(btn);
  });

  const current = getCurrentGroup();
  if (!current) return;

  document.getElementById("dash-group-title").textContent = `Nhóm: ${current.name}`;
  document.getElementById("dash-group-members").textContent = `Thành viên: ${current.members.join(", ")}`;

  const tbody = document.getElementById("balance-table-body");
  tbody.innerHTML = "";

  current.members.forEach((member) => {
    const bal = Number(current.balances[member] || 0);
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
    tr.innerHTML = `
      <td><strong>${member}</strong></td>
      <td class="${cls}">${sign}${formatVND(bal)}</td>
      <td class="${cls}">${statusText}</td>
    `;
    tbody.appendChild(tr);
  });

  const historyEl = document.getElementById("expense-history-list");
  historyEl.innerHTML = "";
  if (!current.expenses || current.expenses.length === 0) {
    historyEl.innerHTML = `<p class="muted-text">Chưa có hóa đơn nào trong nhóm này.</p>`;
    return;
  }

  [...current.expenses].reverse().forEach((exp) => {
    const div = document.createElement("div");
    div.className = "row-card";
    div.innerHTML = `
      <div>
        <strong>${exp.title}</strong>
        <p class="muted-text small">${exp.payer} trả • Chia cho ${exp.participants.length} người (${exp.participants.join(", ")})</p>
      </div>
      <strong class="text-pos">${formatVND(exp.amount)}</strong>
    `;
    historyEl.appendChild(div);
  });
}

// Render Form Nhập hóa đơn
function renderExpenseForm() {
  const groupSelect = document.getElementById("exp-group");
  groupSelect.innerHTML = groups
    .map((g) => `<option value="${g.id}" ${g.id === selectedGroupId ? "selected" : ""}>${g.name}</option>`)
    .join("");

  updateExpenseMembers(groupSelect.value);
}

function updateExpenseMembers(groupId) {
  const grp = groups.find((g) => g.id === groupId);
  if (!grp) return;

  const payerSelect = document.getElementById("exp-payer");
  payerSelect.innerHTML = grp.members.map((m) => `<option value="${m}">${m}</option>`).join("");

  const box = document.getElementById("exp-participants");
  box.innerHTML = grp.members
    .map(
      (m) => `
      <label class="checkbox-item">
        <input type="checkbox" name="participant" value="${m}" checked />
        <span>${m}</span>
      </label>`
    )
    .join("");
}

// Thuật toán tối ưu giao dịch trả nợ
function computeSettlements(group) {
  if (!group) return [];
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

// Render Màn hình Tối ưu nợ
function renderSettlements() {
  const current = getCurrentGroup();
  if (!current) return;

  document.getElementById("settle-title").textContent = `Kết quả tối ưu nợ — ${current.name}`;
  const listEl = document.getElementById("settlement-list");
  const transfers = computeSettlements(current);

  if (transfers.length === 0) {
    listEl.innerHTML = `<div class="row-card"><p>Tất cả thành viên đã cân bằng, không cần chuyển khoản thêm.</p></div>`;
    return;
  }

  listEl.innerHTML = "";
  transfers.forEach((t) => {
    const row = document.createElement("div");
    row.className = "row-card";
    row.innerHTML = `
      <div><strong>${t.from}</strong> trả cho <strong>${t.to}</strong></div>
      <div class="header-actions" style="align-items:center;">
        <strong class="text-pos" style="margin-right:8px;">${formatVND(t.amount)}</strong>
        <button class="btn btn-primary" onclick="openVietQR('${t.from}', '${t.to}', ${t.amount})">VietQR</button>
      </div>
    `;
    listEl.appendChild(row);
  });
}

function openVietQR(sender, receiver, amount) {
  const modal = document.getElementById("qr-modal");
  const info = document.getElementById("qr-info");
  const img = document.getElementById("qr-image");

  const addInfo = encodeURIComponent(`${sender} tra ${receiver} ChuDe13`);
  const accountName = encodeURIComponent(receiver);
  // Link ảnh VietQR chuẩn (có thể thay mã ngân hàng & STK thật của từng thành viên)
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

// Khởi tạo sự kiện
document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  renderAll();

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

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
    saveGroups();

    e.target.reset();
    renderAll();
  });

  document.getElementById("exp-group").addEventListener("change", (e) => {
    selectedGroupId = e.target.value;
    updateExpenseMembers(selectedGroupId);
  });

  document.getElementById("btn-toggle-all").addEventListener("click", () => {
    const boxes = [...document.querySelectorAll('input[name="participant"]')];
    const allChecked = boxes.every((b) => b.checked);
    boxes.forEach((b) => (b.checked = !allChecked));
  });

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
    saveGroups();

    document.getElementById("exp-title").value = "";
    document.getElementById("exp-amount").value = "";
    msgEl.textContent = "Đã lưu hóa đơn thành công!";
    msgEl.style.color = "#2e7d32";
    renderAll();
  });

  document.getElementById("btn-close-qr").addEventListener("click", () => {
    document.getElementById("qr-modal").classList.add("hidden");
  });

  document.getElementById("btn-export-csv").addEventListener("click", () => exportReport("csv"));
  document.getElementById("btn-export-excel").addEventListener("click", () => exportReport("xls"));

  document.getElementById("btn-reset-demo").addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    groups = loadGroups();
    selectedGroupId = groups[0].id;
    renderAll();
  });
});