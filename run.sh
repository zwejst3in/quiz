#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="local-llm-chat"

HOST_CHAT_DIR="${HOST_CHAT_DIR:-$PWD/chats}"

mkdir -p "${HOST_CHAT_DIR}"

echo "Verfügbare Ollama-Modelle:"
echo
mapfile -t MODELS < <(ollama list | awk 'NR>1 {print $1}')

if [ "${#MODELS[@]}" -eq 0 ]; then
  echo "Keine Modelle gefunden. Bitte zuerst ein Modell mit 'ollama pull ...' laden."
  exit 1
fi

i=1
for m in "${MODELS[@]}"; do
  echo "  [$i] $m"
  i=$((i+1))
done

echo
read -rp "Bitte die Nummer des gewünschten Modells wählen: " SELECTION

if ! [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
  echo "Ungültige Eingabe."
  exit 1
fi

INDEX=$((SELECTION-1))
if [ "$INDEX" -lt 0 ] || [ "$INDEX" -ge "${#MODELS[@]}" ]; then
  echo "Auswahl außerhalb des gültigen Bereichs."
  exit 1
fi

MODEL_NAME="${MODELS[$INDEX]}"
SECRET_KEY="${FLASK_SECRET_KEY:-splash123!}"

echo
echo "Building image: ${IMAGE_NAME}"
podman build -t "${IMAGE_NAME}" .

echo "Starting container with model: ${MODEL_NAME}"
echo "Chats werden persistiert unter: ${HOST_CHAT_DIR}"

podman run --rm --network=host -p 5000:5000 \
  -e OLLAMA_MODEL="${MODEL_NAME}" \
  -e FLASK_SECRET_KEY="${SECRET_KEY}" \
  -e CHAT_DIR="/data/chats" \
  -v "${HOST_CHAT_DIR}:/data/chats" \
  "${IMAGE_NAME}"
