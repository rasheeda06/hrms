/* ============================================================
   storage.js = the "backend"
   All app data is saved in the browser's localStorage.
   Nothing is sent to a server.
   ============================================================ */

const Storage = (() => {
  const KEYS = {
    USERS: "haven_hrms_users",
    EMPLOYEES: "haven_hrms_employees",
    LEAVES: "haven_hrms_leaves",
    PAYROLL: "haven_hrms_payroll",
    SESSION: "haven_hrms_session"
  };

  function read(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (err) {
      return fallback;
    }
  }

  function write(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function id(prefix) {
    return prefix + "_" + Date.now() + "_" + Math.floor(Math.random() * 1000);
  }

  /* First-time demo data so the app is not empty. */
  function ensureSeed() {
    if (localStorage.getItem(KEYS.USERS)) return;

    const employees = [
      {
        id: "emp_1001",
        name: "Emma Chen",
        email: "emma@havenhr.local",
        phone: "555-0101",
        department: "Design",
        position: "Product Designer",
        joinDate: "2024-03-12",
        basicSalary: 52000,
        allowances: 4000,
        deductions: 1200
      },
      {
        id: "emp_1002",
        name: "Raj Patel",
        email: "raj@havenhr.local",
        phone: "555-0102",
        department: "Engineering",
        position: "Frontend Developer",
        joinDate: "2023-11-08",
        basicSalary: 64000,
        allowances: 5000,
        deductions: 1600
      },
      {
        id: "emp_1003",
        name: "Sofia Alvarez",
        email: "sofia@havenhr.local",
        phone: "555-0103",
        department: "HR",
        position: "People Partner",
        joinDate: "2024-01-20",
        basicSalary: 48000,
        allowances: 2500,
        deductions: 900
      }
    ];

    const users = [
      { id: "usr_admin", username: "admin", password: "admin123", role: "admin", name: "Ava Brooks", employeeId: null },
      { id: "usr_1001", username: "emma", password: "emma123", role: "employee", name: "Emma Chen", employeeId: "emp_1001" },
      { id: "usr_1002", username: "raj", password: "raj123", role: "employee", name: "Raj Patel", employeeId: "emp_1002" },
      { id: "usr_1003", username: "sofia", password: "sofia123", role: "employee", name: "Sofia Alvarez", employeeId: "emp_1003" }
    ];

    const leaves = [
      {
        id: "lv_1",
        employeeId: "emp_1001",
        type: "Annual",
        from: "2026-08-20",
        to: "2026-08-22",
        days: 3,
        reason: "Family visit",
        status: "pending",
        createdAt: "2026-08-10"
      },
      {
        id: "lv_2",
        employeeId: "emp_1002",
        type: "Sick",
        from: "2026-07-03",
        to: "2026-07-03",
        days: 1,
        reason: "Fever",
        status: "approved",
        createdAt: "2026-07-03"
      }
    ];

    write(KEYS.EMPLOYEES, employees);
    write(KEYS.USERS, users);
    write(KEYS.LEAVES, leaves);
    write(KEYS.PAYROLL, []);
  }

  function resetDemo() {
    localStorage.removeItem(KEYS.USERS);
    localStorage.removeItem(KEYS.EMPLOYEES);
    localStorage.removeItem(KEYS.LEAVES);
    localStorage.removeItem(KEYS.PAYROLL);
    localStorage.removeItem(KEYS.SESSION);
    ensureSeed();
  }

  return {
    KEYS,
    id,
    ensureSeed,
    resetDemo,

    getUsers() {
      return read(KEYS.USERS, []);
    },
    saveUsers(list) {
      write(KEYS.USERS, list);
    },

    getEmployees() {
      return read(KEYS.EMPLOYEES, []);
    },
    saveEmployees(list) {
      write(KEYS.EMPLOYEES, list);
    },
    getEmployee(idValue) {
      return this.getEmployees().find((e) => e.id === idValue) || null;
    },

    getLeaves() {
      return read(KEYS.LEAVES, []);
    },
    saveLeaves(list) {
      write(KEYS.LEAVES, list);
    },

    getPayroll() {
      return read(KEYS.PAYROLL, []);
    },
    savePayroll(list) {
      write(KEYS.PAYROLL, list);
    },

    getSession() {
      return read(KEYS.SESSION, null);
    },
    setSession(session) {
      write(KEYS.SESSION, session);
    },
    clearSession() {
      localStorage.removeItem(KEYS.SESSION);
    }
  };
})();
