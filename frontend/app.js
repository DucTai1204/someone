// URL API mà trình duyệt gọi. Mặc định /api (đi qua nginx proxy sang backend).
// Muốn gọi thẳng backend thì đặt window.API_URL trước khi nạp file này.
const API_URL = (window.API_URL || "/api").replace(/\/+$/, "");
const API = `${API_URL}/todos`;

let todos = [];
let loading = true;
let editingId = null;

const $ = (id) => document.getElementById(id);
const listEl = $("list");
const errorEl = $("error");
const addForm = $("add-form");
const addInput = $("add-input");

async function request(url, options) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`Lỗi ${res.status}`);
  return res.status === 204 ? null : res.json();
}

function setError(msg) {
  errorEl.textContent = msg;
  errorEl.hidden = !msg;
}

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  for (const c of children) node.append(c);
  return node;
}

function render() {
  $("loading").hidden = !loading;
  $("empty").hidden = loading || todos.length > 0 || !errorEl.hidden;

  let editInput = null;
  listEl.replaceChildren(
    ...todos.map((t) => {
      const li = el("li", { className: t.done ? "done" : "" });

      if (editingId === t.id) {
        const input = el("input", { value: t.title, maxLength: 255 });
        input.addEventListener("keydown", (e) => e.key === "Escape" && cancelEdit());
        const form = el("form", { className: "edit" }, [
          input,
          el("button", { type: "submit", textContent: "Lưu" }),
          el("button", {
            type: "button",
            className: "secondary",
            textContent: "Hủy",
            onclick: cancelEdit,
          }),
        ]);
        form.addEventListener("submit", (e) => {
          e.preventDefault();
          saveEdit(t, input.value);
        });
        li.append(form);
        editInput = input;
        return li;
      }

      const checkbox = el("input", { type: "checkbox", checked: t.done, onchange: () => toggle(t) });
      const span = el("span", { textContent: t.title, ondblclick: () => startEdit(t) });
      li.append(
        el("label", {}, [checkbox, span]),
        el("div", { className: "actions" }, [
          el("button", {
            className: t.done ? "secondary" : "ok",
            textContent: t.done ? "Bỏ done" : "Done",
            onclick: () => toggle(t),
          }),
          el("button", { className: "secondary", textContent: "Sửa", onclick: () => startEdit(t) }),
          el("button", { className: "del", textContent: "Xóa", onclick: () => remove(t.id) }),
        ])
      );
      return li;
    })
  );
  if (editInput) editInput.focus();
}

async function load() {
  try {
    setError("");
    todos = await request(API);
  } catch (e) {
    setError("Không tải được dữ liệu. Backend đã chạy chưa? (" + e.message + ")");
  } finally {
    loading = false;
    render();
  }
}

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = addInput.value.trim();
  if (!text) return;
  try {
    const created = await request(API, {
      method: "POST",
      body: JSON.stringify({ title: text }),
    });
    todos = [created, ...todos];
    addInput.value = "";
    render();
  } catch (e) {
    setError(e.message);
  }
});

async function update(id, changes) {
  try {
    const updated = await request(`${API}/${id}`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    });
    todos = todos.map((t) => (t.id === id ? updated : t));
    render();
    return true;
  } catch (e) {
    setError(e.message);
    render();
    return false;
  }
}

function toggle(todo) {
  update(todo.id, { done: !todo.done });
}

function startEdit(todo) {
  editingId = todo.id;
  render();
}

function cancelEdit() {
  editingId = null;
  render();
}

async function saveEdit(todo, value) {
  const text = value.trim();
  if (!text) return;
  if (text === todo.title || (await update(todo.id, { title: text }))) {
    cancelEdit();
  }
}

async function remove(id) {
  try {
    await request(`${API}/${id}`, { method: "DELETE" });
    todos = todos.filter((t) => t.id !== id);
    render();
  } catch (e) {
    setError(e.message);
  }
}

render();
load();
