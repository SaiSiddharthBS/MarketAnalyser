#!/bin/bash
echo "Starting Market Analyser Production Environment..."

# Start the background scheduler
echo "Spawning scheduler in the background..."
python scheduler.py &

# Start the FastAPI web server
echo "Starting FastAPI on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000
