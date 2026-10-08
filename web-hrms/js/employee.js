/* ============================================================
   employee.js = employee dashboard, leave requests, payslips
   ============================================================ */

function bootEmployee(session) {
  const employee = Storage.getEmployee(session.employeeId);
  if (!employee) {
    UI.toast("This login is missing an employee record.");
    Auth.logout();
    return;
  }

  document.getElementById("emp-chip-name").textContent = employee.name;
  document.getElementById("emp-chip-role").textContent = employee.position;
  document.getElementById("emp-avatar").textContent = UI.initials(employee.name);
  document.getElementById("welcome-line").textContent = "Welcome back, " + employee.name.split(" ")[0] + ".";
  document.getElementById("emp-logout").addEventListener("click", () => Auth.logout());

  setupEmployeeNav();
  setupEmployeeMobile();
  setupLeaveForm(employee);
  renderEmployee(employee);
}

function setupEmployeeNav() {
  const titles = {
    dashboard: "My dashboard",
    profile: "My profile",
    leave: "Apply leave",
    payslips: "My payroll"
  };
  document.querySelectorAll("#emp-sidebar .nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#emp-sidebar .nav-btn[data-view]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      ["dashboard", "profile", "leave", "payslips"].forEach((name) => {
        document.getElementById("emp-view-" + name).classList.toggle("hidden", name !== view);
      });
      document.getElementById("emp-title").textContent = titles[view];
      closeEmployeeMobile();
    });
  });
}

function setupEmployeeMobile() {
  document.getElementById("emp-menu").addEventListener("click", () => {
    document.getElementById("emp-sidebar").classList.add("open");
    document.getElementById("emp-overlay").classList.add("open");
  });
  document.getElementById("emp-overlay").addEventListener("click", closeEmployeeMobile);
}

function closeEmployeeMobile() {
  document.getElementById("emp-sidebar").classList.remove("open");
  document.getElementById("emp-overlay").classList.remove("open");
}

function renderEmployee(employee) {
  renderEmpStats(employee);
  renderProfile(employee);
  renderLeaveTables(employee);
  renderBalances(employee);
  renderEmpPayroll(employee);
}

function renderEmpStats(employee) {
  const mine = Storage.getLeaves().filter((l) => l.employeeId === employee.id);
  const pending = mine.filter((l) => l.status === "pending").length;
  const approvedDays = mine.filter((l) => l.status === "approved").reduce((s, l) => s + Number(l.days), 0);
  const latest = latestPayslip(employee.id);

  document.getElementById("emp-stats").innerHTML = [
    `<article class="stat-card"><span>Department</span><strong style="font-size:1.15rem">${escapeText(employee.department)}</strong></article>`,
    `<article class="stat-card"><span>Pending requests</span><strong>${pending}</strong></article>`,
    `<article class="stat-card"><span>Approved leave days</span><strong>${approvedDays}</strong></article>`,
    `<article class="stat-card"><span>Latest net pay</span><strong>${latest ? UI.money(latest.netPay) : "—"}</strong></article>`
  ].join("");

  document.getElementById("latest-payslip").innerHTML = latest
    ? empPayslipHtml(employee, latest)
    : `<p class="empty">No payslip yet. Admin generates payroll from the admin page.</p>`;
}

function renderProfile(employee) {
  document.getElementById("profile-card").innerHTML = `
    <div class="panel-head"><h3>${escapeText(employee.name)}</h3><span class="badge badge-approved">${escapeText(employee.department)}</span></div>
    <div class="payslip-row"><span>Email</span><span>${escapeText(employee.email)}</span></div>
    <div class="payslip-row"><span>Phone</span><span>${escapeText(employee.phone || "—")}</span></div>
    <div class="payslip-row"><span>Position</span><span>${escapeText(employee.position)}</span></div>
    <div class="payslip-row"><span>Join date</span><span>${escapeText(employee.joinDate)}</span></div>
    <div class="payslip-row"><span>Basic salary</span><span>${UI.money(employee.basicSalary)}</span></div>
    <div class="payslip-row"><span>Allowances</span><span>${UI.money(employee.allowances)}</span></div>
    <div class="payslip-row total"><span>Monthly deductions</span><span>${UI.money(employee.deductions)}</span></div>
  `;
}

