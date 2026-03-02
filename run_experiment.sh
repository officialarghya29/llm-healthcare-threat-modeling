#!/bin/bash

# Log file
LOG_FILE="experiments/logs/runner.log"
exec > >(tee -a $LOG_FILE) 2>&1

echo "Starting Orchestrator on port 8001..."
venv/bin/uvicorn experiments.orchestrator.main:app --host 127.0.0.1 --port 8001 &
PID=$!
echo "Orchestrator PID: $PID"

# Wait for server to be ready
echo "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8001/docs > /dev/null; then
        echo "Server is UP!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Run attacker
echo "Running Attacker..."
export ORCHESTRATOR_URL="http://127.0.0.1:8001/generate"
PYTHONPATH=. venv/bin/python experiments/client/attacker.py

# Cleanup
echo "Killing Orchestrator ($PID)..."
kill $PID
wait $PID 2>/dev/null
echo "Done."
