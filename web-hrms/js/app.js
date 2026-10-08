/* ============================================================
   app.js = starts the right screen after the page loads
   ============================================================ */

Storage.ensureSeed();

const session = Auth.current();
document.getElementById("screen-login").classList.add("hidden");
document.getElementById("screen-admin").classList.add("hidden");
document.getElementById("screen-employee").classList.add("hidden");

if (!session) {
  document.getElementById("screen-login").classList.remove("hidden");
  bootLogin();
} else if (session.role === "admin") {
  document.getElementById("screen-admin").classList.remove("hidden");
  bootAdmin(session);
} else {
  document.getElementById("screen-employee").classList.remove("hidden");
  bootEmployee(session);
}
