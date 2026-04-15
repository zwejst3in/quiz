#!/bin/bash

echo "------------------------------"
echo "podman starting local-llm-chat"
echo "------------------------------"
podman run --rm --network=host -p 5000:5000   -e OLLAMA_MODEL="deepseek-r1:14b"   -e FLASK_SECRET_KEY="splash123!"   local-llm-chat:latest
exit 0
