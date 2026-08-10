#!/bin/bash
# Double-click this file to launch the NBA Matchup Dashboard.
# It sets up a local Python environment the first time, then starts the app
# in your browser. Later launches are fast.

cd "$(dirname "$0")" || exit 1
echo "🏀  NBA Matchup Dashboard — starting up..."
echo

# Find Python 3
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "❌ Python 3 isn't installed. Get it from https://www.python.org/downloads/ and try again."
  read -r -p "Press Return to close."
  exit 1
fi

# Create a local virtual environment on first run
if [ ! -d ".venv" ]; then
  echo "📦 First-time setup: creating a local environment (this takes a minute)..."
  "$PY" -m venv .venv || { echo "❌ Could not create venv."; read -r -p "Press Return to close."; exit 1; }
  ./.venv/bin/pip install --upgrade pip >/dev/null 2>&1
  echo "📦 Installing packages..."
  ./.venv/bin/pip install -r requirements.txt || { echo "❌ Install failed."; read -r -p "Press Return to close."; exit 1; }
fi

# Build the engine if it hasn't been built yet
if [ ! -f "models/engine.json" ]; then
  echo "🧮 Building the prediction engine..."
  ./.venv/bin/python -m scripts.build_ratings
fi

echo
echo "✅ Launching. Your browser will open at http://localhost:8501"
echo "   (To stop the app later: close this window.)"
echo
./.venv/bin/streamlit run app.py
