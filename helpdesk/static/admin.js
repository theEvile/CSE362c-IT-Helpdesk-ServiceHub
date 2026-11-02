/* Authenticated ticket operations. All untrusted text uses textContent. */
const loginPanel = document.getElementById("login-section");
const ticketsPanel = document.getElementById("tickets-section");
const loginForm = document.getElementById("login-form");
const ticketsList = document.getElementById("tickets");
const message = document.getElementById("admin-status");
const nameText = document.getElementById("admin-name");
const filter = document.getElementById("status-filter");
const logoutButton = document.getElementById("logout");
const state = { csrf: "", username: "", authenticated: false, tickets: [] };

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}
function view(loggedIn) {
  loginPanel.hidden = loggedIn;
  ticketsPanel.hidden = !loggedIn;
  nameText.textContent = loggedIn ? "Signed in as " + state.username : "";
  if (!loggedIn) ticketsList.replaceChildren();
}
function txt(parent, tag, value) {
  const node = document.createElement(tag);
  node.textContent = value;
  parent.append(node);
  return node;
}
function renderTickets() {
  ticketsList.replaceChildren();
  const allStatuses = ["OPEN", "IN_PROGRESS", "RESOLVED"];
  for (const ticket of state.tickets) {
    const card = document.createElement("li");
    txt(card, "h3", "#" + ticket.id + ": " + ticket.title);
    txt(card, "small", ticket.category + " · " + ticket.status);
    txt(card, "p", ticket.description);
    txt(card, "p", "Contact: " + ticket.contact_email);
    const controls = document.createElement("div");
    controls.className = "ticket-controls";
    const dropdown = document.createElement("select");
    dropdown.setAttribute("aria-label", "Status for ticket #" + ticket.id);
    for (const status of allStatuses) {
      const option = document.createElement("option");
      option.value = status;
      option.textContent = status.replace("_", " ");
      option.selected = status === ticket.status;
      option.disabled = allStatuses.indexOf(status) < allStatuses.indexOf(ticket.status);
      dropdown.append(option);
    }
    dropdown.disabled = ticket.status === "RESOLVED";
    const save = txt(controls, "button", "Save status");
    save.type = "button";
    save.disabled = ticket.status === "RESOLVED";
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        await api("/api/tickets/" + ticket.id, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
          body: JSON.stringify({ status: dropdown.value })
        });
        await loadTickets();
        message.textContent = "Ticket #" + ticket.id + " updated.";
      } catch (error) {
        message.textContent = error.message;
        save.disabled = false;
      }
    });
    controls.prepend(dropdown);
    if (ticket.status === "RESOLVED") {
      const remove = txt(controls, "button", "Delete resolved ticket");
      remove.type = "button";
      remove.className = "danger-button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Permanently delete ticket #" + ticket.id + "?")) return;
        remove.disabled = true;
        try {
          await api("/api/tickets/" + ticket.id, {
            method: "DELETE",
            headers: { "X-CSRF-Token": state.csrf }
          });
          await loadTickets();
          message.textContent = "Ticket #" + ticket.id + " deleted.";
        } catch (error) {
          message.textContent = error.message;
          remove.disabled = false;
        }
      });
    }
    card.append(controls);
    ticketsList.append(card);
  }
  if (!state.tickets.length) txt(ticketsList, "li", "No matching tickets.");
}
async function loadTickets() {
  const params = new URLSearchParams();
  if (filter.value) params.set("status", filter.value);
  const result = await api("/api/tickets?" + params.toString());
  state.tickets = result.tickets;
  renderTickets();
  message.textContent = result.tickets.length + " ticket(s) loaded.";
}
async function refreshSession() {
  const data = await api("/api/admin/session");
  state.csrf = data.csrf_token;
  state.username = data.username || "";
  state.authenticated = data.authenticated;
  view(data.authenticated);
  if (data.authenticated) await loadTickets();
  else message.textContent = "Sign in to review student tickets.";
}
loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Signing in…";
  try {
    const result = await api("/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
      body: JSON.stringify(Object.fromEntries(new FormData(loginForm).entries()))
    });
    state.csrf = result.csrf_token;
    state.username = result.username;
    state.authenticated = true;
    loginForm.reset();
    view(true);
    await loadTickets();
  } catch (error) { message.textContent = error.message; }
});
filter.addEventListener("change", () => {
  loadTickets().catch(error => { message.textContent = error.message; });
});
logoutButton.addEventListener("click", async () => {
  try {
    await api("/api/admin/logout", {
      method: "POST", headers: { "X-CSRF-Token": state.csrf }
    });
    await refreshSession();
  } catch (error) { message.textContent = error.message; }
});
refreshSession().catch(error => { view(false); message.textContent = error.message; });
