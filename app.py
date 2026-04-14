import os
import requests
from flask import Flask, request, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-please")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")

PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Lokaler LLM-Chat (Ollama)</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 1rem; }
    .chat-box { border: 1px solid #ccc; padding: 1rem; height: 60vh; overflow-y: auto; }
    .msg { margin-bottom: 0.75rem; }
    .user { font-weight: bold; color: #005; }
    .assistant { font-weight: bold; color: #050; }
    .bubble { margin-left: 0.5rem; white-space: pre-wrap; }
    form { margin-top: 1rem; display: flex; gap: 0.5rem; }
    textarea { flex: 1; height: 4rem; }
  </style>
</head>
<body>
  <h1>Chat mit lokalem LLM ({{ model }})</h1>

  <div class="chat-box">
    {% if messages %}
      {% for m in messages %}
        <div class="msg">
          {% if m.role == 'user' %}
            <span class="user">Du:</span>
          {% else %}
            <span class="assistant">LLM:</span>
          {% endif %}
          <span class="bubble">{{ m.content }}</span>
        </div>
      {% endfor %}
    {% else %}
      <p>Noch keine Nachrichten. Schreib einfach los 🙂</p>
    {% endif %}
  </div>

  <form method="post" action="{{ url_for('chat') }}">
    <textarea name="user_input" autofocus placeholder="Deine Nachricht..."></textarea>
    <button type="submit">Senden</button>
  </form>

  <form method="post" action="{{ url_for('reset_chat') }}">
    <button type="submit">Chat zurücksetzen</button>
  </form>
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
