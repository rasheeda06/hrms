/* ============================================================
   admin.js = admin dashboard, employees, leave, payroll
   ============================================================ */

function bootAdmin(session) {
  document.getElementById("admin-name").textContent = session.name;
  document.getElementById("admin-avatar").textContent = UI.initials(session.name);
  document.getElementById("admin-logout").addEventListener("click", () => Auth.logout());
  document.getElementById("reset-demo").addEventListener("click", () => {
    if (confirm("Reset all Haven HR data back to the demo accounts?")) {
      Storage.resetDemo();
      Auth.logout();
    }
  });

  setupAdminNav();
  setupAdminMobile();
  setupEmployeeForm();
  setupLeaveFilter();
  setupPayroll();
  renderAdmin();
}

function setupAdminNav() {
  const titles = {
    dashboard: ["Dashboard", "Overview of people, leave, and pay."],
    employees: ["Employees", "Add, edit, or remove people and their login accounts."],
    leaves: ["Leave management", "Approve or reject team time off."],
    payroll: ["Payroll", "Generate monthly net pay for the whole team."]
  };

  document.querySelectorAll("#admin-sidebar .nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#admin-sidebar .nav-btn[data-view]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      ["dashboard", "employees", "leaves", "payroll"].forEach((name) => {
        document.getElementById("admin-view-" + name).classList.toggle("hidden", name !== view);
      });
      document.getElementById("admin-title").textContent = titles[view][0];
      document.getElementById("admin-sub").textContent = titles[view][1];
      closeAdminMobile();
      renderAdmin();
    });
  });
}

function setupAdminMobile() {
  document.getElementById("admin-menu").addEventListener("click", () => {
    document.getElementById("admin-sidebar").classList.add("open");
    document.getElementById("admin-overlay").classList.add("open");
  });
  document.getElementById("admin-overlay").addEventListener("click", closeAdminMobile);
}

function closeAdminMobile() {
  document.getElementById("admin-sidebar").classList.remove("open");
  document.getElementById("admin-overlay").classList.remove("open");
}

function renderAdmin() {
  renderDashboard();
  renderEmployees(document.getElementById("employee-search").value);
  renderLeaves(document.getElementById("leave-filter").value);
  renderPayroll();
}

function renderDashboard() {
  const employees = Storage.getEmployees();
  const leaves = Storage.getLeaves();
  const pending = leaves.filter((l) => l.status === "pending");
  const payroll = Storage.getPayroll();
  const thisMonth = new Date().toISOString().slice(0, 7);
  const monthPay = payroll.filter((p) => p.month === thisMonth);
  const payrollTotal = monthPay.reduce((sum, p) => sum + Number(p.netPay), 0);

  document.getElementById("dash-stats").innerHTML = [
    adminCard("People", employees.length),
    adminCard("Pending leave", pending.length),
    adminCard("Payslips this month", monthPay.length),
    adminCard("Payroll total", UI.money(payrollTotal))
  ].join("");

  document.getElementById("dash-leaves").innerHTML = leaveTable(pending.slice(0, 6), true);
  document.getElementById("dash-team").innerHTML = employees
    .map(
      (e) =>
        `<div class="payslip-row"><span>${escapeHtml(e.name)}<br><small class="muted">${escapeHtml(e.position)}</small></span><strong>${escapeHtml(e.department)}</strong></div>`
    )
    .join("") || `<p class="empty">No employees yet.</p>`;
}

function adminCard(label, value) {
  return `<article class="stat-card"><span>${label}</span><strong>${value}</strong></article>`;
}

function renderEmployees(query) {
  const q = String(query || "").toLowerCase();
  const rows = Storage.getEmployees().filter((e) =>
    [e.name, e.email, e.department, e.position].join(" ").toLowerCase().includes(q)
  );

  document.getElementById("employee-table").innerHTML = table(
    ["Name", "Department", "Position", "Salary", "Actions"],
    rows.map(
      (e) => `<tr>
        <td><strong>${escapeHtml(e.name)}</strong><br><small class="muted">${escapeHtml(e.email)}</small></td>
        <td>${escapeHtml(e.department)}</td>
        <td>${escapeHtml(e.position)}</td>
        <td>${UI.money(e.basicSalary)}</td>
        <td class="row-actions">
          <button class="btn btn-ghost btn-sm" data-edit="${e.id}">Edit</button>
          <button class="btn btn-danger btn-sm" data-del="${e.id}">Delete</button>
        </td>
      </tr>`
    )
  );

  document.querySelectorAll("[data-edit]").forEach((btn) =>
    btn.addEventListener("click", () => openEmployeeModal(btn.dataset.edit))
  );
  document.querySelectorAll("[data-del]").forEach((btn) =>
    btn.addEventListener("click", () => deleteEmployee(btn.dataset.del))
  );
}

