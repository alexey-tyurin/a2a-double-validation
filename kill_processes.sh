#!/bin/bash

echo "Stopping A2A Double Validation processes..."
echo "Looking for processes on known A2A ports..."

# Kill processes running on the application's ports
ports=(8001 8002 8003 8004 8005 9001)
port_labels=("Manager A2A" "Safeguard A2A" "Processor A2A" "Critic A2A" "Main API" "Manager API")
processes_killed=0

for i in "${!ports[@]}"; do
    port=${ports[$i]}
    label=${port_labels[$i]}
    pid=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pid" ]; then
        echo "Found $label process on port $port (PID: $pid)"
        echo "Terminating process..."
        # First try graceful termination
        kill $pid 2>/dev/null
        
        # Wait a moment
        sleep 1
        
        # Check if still running and force kill if necessary
        if lsof -ti :$port > /dev/null 2>&1; then
            echo "Process still running, force killing..."
            kill -9 $(lsof -ti :$port) 2>/dev/null
        fi
        
        echo "✅ Process on port $port terminated"
        ((processes_killed++))
    fi
done

if [ $processes_killed -eq 0 ]; then
    echo "No A2A processes found running on expected ports."
else
    echo "Successfully terminated $processes_killed A2A processes."
fi

echo "A2A Double Validation processes have been stopped." 