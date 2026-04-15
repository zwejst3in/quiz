import os
import json
import pathlib
import requests
from flask import (
    Flask,
    request,
    render_template_string,
    session,
    redirect,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-please")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")

BASE_DIR = pathlib.Path(__file__).resolve().parent
CHAT_DIR = pathlib.Path(os.getenv("CHAT_DIR", BASE_DIR / "chats"))
CHAT_DIR.mkdir(parents=True, exist_ok=True)

PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Lokaler LLM-Chat (Ollama)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f5f5f5;
      --bg-dark: #111;
      --card: #ffffff;
      --card-dark: #1e1e1e;
      --border: #ccc;
      --border-dark: #333;
      --user: #0055aa;
      --assistant: #008744;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
    }
    @media (prefers-color-scheme: dark) {
      body { background: var(--bg-dark); color: #f5f5f5; }
    }
    .page {
      max-width: 900px;
      margin: 0 auto;
      padding: 0.75rem;
    }
    header {
      padding: 0.5rem 0 0.75rem;
    }
    h1 {
      font-size: 1.2rem;
      margin: 0;
    }
    .subtitle {
      font-size: 0.8rem;
      opacity: 0.8;
    }
    .card {
      background: var(--card);
      border-radius: 0.75rem;
      border: 1px solid var(--border);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      height: calc(100vh - 7rem);
      max-height: 900px;
    }
    @media (prefers-color-scheme: dark) {
      .card {
        background: var(--card-dark);
        border-color: var(--border-dark);
      }
    }
    .chat-box {
      flex: 1;
      overflow-y: auto;
      padding-right: 0.25rem;
      margin-bottom: 0.5rem;
    }
    .msg {
      margin-bottom: 0.5rem;
      display: flex;
      flex-direction: column;
    }
    .msg-user { align-items: flex-end; }
    .msg-assistant { align-items: flex-start; }

    .label {
      font-size: 0.7rem;
      opacity: 0.8;
      margin-bottom: 0.15rem;
    }
    .label-user { color: var(--user); }
    .label-assistant { color: var(--assistant); }

    .bubble {
      max-width: 100%;
      padding: 0.4rem 0.6rem;
      border-radius: 0.8rem;
      font-size: 0.9rem;
      line-height: 1.4;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .bubble-user {
      background: rgba(0, 85, 170, 0.1);
    }
    .bubble-assistant {
      background: rgba(0, 135, 68, 0.12);
    }

    .forms {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      margin-top: 0.25rem;
    }
    .input-row {
      display: flex;
      gap: 0.35rem;
    }
    textarea {
      flex: 1;
      min-height: 3rem;
      max-height: 8rem;
      resize: vertical;
      padding: 0.4rem 0.5rem;
      font-size: 0.95rem;
      border-radius: 0.6rem;
      border: 1px solid var(--border);
      font-family: inherit;
    }
    @media (prefers-color-scheme: dark) {
      textarea {
        background: #121212;
        color: #f5f5f5;
        border-color: var(--border-dark);
      }
    }
    button {
      border-radius: 0.6rem;
      border: none;
      padding: 0.45rem 0.9rem;
      font-size: 0.9rem;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
    }
    .btn-primary {
      background: #007bff;
      color: #fff;
    }
    .btn-secondary {
      background: #e0e0e0;
    }
    @media (prefers-color-scheme: dark) {
      .btn-secondary {
        background: #333;
        color: #f5f5f5;
      }
    }

    .save-load-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      align-items: center;
      font-size: 0.8rem;
    }
    .save-load-row input[type="text"],
    .save-load-row select {
      font-size: 0.8rem;
      padding: 0.25rem 0.4rem;
      border-radius: 0.4rem;
      border: 1px solid var(--border);
      background: inherit;
      color: inherit;
    }
    @media (prefers-color-scheme: dark) {
      .save-load-row input[type="text"],
      .save-load-row select {
        border-color: var(--border-dark);
      }
    }

    @media (max-width: 600px) {
      .page { padding: 0.5rem; }
      .card { height: calc(100vh - 5.5rem); }
      h1 { font-size: 1rem; }
      .subtitle { font-size: 0.7rem; }
      .bubble { font-size: 0.85rem; }
      textarea { font-size: 0.9rem; }
      button { font-size: 0.85rem; padding: 0.4rem 0.75rem; }
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>Chat mit lokalem LLM</h1>
      <div class="subtitle">
        Modell: {{ model }}{% if current_chat %} &middot; Chat: {{ current_chat }}{% endif %}
      </div>
    </header>

    <div class="card">
      <div class="chat-box">
        {% if messages %}
          {% for m in messages %}
            <div class="msg {% if m.role == 'user' %}msg-user{% else %}msg-assistant{% endif %}">
              <div class="label {% if m.role == 'user' %}label-user{% else %}label-assistant{% endif %}">
                {% if m.role == 'user' %}Du{% else %}LLM{% endif %}
              </div>
              <div class="bubble {% if m.role == 'user' %}bubble-user{% else %}bubble-assistant{% endif %}">
                {{ m.content }}
              </div>
            </div>
          {% endfor %}
        {% else %}
          <p>Noch keine Nachrichten. Schreib einfach los 🙂</p>
        {% endif %}
      </div>

      <div class="forms">
        <form method="post" action="{{ url_for('chat') }}" class="input-row">
          <textarea name="user_input" autofocus placeholder="Deine Nachricht..."></textarea>
          <button type="submit" class="btn-primary">Senden</button>
        </form>

        <div class="save-load-row">
          <form method="post" action="{{ url_for('save_chat_route') }}">
            <input type="text" name="chat_name" placeholder="Chat-Namen zum Speichern" required>
            <button type="submit" class="btn-secondary">Speichern</button>
          </form>

          <form method="post" action="{{ url_for('load_chat_route') }}">
            <select name="chat_name">
              <option value="">Chat laden...</option>
              {% for c in saved_chats %}
                <option value="{{ c }}" {% if c == current_chat %}selected{% endif %}>{{ c }}</option>
              {% endfor %}
            </select>
            <button type="submit" class="btn-secondary">Laden</button>
          </form>

          <form method="post" action="{{ url_for('reset_chat') }}">
            <button type="submit" class="btn-secondary">Neu (leer)</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

# ---------- Persistenz-Funktionen ----------

def safe_name(name: str) -> str:
    """Einfache 'Slug'-Funktion für Dateinamen."""
    name = name.strip()
    if not name:
        return "chat"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    cleaned = "".join(ch if ch in allowed else "_" for ch in name)
    return cleaned or "chat"

def chat_path(chat_name: str) -> pathlib.Path:
    return CHAT_DIR / f"{safe_name(chat_name)}.json"

def list_saved_chats():
    chats = []
    for p in CHAT_DIR.glob("*.json"):
        chats.append(p.stem)
    chats.sort()
    return chats

def save_chat_to_disk(chat_name: str, history):
    path = chat_path(chat_name)
    data = {
        "model": OLLAMA_MODEL,
        "history": history,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat_from_disk(chat_name: str):
    path = chat_path(chat_name)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Nur history nutzen; Modell kann sich geändert haben
    return data.get("history", [])

# ---------- Session-Helfer ----------

def get_history():
    return session.get("history", [])

def save_history(history):
    session["history"] = history

def get_current_chat_name():
    return session.get("current_chat_name", "")

def set_current_chat_name(name: str):
    session["current_chat_name"] = name

# ---------- Ollama-Aufruf ----------

def call_ollama(messages):
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]

# ---------- Routes ----------

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("chat"))

@app.route("/chat", methods=["GET", "POST"])
def chat():
    history = get_history()

    if request.method == "POST":
        user_input = (request.form.get("user_input") or "").strip()
        if user_input:
            history.append({"role": "user", "content": user_input})
            try:
                assistant_reply = call_ollama(history)
            except Exception as e:
                assistant_reply = f"[Fehler beim Aufruf von Ollama: {e}]"
            history.append({"role": "assistant", "content": assistant_reply})
            save_history(history)

    return render_template_string(
        PAGE,
        messages=history,
        model=OLLAMA_MODEL,
        saved_chats=list_saved_chats(),
        current_chat=get_current_chat_name(),
    )

@app.route("/reset", methods=["POST"])
def reset_chat():
    save_history([])
    set_current_chat_name("")
    return redirect(url_for("chat"))

@app.route("/save", methods=["POST"])
def save_chat_route():
    chat_name = (request.form.get("chat_name") or "").strip()
    if not chat_name:
        return redirect(url_for("chat"))
    history = get_history()
    save_chat_to_disk(chat_name, history)
    set_current_chat_name(safe_name(chat_name))
    return redirect(url_for("chat"))

@app.route("/load", methods=["POST"])
def load_chat_route():
    chat_name = (request.form.get("chat_name") or "").strip()
    if not chat_name:
        return redirect(url_for("chat"))
    loaded = load_chat_from_disk(chat_name)
    if loaded is not None:
        save_history(loaded)
        set_current_chat_name(chat_name)
    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
