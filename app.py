import os
import requests
from flask import Flask, request, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "splash123!")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")

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
      color: inherit;
    }
    .bubble-assistant {
      background: rgba(0, 135, 68, 0.12);
      color: inherit;
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

    /* Mobile-Optimierung */
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
      <div class="subtitle">Modell: {{ model }}</div>
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

        <form method="post" action="{{ url_for('reset_chat') }}">
          <button type="submit" class="btn-secondary">Chat zurücksetzen</button>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
"""

def call_ollama(messages):
    """Schickt den Chat-Verlauf an Ollama und gibt die Antwort zurück."""
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

def get_history():
    return session.get("history", [])

def save_history(history):
    session["history"] = history

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
    )

@app.route("/reset", methods=["POST"])
def reset_chat():
    save_history([])
    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
