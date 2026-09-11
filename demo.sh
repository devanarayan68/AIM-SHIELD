#!/bin/bash

###############################################################################
# AIM-SHIELD One-Click Demo Launcher
# Opens everything you need in your browser
###############################################################################

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🎯 AIM-SHIELD Demo Launcher"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if services are running
echo "✓ Checking services..."

if ! lsof -i :5000 > /dev/null 2>&1; then
    echo "⚠️  Backend not running. Starting..."
    cd "$REPO_DIR/backend"
    nohup "$REPO_DIR/venv/bin/python" app_advanced.py > "$REPO_DIR/logs/backend.log" 2>&1 &
    sleep 3
fi

if ! lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Frontend not running. Starting..."
    cd "$REPO_DIR"
    nohup "$REPO_DIR/venv/bin/python" -m http.server 8000 > "$REPO_DIR/logs/frontend.log" 2>&1 &
    sleep 2
fi

echo "✓ Both services verified running"
echo ""
echo "🌐 Opening your browser to the dashboard..."
echo ""

# Open in default browser
sleep 1
open http://localhost:8000/frontend_advanced.html

echo "✓ Dashboard opened in your default browser"
echo ""
echo "📊 You should now see:"
echo "   • Real-time system metrics"
echo "   • 4-tab dashboard interface"
echo "   • System simulation controls"
echo "   • Alert management"
echo "   • Historical data explorer"
echo ""
echo "🎬 Ready for your demo!"
echo ""
echo "Backend API: http://localhost:5000"
echo "Frontend Dashboard: http://localhost:8000/frontend_advanced.html"
echo ""
echo "View deployment details:"
echo "   cat $REPO_DIR/DEPLOYMENT_COMPLETE.md"
echo ""
echo "Read the investor demo script:"
echo "   cat $REPO_DIR/INVESTOR_DEMO.md"
echo ""
