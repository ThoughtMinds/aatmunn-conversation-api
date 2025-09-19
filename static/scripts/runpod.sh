#!/bin/bash

# Ollama Setup Script
# This script installs Ollama on Linux, configures it to listen on 0.0.0.0,
# starts the server in the background, and pulls the specified models.

set -e  # Exit on any error

echo "Starting Ollama installation and setup..."

# Step 1: Install Ollama (Linux)
echo "Step 1: Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Ollama."
    exit 1
fi

echo "Ollama installed successfully."

# Step 2: Expose to 0.0.0.0 with env var
echo "Step 2: Configuring Ollama to listen on 0.0.0.0..."
export OLLAMA_HOST=0.0.0.0:11434

# Note: To make this persistent, add 'export OLLAMA_HOST=0.0.0.0:11434' to ~/.bashrc or run this script with source.

# Step 3: Serve Ollama in background
echo "Step 3: Starting Ollama server in background..."
ollama serve &

# Wait a moment for the server to start
sleep 5

if [ $? -ne 0 ]; then
    echo "Error: Failed to start Ollama server."
    exit 1
fi

echo "Ollama server started on 0.0.0.0:11434"

# Step 4: Pull models
models=("llama3.2:1b" "llama3.2:3b" "nomic-embed-text:v1.5")

echo "Step 4: Pulling models..."
for model in "${models[@]}"; do
    echo "Pulling $model..."
    ollama pull "$model"
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to pull $model. It may already exist or there was a network issue."
    else
        echo "$model pulled successfully."
    fi
done

echo "Setup complete! Ollama is running in the background."
echo "To check status: ollama list"
echo "To stop the server: pkill ollama"