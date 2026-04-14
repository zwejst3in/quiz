# Local LLM Chat (Ollama)

Einfache Web-Chat-Oberfläche für ein lokales LLM über die Ollama-API.
Getestet mit `deepseek-r1:14b` unter Linux + podman.

## Voraussetzungen

- Ollama installiert und laufend, z.B.:

  ```bash
  ollama run deepseek-r1:14b
  ```
### Build
podman build -t local-llm-chat .

### Run
podman run --rm --network=host -p 5000:5000 \
  -e OLLAMA_MODEL="deepseek-r1:14b" \
  -e FLASK_SECRET_KEY="some-secret-key" \
  local-llm-chat


---
# Dann im Browser:
```bash
http://localhost:5000
```

# Konfiguration
- OLLAMA_URL (optional): Standard http://localhost:11434
- OLLAMA_MODEL: z.B. deepseek-r1:14b, qwen3-vl:8b
- FLASK_SECRET_KEY: beliebiger geheimer String für Session-Cookies



-----------------------


# Git-Repo anlegen

Im Projektordner:

```bash
mkdir local-llm-chat
cd local-llm-chat

# Dateien wie oben anlegen ...

git init
git add app.py requirements.txt Dockerfile .gitignore README.md
git commit -m "Initial local LLM chat using Ollama and Flask"

```
#


