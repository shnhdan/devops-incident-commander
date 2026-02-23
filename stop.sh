#!/bin/bash
echo "Stopping services..."

pkill -f web_ui.py
pkill ollama

echo "Stopped."
