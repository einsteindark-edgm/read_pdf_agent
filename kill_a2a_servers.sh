#!/bin/bash
# Script to kill all processes using port 8080

echo "🔍 Finding processes using port 8080..."

# Find PIDs using port 8080
PIDS=$(lsof -ti:8080)

if [ -z "$PIDS" ]; then
    echo "✅ No processes found using port 8080"
    exit 0
fi

echo "Found the following processes:"
lsof -i:8080

echo ""
echo "🛑 Killing processes..."

for PID in $PIDS; do
    echo "   Killing process $PID..."
    kill -9 $PID 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ Process $PID killed"
    else
        echo "   ❌ Failed to kill process $PID (may require sudo)"
    fi
done

echo ""
echo "🔍 Verifying..."
REMAINING=$(lsof -ti:8080)

if [ -z "$REMAINING" ]; then
    echo "✅ All processes using port 8080 have been terminated"
else
    echo "⚠️  Some processes are still running:"
    lsof -i:8080
    echo ""
    echo "You may need to run: sudo ./kill_a2a_servers.sh"
fi