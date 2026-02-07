#!/bin/bash

# WhatsApp Chatbot Startup Script
# This script starts both the Node.js bridge and Python chatbot

set -e

echo "🚀 Starting WhatsApp Chatbot..."
echo "================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18 or higher (found: $NODE_VERSION)"
    exit 1
fi

echo "✅ Node.js $(node -v) found"

# Navigate to WhatsApp integration directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHATSAPP_DIR="$SCRIPT_DIR/src/integrations/whatsapp"

# Install Node.js dependencies if needed
if [ ! -d "$WHATSAPP_DIR/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd "$WHATSAPP_DIR"
    npm install
    cd "$SCRIPT_DIR"
    echo "✅ Dependencies installed"
else
    echo "✅ Node.js dependencies already installed"
fi

# Start Node.js bridge in background
echo "🌉 Starting Node.js bridge server..."
cd "$WHATSAPP_DIR"
node server.js > /tmp/whatsapp-bridge.log 2>&1 &
NODE_PID=$!
cd "$SCRIPT_DIR"

# Wait for bridge to start and check health
echo "⏳ Waiting for bridge server to initialize..."
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ Bridge server started (PID: $NODE_PID)"
        break
    fi
    
    # Check if process is still alive
    if ! kill -0 $NODE_PID 2>/dev/null; then
        echo "❌ Bridge server crashed during startup"
        echo "📋 Last 30 lines of log:"
        tail -30 /tmp/whatsapp-bridge.log
        exit 1
    fi
    
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done
echo ""

if [ $WAITED -eq $MAX_WAIT ]; then
    echo "⚠️ Bridge server took too long to start, but continuing..."
    echo "📋 Check log: tail -f /tmp/whatsapp-bridge.log"
fi

# Check if bridge is running
if ! kill -0 $NODE_PID 2>/dev/null; then
    echo "❌ Failed to start Node.js bridge"
    exit 1
fi

echo "✅ Bridge server started (PID: $NODE_PID)"

# Activate Python virtual environment and start chatbot
echo "🐍 Starting Python chatbot..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $NODE_PID 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Python chatbot
source venv/bin/activate
python run_whatsapp.py

# If Python exits, cleanup
cleanup
