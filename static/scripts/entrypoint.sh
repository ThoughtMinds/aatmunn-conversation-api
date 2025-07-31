#!/bin/bash

echo "🔴 Retrieve LLAMA3.2 model..."
ollama pull llama3.2:3b
echo "🟢 Done!"

echo "🔴 Retrieve nomic-embed-text model..."
ollama pull nomic-embed-text:v1.5
echo "🟢 Done!"
