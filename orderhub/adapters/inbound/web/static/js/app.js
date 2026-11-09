// OrderHub · utilidades compartidas: sesión, llamadas a la API y helpers de interfaz.
// Todo el contenido dinámico se pinta con textContent (nunca innerHTML con datos)
// para evitar XSS, por ejemplo con nombres de producto maliciosos.
const OrderHub = (() => {
  const KEY = "orderhub.session";

  const session = {
    get() {
      try { return JSON.parse(sessionStorage.getItem(KEY)); } catch { return null; }
    },
    set(data) { sessionStorage.setItem(KEY, JSON.stringify(data)); },
    clear() { sessionStorage.removeItem(KEY); },
  };

  // Llama a la API con el token de la sesión. Ante un 401, la sesión expiró:
  // se limpia y se vuelve al login.
  async function api(method, path, body) {
    const headers = {};
    const s = session.get();
    if (s && s.token) headers["Authorization"] = "Bearer " + s.token;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    const data = await res.json().catch(() => null);
    if (res.status === 401 && s) {
      session.clear();
      location.href = "/login?expirada=1";
    }
    return { ok: res.ok, status: res.status, data };
  }

  function errorMessage(data, fallback) {
    return (data && (data.message || data.error)) || fallback;
  }

  // Protege una página: exige sesión (y rol admin si se pide). Pinta la barra superior.
  function requireSession(options = {}) {
    const s = session.get();
    if (!s || !s.token) { location.href = "/login"; return null; }
    if (options.admin && s.user.role !== "admin") { location.href = "/catalogo"; return null; }
    renderTopbar(s.user);
    return s;
  }

  function renderTopbar(user) {
    const name = document.querySelector("[data-user-name]");
    const avatar = document.querySelector("[data-user-avatar]");
    const role = document.querySelector("[data-user-role]");
    if (name) name.textContent = user.username;
    if (avatar) avatar.textContent = user.username.slice(0, 1);
    if (role) {
      role.textContent = user.role === "admin" ? "Admin" : "Cliente";
      role.className = "badge " + (user.role === "admin" ? "badge-navy" : "badge-green");
    }
    document.querySelectorAll("[data-admin-only]").forEach((el) => {
      el.hidden = user.role !== "admin";
    });
    document.querySelectorAll(".nav a").forEach((a) => {
      if (a.getAttribute("href") === location.pathname) a.classList.add("active");
    });
    const logout = document.querySelector("[data-logout]");
    if (logout) logout.addEventListener("click", () => { session.clear(); location.href = "/login"; });
  }

  function showAlert(el, text, kind = "error") {
    el.textContent = text;
    el.className = "alert alert-" + kind + " show";
  }

  let toastTimer;
  function toast(text, isError = false) {
    let el = document.querySelector(".toast");
    if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
    el.textContent = text;
    el.classList.toggle("error", isError);
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
  }

  const money = new Intl.NumberFormat("es-CO", { style: "currency", currency: "USD", minimumFractionDigits: 2 });
  function formatMoney(value) { return money.format(value); }

  // Crea un elemento con clase y texto de forma segura.
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function stockBadge(stock) {
    if (stock <= 0) return el("span", "badge badge-red", "Agotado");
    if (stock <= 5) return el("span", "badge badge-amber", stock + " disponibles");
    return el("span", "badge badge-green", stock + " disponibles");
  }

  return { session, api, errorMessage, requireSession, showAlert, toast, formatMoney, el, stockBadge };
})();
