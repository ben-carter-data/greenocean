#!/bin/bash
# Runs the download agent and the raw load with this computer's own network.
# Double-click this file in Finder; the output stays visible in Terminal.
cd "$(dirname "$0")/.." || exit 1

# A local virtual environment keeps the project libraries apart from the system.
if [ ! -d ".venv" ]; then
    python3 -m venv .venv || exit 1
fi
.venv/bin/python -m pip install --quiet -r requirements.txt || exit 1

.venv/bin/python agent/agent.py
echo "Agent exit code: $?"
.venv/bin/python etl/etl.py
echo "ETL exit code: $?"
