#!/bin/bash

echo "Checking for A2A Double Validation processes..."
echo "NOTE: System health is determined by active ports"
echo "-----------------------------------------------------------------"

# Track overall system status
system_running=true
port_issues=false

# Check if uvicorn servers are running on the expected ports - this is the primary health check
ports=(8001 8002 8003 8004 8005 9001)
labels=("Manager A2A" "Safeguard A2A" "Processor A2A" "Critic A2A" "Main API" "Manager API")

echo "PORT CHECKS:"
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