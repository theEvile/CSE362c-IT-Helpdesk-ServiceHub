/* Explicit UI state; safe rendering through textContent, not HTML strings. */
const articleList = document.getElementById("articles");
const articleStatus = document.getElementById("articles-status");
const searchInput = document.getElementById("search");
const categoryInput = document.getElementById("article-category");
const ticketForm = document.getElementById("ticket-form");
const ticketStatus = document.getElementById("ticket-status");
const state = { articles: [], query: "", category: "" };

function renderArticles() {
  articleList.replaceChildren();
  for (const article of state.articles) {
    const item = document.createElement("li");
    const title = document.createElement("h3");
    const details = document.createElement("p");
    const category = document.createElement("small");
    title.textContent = article.title;
    details.textContent = article.body;
    category.textContent = article.category;
    item.append(title, category, details);
    articleList.append(item);
  }
  articleStatus.textContent = state.articles.length
    ? state.articles.length + " article(s) found."
    : "No matching articles. Try a different search.";
}

let lastSearch = 0;
async function loadArticles() {
  const serial = ++lastSearch;
  const params = new URLSearchParams();
  if (state.query) params.set("q", state.query);
  if (state.category) params.set("category", state.category);
  articleStatus.textContent = "Loading articles…";
  try {
    const response = await fetch("/api/articles?" + params.toString());
    if (!response.ok) throw new Error("Article request failed");
    const data = await response.json();
    if (serial !== lastSearch) return;
    state.articles = data.articles;
    renderArticles();
  } catch (_error) {
    if (serial === lastSearch)
      articleStatus.textContent = "Could not load articles. Check the connection and retry.";
  }
}
searchInput.addEventListener("input", () => {
  state.query = searchInput.value.trim();
  loadArticles();
});
categoryInput.addEventListener("change", () => {
  state.category = categoryInput.value;
  loadArticles();
});
ticketForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!ticketForm.reportValidity()) return;
  const payload = Object.fromEntries(new FormData(ticketForm).entries());
  ticketStatus.textContent = "Submitting…";
  try {
    const response = await fetch("/api/tickets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      ticketStatus.textContent = data.error || "Could not submit ticket.";
      return;
    }
    ticketStatus.textContent = "Ticket #" + data.ticket.id + " submitted successfully.";
    ticketForm.reset();
  } catch (_error) {
    ticketStatus.textContent = "Network error. Please retry.";
  }
});
loadArticles();