function setupEmployeeForm() {
  document.getElementById("employee-search").addEventListener("input", (e) => renderEmployees(e.target.value));
  document.getElementById("add-employee-btn").addEventListener("click", () => openEmployeeModal());
  document.getElementById("cancel-employee").addEventListener("click", closeEmployeeModal);
  document.getElementById("employee-modal").addEventListener("click", (e) => {
    if (e.target.id === "employee-modal") closeEmployeeModal();
  });

  document.getElementById("employee-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const id = document.getElementById("emp-id").value || Storage.id("emp");
    const employee = {
      id,
      name: val("emp-name"),
      email: val("emp-email"),
      phone: val("emp-phone"),
      department: val("emp-dept"),
      position: val("emp-position"),
      joinDate: val("emp-join"),
      basicSalary: Number(val("emp-basic")),
      allowances: Number(val("emp-allow") || 0),
      deductions: Number(val("emp-deduct") || 0)
    };
    const username = val("emp-user").toLowerCase();
    const password = val("emp-pass");

    const users = Storage.getUsers();
    if (users.some((u) => u.username.toLowerCase() === username && u.employeeId !== id && u.role === "employee")) {
      UI.toast("That username is already taken.");
      return;
    }
    if (users.some((u) => u.username.toLowerCase() === username && u.role === "admin")) {
      UI.toast("That username is already taken.");
      return;
    }

    const employees = Storage.getEmployees();
    const existing = employees.findIndex((e) => e.id === id);
    if (existing >= 0) employees[existing] = employee;
    else employees.push(employee);
    Storage.saveEmployees(employees);

    const userIndex = users.findIndex((u) => u.employeeId === id);
    const userRecord = {
      id: userIndex >= 0 ? users[userIndex].id : Storage.id("usr"),
      username,
      password,
      role: "employee",
      name: employee.name,
      employeeId: id
    };
    if (userIndex >= 0) users[userIndex] = userRecord;
    else users.push(userRecord);
    Storage.saveUsers(users);

    closeEmployeeModal();
    renderAdmin();
    UI.toast(existing >= 0 ? "Employee updated." : "Employee added.");
  });
}

function openEmployeeModal(id) {
  const form = document.getElementById("employee-form");
  form.reset();
  document.getElementById("emp-id").value = "";
  document.getElementById("employee-modal-title").textContent = "Add employee";
  if (id) {
    const emp = Storage.getEmployee(id);
    const user = Storage.getUsers().find((u) => u.employeeId === id);
    document.getElementById("employee-modal-title").textContent = "Edit employee";
    document.getElementById("emp-id").value = emp.id;
    document.getElementById("emp-name").value = emp.name;
    document.getElementById("emp-email").value = emp.email;
    document.getElementById("emp-phone").value = emp.phone;
    document.getElementById("emp-dept").value = emp.department;
    document.getElementById("emp-position").value = emp.position;
    document.getElementById("emp-join").value = emp.joinDate;
    document.getElementById("emp-basic").value = emp.basicSalary;
    document.getElementById("emp-allow").value = emp.allowances;
    document.getElementById("emp-deduct").value = emp.deductions;
    document.getElementById("emp-user").value = user ? user.username : "";
    document.getElementById("emp-pass").value = user ? user.password : "";
  }
  document.getElementById("employee-modal").classList.remove("hidden");
}

function closeEmployeeModal() {
  document.getElementById("employee-modal").classList.add("hidden");
}

function deleteEmployee(id) {
  const emp = Storage.getEmployee(id);
  if (!emp || !confirm("Delete " + emp.name + " and their login?")) return;
  Storage.saveEmployees(Storage.getEmployees().filter((e) => e.id !== id));
  Storage.saveUsers(Storage.getUsers().filter((u) => u.employeeId !== id));
  Storage.saveLeaves(Storage.getLeaves().filter((l) => l.employeeId !== id));
  Storage.savePayroll(Storage.getPayroll().filter((p) => p.employeeId !== id));
  renderAdmin();
  UI.toast("Employee removed.");
}

function setupLeaveFilter() {
  document.getElementById("leave-filter").addEventListener("change", (e) => renderLeaves(e.target.value));
}

function renderLeaves(status) {
  let leaves = Storage.getLeaves().slice().reverse();
  if (status) leaves = leaves.filter((l) => l.status === status);
  document.getElementById("leave-table").innerHTML = leaveTable(leaves, false);

  document.querySelectorAll("[data-approve]").forEach((btn) =>
    btn.addEventListener("click", () => setLeaveStatus(btn.dataset.approve, "approved"))
  );
  document.querySelectorAll("[data-reject]").forEach((btn) =>
    btn.addEventListener("click", () => setLeaveStatus(btn.dataset.reject, "rejected"))
  );
}

