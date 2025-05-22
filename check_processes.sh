#!/bin/bash

echo "Checking for A2A Double Validation processes..."
echo "NOTE: System health is primarily determined by active ports, not process names"
echo "-----------------------------------------------------------------"

# Track overall system status
system_running=true
port_issues=false

# Check if uvicorn servers are running on the expected ports - this is the primary health check
ports=(8001 8002 8003 8004 8005 9001)
labels=("Manager A2A" "Safeguard A2A" "Processor A2A" "Critic A2A" "Main API" "Manager API")

echo "PORT CHECKS (PRIMARY HEALTH INDICATOR):"
for i in "${!ports[@]}"; do
    if lsof -i :${ports[$i]} -sTCP:LISTEN > /dev/null; then
        echo "✅ ${labels[$i]} server (port ${ports[$i]}) is running"
    else
        echo "❌ ${labels[$i]} server (port ${ports[$i]}) is NOT running"
        port_issues=true
        system_running=false
    fi
done

echo "-----------------------------------------------------------------"
echo "PROCESS NAME CHECKS (INFORMATIONAL ONLY):"

# Check if main.py is running - this is just informational
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Main process (python main.py) is running"
else
    echo "ℹ️ Main process (python main.py) is not detected (but system may still be running)"
fi

# Additional check for Python processes related to agents - just informational
agent_patterns=("agent_manager" "agent_processor" "agent_critic" "agent_safeguard")

for pattern in "${agent_patterns[@]}"; do
    count=$(pgrep -f "$pattern" | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "✅ $pattern processes: $count running"
    else
        echo "ℹ️ $pattern processes not detected by name (but system may still be running)"
    fi
done

echo "-----------------------------------------------------------------"
# Overall system status
if [ "$system_running" = true ]; then
    if [ "$port_issues" = true ]; then
        echo "⚠️ SYSTEM STATUS: PARTIAL - Some services are running but others are missing"
    else
        echo "✅ SYSTEM STATUS: RUNNING - All services are operational"
    fi
else
    echo "❌ SYSTEM STATUS: NOT RUNNING - Critical services are missing"
fi 