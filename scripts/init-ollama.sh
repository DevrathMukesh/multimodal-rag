#!/bin/bash
# Script to initialize Ollama with the embedding model
# This should be run after Ollama container starts

set -e

echo "Waiting for Ollama to be ready..."
until curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama..."
    sleep 2
done

echo "Pulling embedding model: embeddinggemma:latest"
curl -X POST http://localhost:11434/api/pull -d '{
    "name": "embeddinggemma:latest"
}'

echo "Ollama initialization complete!"
echo "Available models:"
curl -s http://localhost:11434/api/tags | jq -r '.models[].name'