function leaveTable(leaves, compact) {
  if (!leaves.length) return `<p class="empty">No leave requests.</p>`;
  const employees = Storage.getEmployees();
  return table(
    ["Employee", "Type", "Dates", "Days", "Status", compact ? "" : "Actions"].filter(Boolean),
    leaves.map((l) => {
      const emp = employees.find((e) => e.id === l.employeeId);
      const actions =
        l.status === "pending"
          ? `<td class="row-actions">
              <button class="btn btn-ok btn-sm" data-approve="${l.id}">Approve</button>
              <button class="btn btn-danger btn-sm" data-reject="${l.id}">Reject</button>
            </td>`
          : `<td></td>`;
      return `<tr>
        <td>${emp ? escapeHtml(emp.name) : "Unknown"}<br><small class="muted">${escapeHtml(l.reason)}</small></td>
        <td>${escapeHtml(l.type)}</td>
        <td>${escapeHtml(l.from)} → ${escapeHtml(l.to)}</td>
        <td>${l.days}</td>
        <td>${UI.badge(l.status)}</td>
        ${compact ? "" : actions}
      </tr>`;
    })
  );
}

function setLeaveStatus(id, status) {
  const leaves = Storage.getLeaves();
  const item = leaves.find((l) => l.id === id);
  if (!item) return;
  item.status = status;
  Storage.saveLeaves(leaves);
  renderAdmin();
  UI.toast("Leave " + status + ".");
}

function setupPayroll() {
  const monthInput = document.getElementById("payroll-month");
  monthInput.value = new Date().toISOString().slice(0, 7);
  monthInput.addEventListener("change", renderPayroll);
  document.getElementById("generate-payroll").addEventListener("click", generatePayroll);
}

function generatePayroll() {
  const month = document.getElementById("payroll-month").value;
  if (!month) return;
  const existing = Storage.getPayroll().filter((p) => p.month !== month);
  const generated = Storage.getEmployees().map((emp) => calculatePayroll(emp, month));
  Storage.savePayroll(existing.concat(generated));
  renderPayroll();
  UI.toast("Payroll generated for " + month + ".");
}

function renderPayroll() {
  const month = document.getElementById("payroll-month").value;
  const employees = Storage.getEmployees();
  const rows = Storage.getPayroll().filter((p) => p.month === month);
  document.getElementById("payroll-table").innerHTML = rows.length
    ? table(
        ["Employee", "Basic", "Allowances", "Deductions", "Unpaid days", "Net pay", ""],
        rows.map((p) => {
          const emp = employees.find((e) => e.id === p.employeeId);
          return `<tr>
            <td>${emp ? escapeHtml(emp.name) : "Unknown"}</td>
            <td>${UI.money(p.basicSalary)}</td>
            <td>${UI.money(p.allowances)}</td>
            <td>${UI.money(p.deductions + p.leaveDeduction)}</td>
            <td>${p.unpaidDays}</td>
            <td><strong>${UI.money(p.netPay)}</strong></td>
            <td><button class="btn btn-ghost btn-sm" data-slip="${p.employeeId}">View</button></td>
          </tr>`;
        })
      )
    : `<p class="empty">No payroll yet for this month. Click Generate payroll.</p>`;

  document.querySelectorAll("[data-slip]").forEach((btn) =>
    btn.addEventListener("click", () => showAdminPayslip(btn.dataset.slip, month))
  );
}

function showAdminPayslip(employeeId, month) {
  const slip = Storage.getPayroll().find((p) => p.employeeId === employeeId && p.month === month);
  const emp = Storage.getEmployee(employeeId);
  if (!slip || !emp) return;
  const modal = document.getElementById("admin-payslip-modal");
  modal.innerHTML = `<div class="modal">
    <h3>Payslip — ${escapeHtml(emp.name)}</h3>
    <p class="muted">${escapeHtml(month)} · ${escapeHtml(emp.department)} · ${escapeHtml(emp.position)}</p>
    ${payslipBody(slip)}
    <div style="margin-top:14px;text-align:right;"><button class="btn btn-ghost" id="close-admin-slip">Close</button></div>
  </div>`;
  modal.classList.remove("hidden");
  document.getElementById("close-admin-slip").addEventListener("click", () => modal.classList.add("hidden"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
}

function payslipBody(slip) {
  return `<div class="payslip">
    <div class="payslip-row"><span>Basic salary</span><span>${UI.money(slip.basicSalary)}</span></div>
    <div class="payslip-row"><span>Allowances</span><span>${UI.money(slip.allowances)}</span></div>
    <div class="payslip-row"><span>Fixed deductions</span><span>- ${UI.money(slip.deductions)}</span></div>
    <div class="payslip-row"><span>Unpaid leave (${slip.unpaidDays} days)</span><span>- ${UI.money(slip.leaveDeduction)}</span></div>
    <div class="payslip-row total"><span>Net pay</span><span>${UI.money(slip.netPay)}</span></div>
  </div>`;
}

function table(headers, rowHtml) {
  if (!rowHtml.length) return `<p class="empty">Nothing to show.</p>`;
  return `<table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rowHtml.join("")}</tbody></table>`;
}

function val(id) {
  return document.getElementById(id).value.trim();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