function setupLeaveForm(employee) {
  document.getElementById("leave-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const error = document.getElementById("leave-error");
    error.textContent = "";
    const type = document.getElementById("leave-type").value;
    const from = document.getElementById("leave-from").value;
    const to = document.getElementById("leave-to").value;
    const reason = document.getElementById("leave-reason").value.trim();
    const days = UI.daysBetween(from, to);

    if (!days) {
      error.textContent = "The end date must be on or after the start date.";
      return;
    }

    const used = usedLeaveDays(employee.id, type);
    const remaining = (LEAVE_LIMITS[type] || 0) - used;
    if (type !== "Unpaid" && days > remaining) {
      error.textContent = `Only ${remaining} ${type.toLowerCase()} day(s) left.`;
      return;
    }

    const leaves = Storage.getLeaves();
    leaves.push({
      id: Storage.id("lv"),
      employeeId: employee.id,
      type,
      from,
      to,
      days,
      reason,
      status: "pending",
      createdAt: new Date().toISOString().slice(0, 10)
    });
    Storage.saveLeaves(leaves);
    event.target.reset();
    renderEmployee(employee);
    UI.toast("Leave request sent.");
  });
}

function renderBalances(employee) {
  document.getElementById("leave-balances").innerHTML = ["Annual", "Sick", "Casual"]
    .map((type) => {
      const used = usedLeaveDays(employee.id, type);
      const left = LEAVE_LIMITS[type] - used;
      return `<div class="payslip-row"><span>${type}</span><strong>${left} / ${LEAVE_LIMITS[type]} days left</strong></div>`;
    })
    .join("");
}

function renderLeaveTables(employee) {
  const mine = Storage.getLeaves()
    .filter((l) => l.employeeId === employee.id)
    .slice()
    .reverse();
  const html = empLeaveTable(mine);
  document.getElementById("my-leave-preview").innerHTML = empLeaveTable(mine.slice(0, 5));
  document.getElementById("my-leave-table").innerHTML = html;
}

function empLeaveTable(leaves) {
  if (!leaves.length) return `<p class="empty">No leave requests yet.</p>`;
  return `<table>
    <thead><tr><th>Type</th><th>Dates</th><th>Days</th><th>Status</th></tr></thead>
    <tbody>
      ${leaves
        .map(
          (l) => `<tr>
            <td>${escapeText(l.type)}<br><small class="muted">${escapeText(l.reason)}</small></td>
            <td>${escapeText(l.from)} → ${escapeText(l.to)}</td>
            <td>${l.days}</td>
            <td>${UI.badge(l.status)}</td>
          </tr>`
        )
        .join("")}
    </tbody>
  </table>`;
}

function renderEmpPayroll(employee) {
  const rows = Storage.getPayroll()
    .filter((p) => p.employeeId === employee.id)
    .slice()
    .reverse();
  document.getElementById("my-payroll-table").innerHTML = rows.length
    ? `<table>
        <thead><tr><th>Month</th><th>Unpaid days</th><th>Net pay</th><th></th></tr></thead>
        <tbody>
          ${rows
            .map(
              (p) => `<tr>
                <td>${escapeText(p.month)}</td>
                <td>${p.unpaidDays}</td>
                <td><strong>${UI.money(p.netPay)}</strong></td>
                <td><button class="btn btn-ghost btn-sm" data-emp-slip="${p.month}">View</button></td>
              </tr>`
            )
            .join("")}
        </tbody>
      </table>`
    : `<p class="empty">No payslips yet.</p>`;

  document.querySelectorAll("[data-emp-slip]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const slip = rows.find((p) => p.month === btn.dataset.empSlip);
      const modal = document.getElementById("emp-payslip-modal");
      modal.innerHTML = `<div class="modal">${empPayslipHtml(employee, slip)}<div style="margin-top:14px;text-align:right;"><button class="btn btn-ghost" id="close-emp-slip">Close</button></div></div>`;
      modal.classList.remove("hidden");
      document.getElementById("close-emp-slip").addEventListener("click", () => modal.classList.add("hidden"));
      modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.add("hidden");
      });
    });
  });
}

function latestPayslip(employeeId) {
  return Storage.getPayroll()
    .filter((p) => p.employeeId === employeeId)
    .sort((a, b) => (a.month < b.month ? 1 : -1))[0];
}

function empPayslipHtml(employee, slip) {
  return `<h3>Payslip — ${escapeText(slip.month)}</h3>
    <p class="muted">${escapeText(employee.name)} · ${escapeText(employee.position)}</p>
    <div class="payslip">
      <div class="payslip-row"><span>Basic salary</span><span>${UI.money(slip.basicSalary)}</span></div>
      <div class="payslip-row"><span>Allowances</span><span>${UI.money(slip.allowances)}</span></div>
      <div class="payslip-row"><span>Fixed deductions</span><span>- ${UI.money(slip.deductions)}</span></div>
      <div class="payslip-row"><span>Unpaid leave (${slip.unpaidDays} days)</span><span>- ${UI.money(slip.leaveDeduction)}</span></div>
      <div class="payslip-row total"><span>Net pay</span><span>${UI.money(slip.netPay)}</span></div>
    </div>`;
}

function escapeText(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
