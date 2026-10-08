/* ============================================================
   login.js = Admin / Employee sign-in form
   ============================================================ */

function bootLogin() {
  const form = document.getElementById("login-form");
  const errorEl = document.getElementById("login-error");
  const copyEl = document.getElementById("login-copy");
  const userInput = document.getElementById("username");
  const tabs = document.querySelectorAll(".role-tabs button");
  let expectedRole = "admin";

  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      expectedRole = btn.dataset.role;
      copyEl.textContent =
        expectedRole === "admin"
          ? "Use the admin account to manage the whole team."
          : "Employees can view profile, apply for leave, and see payslips.";
      userInput.focus();
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    errorEl.textContent = "";

    const result = Auth.login(form.username.value, form.password.value);
    if (!result.ok) {
      errorEl.textContent = result.message;
      return;
    }

    if (result.user.role !== expectedRole) {
      Storage.clearSession();
      errorEl.textContent =
        expectedRole === "admin"
          ? "That account is an employee login. Switch to the Employee tab."
          : "That account is an admin login. Switch to the Admin tab.";
      return;
    }

    window.location.reload();
  });
}
