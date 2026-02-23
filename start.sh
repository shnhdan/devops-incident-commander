#!/bin/bash

echo "🚀 Starting Incident Commander..."

# Activate venv if exists
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "✅ Virtual environment activated"
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null
then
    echo "🤖 Starting Ollama..."
    ollama serve &
    sleep 3
else
    echo "✅ Ollama already running"
fi

# Start Web UI
echo "🌐 Launching Web UI..."
python agents/web_ui.py


