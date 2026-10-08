/* ============================================================
   auth.js = login, logout, and who is signed in
   Passwords are stored in localStorage for learning only.
   Never do that in a real production app.
   ============================================================ */

const Auth = {
  login(username, password) {
    Storage.ensureSeed();
    const name = String(username || "").trim().toLowerCase();
    const pass = String(password || "");
    const user = Storage.getUsers().find(
      (u) => u.username.toLowerCase() === name && u.password === pass
    );

    if (!user) {
      return { ok: false, message: "Invalid username or password." };
    }

    Storage.setSession({
      userId: user.id,
      username: user.username,
      name: user.name,
      role: user.role,
      employeeId: user.employeeId || null
    });

    return { ok: true, user };
  },

  logout() {
    Storage.clearSession();
    window.location.reload();
  },

  current() {
    Storage.ensureSeed();
    return Storage.getSession();
  }
};
