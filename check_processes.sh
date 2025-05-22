#!/bin/bash

echo "Checking for A2A Double Validation processes..."

# Check if main.py is running
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Main process (python main.py) is running"
else
    echo "❌ Main process (python main.py) is NOT running"
fi

# Check if uvicorn servers are running on the expected ports
ports=(8001 8002 8003 8004 8005 9001)
labels=("Manager A2A" "Safeguard A2A" "Processor A2A" "Critic A2A" "Main API" "Manager API")

for i in "${!ports[@]}"; do
    if lsof -i :${ports[$i]} -sTCP:LISTEN > /dev/null; then
        echo "✅ ${labels[$i]} server (port ${ports[$i]}) is running"
    else
        echo "❌ ${labels[$i]} server (port ${ports[$i]}) is NOT running"
    fi
done

# Additional check for Python processes related to agents
agent_patterns=("agent_manager" "agent_processor" "agent_critic" "agent_safeguard")

for pattern in "${agent_patterns[@]}"; do
    count=$(pgrep -f "$pattern" | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "✅ $pattern processes: $count running"
    else
        echo "❌ $pattern processes: none running"
    fi
done

echo "Process check complete." 