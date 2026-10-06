import { useEffect, useState } from "react";

const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/+$/, "");
const API = `${API_URL}/todos`;

export default function App() {
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  async function request(url, options) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) throw new Error(`Lỗi ${res.status}`);
    return res.status === 204 ? null : res.json();
  }

  async function load() {
    try {
      setError("");
      setTodos(await request(API));
    } catch (e) {
      setError("Không tải được dữ liệu. Backend đã chạy chưa? (" + e.message + ")");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function addTodo(e) {
    e.preventDefault();
    const text = title.trim();
    if (!text) return;
    try {
      const created = await request(API, {
        method: "POST",
        body: JSON.stringify({ title: text }),
      });
      setTodos((list) => [created, ...list]);
      setTitle("");
    } catch (e) {
      setError(e.message);
    }
  }

  async function update(id, changes) {
    try {
      const updated = await request(`${API}/${id}`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      setTodos((list) => list.map((t) => (t.id === id ? updated : t)));
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }

  function toggle(todo) {
    update(todo.id, { done: !todo.done });
  }

  function startEdit(todo) {
    setEditingId(todo.id);
    setEditText(todo.title);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditText("");
  }

  async function saveEdit(todo) {
    const text = editText.trim();
    if (!text) return;
    if (text === todo.title || (await update(todo.id, { title: text }))) {
      cancelEdit();
    }
  }

  async function remove(id) {
    try {
      await request(`${API}/${id}`, { method: "DELETE" });
      setTodos((list) => list.filter((t) => t.id !== id));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <main className="container">
      <h1>Todo App</h1>
      <p className="sub">React + FastAPI + MySQL</p>

      <form onSubmit={addTodo} className="form">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Nhập việc cần làm..."
          maxLength={255}
        />
        <button type="submit">Thêm</button>
      </form>

      {error && <div className="error">{error}</div>}
      {loading && <p>Đang tải...</p>}

      <ul className="list">
        {todos.map((t) => (
          <li key={t.id} className={t.done ? "done" : ""}>
            {editingId === t.id ? (
              <form
                className="edit"
                onSubmit={(e) => {
                  e.preventDefault();
                  saveEdit(t);
                }}
              >
                <input
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onKeyDown={(e) => e.key === "Escape" && cancelEdit()}
                  maxLength={255}
                  autoFocus
                />
                <button type="submit">Lưu</button>
                <button type="button" className="secondary" onClick={cancelEdit}>
                  Hủy
                </button>
              </form>
            ) : (
              <>
                <label>
                  <input type="checkbox" checked={t.done} onChange={() => toggle(t)} />
                  <span onDoubleClick={() => startEdit(t)}>{t.title}</span>
                </label>
                <div className="actions">
                  <button className={t.done ? "secondary" : "ok"} onClick={() => toggle(t)}>
                    {t.done ? "Bỏ done" : "Done"}
                  </button>
                  <button className="secondary" onClick={() => startEdit(t)}>
                    Sửa
                  </button>
                  <button className="del" onClick={() => remove(t.id)}>
                    Xóa
                  </button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>

      {!loading && todos.length === 0 && !error && <p>Chưa có việc nào.</p>}
    </main>
  );
}
