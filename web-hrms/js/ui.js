/* ============================================================
   ui.js = small helpers used on every page
   ============================================================ */

const UI = {
  money(amount) {
    const n = Number(amount) || 0;
    return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
  },

  daysBetween(from, to) {
    const start = new Date(from);
    const end = new Date(to);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
    const diff = Math.floor((end - start) / 86400000) + 1;
    return diff > 0 ? diff : 0;
  },

  initials(name) {
    return String(name || "?")
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0].toUpperCase())
      .join("");
  },

  toast(message) {
    const old = document.querySelector(".toast");
    if (old) old.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2400);
  },

  badge(status) {
    const safe = String(status || "pending").toLowerCase();
    return `<span class="badge badge-${safe}">${safe}</span>`;
  },

  fillSelect(select, employees, includeAll) {
    const options = includeAll ? `<option value="">All employees</option>` : "";
    select.innerHTML =
      options +
      employees
        .map((e) => `<option value="${e.id}">${e.name} — ${e.department}</option>`)
        .join("");
  }
};

function unpaidLeaveDays(employeeId, yearMonth) {
  const [year, month] = yearMonth.split("-").map(Number);
  const start = new Date(year, month - 1, 1);
  const end = new Date(year, month, 0);

  return Storage.getLeaves()
    .filter((l) => l.employeeId === employeeId && l.status === "approved" && l.type === "Unpaid")
    .reduce((total, leave) => {
      const from = new Date(leave.from);
      const to = new Date(leave.to);
      const overlapStart = from > start ? from : start;
      const overlapEnd = to < end ? to : end;
      if (overlapEnd < overlapStart) return total;
      return total + (Math.floor((overlapEnd - overlapStart) / 86400000) + 1);
    }, 0);
}

/* Simple payroll formula (easy to explain):
   per-day pay = basic salary / 30
   leave deduction = per-day pay * unpaid leave days in that month
   net pay = basic + allowances - fixed deductions - leave deduction
*/
function calculatePayroll(employee, yearMonth) {
  const unpaidDays = unpaidLeaveDays(employee.id, yearMonth);
  const perDay = Number(employee.basicSalary) / 30;
  const leaveDeduction = Math.round(perDay * unpaidDays * 100) / 100;
  const basic = Number(employee.basicSalary) || 0;
  const allowances = Number(employee.allowances) || 0;
  const deductions = Number(employee.deductions) || 0;
  const net = Math.round((basic + allowances - deductions - leaveDeduction) * 100) / 100;

  return {
    employeeId: employee.id,
    month: yearMonth,
    basicSalary: basic,
    allowances,
    deductions,
    unpaidDays,
    leaveDeduction,
    netPay: net,
    generatedAt: new Date().toISOString().slice(0, 10)
  };
}

const LEAVE_LIMITS = { Annual: 12, Sick: 7, Casual: 5, Unpaid: 365 };

function usedLeaveDays(employeeId, type) {
  return Storage.getLeaves()
    .filter((l) => l.employeeId === employeeId && l.type === type && l.status !== "rejected")
    .reduce((sum, l) => sum + Number(l.days || 0), 0);
}
