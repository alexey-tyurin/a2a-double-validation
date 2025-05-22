#!/bin/bash

echo "Stopping A2A Double Validation processes..."

# Array of process patterns to find and kill
patterns=("python main.py" "agent_manager" "agent_processor" "agent_critic" "agent_safeguard")

# Function to kill processes by pattern
kill_pattern() {
    local pattern=$1
    local pids=$(pgrep -f "$pattern")
    
    if [ -n "$pids" ]; then
        echo "Found processes matching '$pattern':"
        ps -f -p $pids
        
        echo "Killing processes..."
        # First try graceful termination
        kill $pids 2>/dev/null
        
        # Wait a moment
        sleep 2
        
        # Check if still running and force kill if necessary
        if pgrep -f "$pattern" > /dev/null; then
            echo "Some processes still running, force killing..."
            kill -9 $(pgrep -f "$pattern") 2>/dev/null
        fi
        
        echo "✅ Processes matching '$pattern' terminated."
    else
        echo "No processes found matching '$pattern'."
    fi
}

# Kill each pattern
for pattern in "${patterns[@]}"; do
    kill_pattern "$pattern"
    echo ""
done

# Kill any remaining uvicorn processes related to our ports
ports=(8001 8002 8003 8004 8005 9001)
for port in "${ports[@]}"; do
    pid=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)..."
        kill $pid 2>/dev/null
        sleep 1
        # Force kill if still running
        kill -9 $pid 2>/dev/null
        echo "✅ Process on port $port terminated."
    fi
done

echo "All A2A Double Validation processes have been stopped." 