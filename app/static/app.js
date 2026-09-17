const state = { todos: [], filter: "all" };
const filterTitles = { all: "Everything", open: "To do", done: "Finished" };

const elements = {
  form: document.querySelector("#add-form"), input: document.querySelector("#new-todo"),
  list: document.querySelector("#todo-list"), open: document.querySelector("#open-count"),
  done: document.querySelector("#done-count"), total: document.querySelector("#total-count"),
  clear: document.querySelector("#clear-completed"), hint: document.querySelector("#saved-hint"),
  heading: document.querySelector("#filter-heading"), progress: document.querySelector("#progress-value"),
  bar: document.querySelector("#progress-bar"), progressCopy: document.querySelector("#progress-copy"),
};

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error("That change could not be saved. Please try again.");
  return response.status === 204 ? null : response.json();
}

function render() {
  const { todos, filter } = state;
  const open = todos.filter((todo) => !todo.completed).length;
  const done = todos.length - open;
  const progress = todos.length ? Math.round((done / todos.length) * 100) : 0;
  const visible = filter === "open" ? todos.filter((todo) => !todo.completed) : filter === "done" ? todos.filter((todo) => todo.completed) : todos;
  elements.open.textContent = `${open} ${open === 1 ? "open" : "open"}`;
  elements.done.textContent = done;
  elements.done.hidden = done === 0;
  elements.total.textContent = todos.length ? `${todos.length} ${todos.length === 1 ? "task" : "tasks"} in your list` : "Start small.";
  elements.clear.hidden = done === 0;
  elements.hint.hidden = done > 0;
  elements.heading.textContent = filterTitles[filter];
  elements.progress.textContent = `${progress}%`;
  elements.bar.style.width = `${progress}%`;
  elements.bar.parentElement.setAttribute("aria-label", `${progress}% complete`);
  elements.progressCopy.textContent = todos.length === 0 ? "A fresh little list." : done === todos.length ? "All clear. Nice work." : `${open} ${open === 1 ? "thing" : "things"} still in front of you.`;
  document.querySelectorAll(".filter-button").forEach((button) => {
    const active = button.dataset.filter === filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  if (!visible.length) {
    elements.list.innerHTML = `<div class="empty-state"><span>✓</span><p>${filter === "done" ? "Nothing finished just yet." : "You're all caught up."}</p><small>${filter === "done" ? "The good stuff will show up here." : "Enjoy the extra breathing room."}</small></div>`;
    return;
  }
  elements.list.innerHTML = visible.map((todo, index) => `
    <article class="todo-row ${todo.completed ? "is-complete" : ""}" style="animation-delay:${index * 35}ms">
      <button type="button" class="check-button" data-action="toggle" data-id="${todo.id}" aria-label="${todo.completed ? "Mark as not done" : "Mark as done"}">${todo.completed ? "✓" : "○"}</button>
      <span class="todo-title">${escapeHtml(todo.title)}</span>
      <button type="button" class="delete-button" data-action="delete" data-id="${todo.id}" aria-label="Delete ${escapeHtml(todo.title)}">⌫</button>
    </article>`).join("");
}

function escapeHtml(value) { const node = document.createElement("span"); node.textContent = value; return node.innerHTML; }
function showError(message) { elements.hint.textContent = message; elements.hint.hidden = false; }

async function refresh() { state.todos = await api("/api/todos"); render(); }

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault(); const title = elements.input.value.trim(); if (!title) return;
  try { const todo = await api("/api/todos", { method: "POST", body: JSON.stringify({ title }) }); state.todos.unshift(todo); elements.input.value = ""; render(); }
  catch (error) { showError(error.message); }
});
elements.list.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]"); if (!button) return;
  const todo = state.todos.find((item) => item.id === Number(button.dataset.id)); if (!todo) return;
  try { if (button.dataset.action === "toggle") Object.assign(todo, await api(`/api/todos/${todo.id}`, { method: "PATCH", body: JSON.stringify({ completed: !todo.completed }) })); else { await api(`/api/todos/${todo.id}`, { method: "DELETE" }); state.todos = state.todos.filter((item) => item.id !== todo.id); } render(); }
  catch (error) { showError(error.message); }
});
document.querySelector(".filters").addEventListener("click", (event) => { const button = event.target.closest("button[data-filter]"); if (button) { state.filter = button.dataset.filter; render(); } });
elements.clear.addEventListener("click", async () => { try { await api("/api/todos", { method: "DELETE" }); state.todos = state.todos.filter((todo) => !todo.completed); state.filter = "all"; render(); } catch (error) { showError(error.message); } });
document.querySelector("#today").textContent = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric" }).format(new Date());
refresh().catch((error) => showError(error.message));
