#!/bin/bash

# Configuration
LOG_FILE="experiments/logs/batch_runner.log"

# Setup
mkdir -p experiments/logs

echo "Starting Orchestrator on port 8001..." | tee -a "$LOG_FILE"
# Start Orchestrator in background
nohup venv/bin/uvicorn experiments.orchestrator.main:app --host 127.0.0.1 --port 8001 > nohup.out 2>&1 &
SERVER_PID=$!
echo "Orchestrator PID: $SERVER_PID" | tee -a "$LOG_FILE"

# Wait for server to start
echo "Waiting for server to be ready..." | tee -a "$LOG_FILE"
for i in {1..30}; do
    if curl -s http://127.0.0.1:8001/docs > /dev/null; then
        echo "Server is UP!" | tee -a "$LOG_FILE"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Run Batch Client
echo "Running Batch Runner..." | tee -a "$LOG_FILE"
PYTHONPATH=. venv/bin/python experiments/client/batch_runner.py 2>&1 | tee -a "$LOG_FILE"

# Cleanup
echo "Experiment Complete. Killing Orchestrator ($SERVER_PID)..." | tee -a "$LOG_FILE"
kill $SERVER_PID
echo "Done." | tee -a "$LOG_FILE"
