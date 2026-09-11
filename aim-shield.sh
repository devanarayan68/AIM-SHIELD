#!/bin/bash

###############################################################################
# AIM-SHIELD Complete Startup & Status Script
# Manages all services and provides system status
###############################################################################

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_BIN="$REPO_DIR/venv/bin"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

show_banner() {
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                            ║"
    echo "║                        🎯 AIM-SHIELD v2.0                                 ║"
    echo "║                   AI-Powered Infrastructure Monitoring                     ║"
    echo "║                                                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo ""
}

check_port() {
    local port=$1
    lsof -i :$port > /dev/null 2>&1
    return $?
}

get_pid_on_port() {
    local port=$1
    lsof -i :$port 2>/dev/null | grep -v COMMAND | awk '{print $2}' | head -1
}

# ==============================================================================
# SERVICE MANAGEMENT
# ==============================================================================

start_backend() {
    echo -e "${BLUE}[→]${NC} Starting Backend Service..."
    
    # Kill existing if running
    if check_port 5000; then
        PID=$(get_pid_on_port 5000)
        echo -e "${YELLOW}[!]${NC} Killing existing backend (PID: $PID)"
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    cd "$REPO_DIR/backend"
    nohup "$VENV_BIN/python" app_advanced.py > "$REPO_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$REPO_DIR/.backend.pid"
    
    # Wait for startup
    sleep 3
    
    # Verify
    if check_port 5000; then
        echo -e "${GREEN}[✓]${NC} Backend running on port 5000 (PID: $BACKEND_PID)"
        return 0
    else
        echo -e "${RED}[✗]${NC} Backend failed to start"
        echo "    Check log: tail -f $REPO_DIR/logs/backend.log"
        return 1
    fi
}

start_frontend() {
    echo -e "${BLUE}[→]${NC} Starting Frontend Service..."
    
    # Kill existing if running
    if check_port 8000; then
        PID=$(get_pid_on_port 8000)
        echo -e "${YELLOW}[!]${NC} Killing existing frontend (PID: $PID)"
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    cd "$REPO_DIR"
    nohup "$VENV_BIN/python" -m http.server 8000 > "$REPO_DIR/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$REPO_DIR/.frontend.pid"
    
    sleep 2
    
    if check_port 8000; then
        echo -e "${GREEN}[✓]${NC} Frontend running on port 8000 (PID: $FRONTEND_PID)"
        return 0
    else
        echo -e "${RED}[✗]${NC} Frontend failed to start"
        return 1
    fi
}

stop_backend() {
    if [ -f "$REPO_DIR/.backend.pid" ]; then
        PID=$(cat "$REPO_DIR/.backend.pid")
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
            sleep 1
            echo -e "${GREEN}[✓]${NC} Backend stopped"
            return 0
        fi
    fi
    
    if check_port 5000; then
        PID=$(get_pid_on_port 5000)
        kill -9 $PID 2>/dev/null
        echo -e "${GREEN}[✓]${NC} Backend stopped"
        return 0
    fi
    
    echo -e "${YELLOW}[!]${NC} Backend not running"
    return 1
}

stop_frontend() {
    if [ -f "$REPO_DIR/.frontend.pid" ]; then
        PID=$(cat "$REPO_DIR/.frontend.pid")
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
            sleep 1
            echo -e "${GREEN}[✓]${NC} Frontend stopped"
            return 0
        fi
    fi
    
    if check_port 8000; then
        PID=$(get_pid_on_port 8000)
        kill -9 $PID 2>/dev/null
        echo -e "${GREEN}[✓]${NC} Frontend stopped"
        return 0
    fi
    
    echo -e "${YELLOW}[!]${NC} Frontend not running"
    return 1
}

# ==============================================================================
# STATUS & MONITORING
# ==============================================================================

show_status() {
    show_banner
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}SYSTEM STATUS${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Backend status
    if check_port 5000; then
        PID=$(get_pid_on_port 5000)
        echo -e "${GREEN}●${NC} Backend:  RUNNING (port 5000, PID: $PID)"
        
        # Try API health check
        HEALTH=$(curl -s http://localhost:5000/api/health 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unreachable")
        echo -e "  └─ Health: ${GREEN}$HEALTH${NC}"
    else
        echo -e "${RED}●${NC} Backend:  STOPPED"
    fi
    
    # Frontend status
    if check_port 8000; then
        PID=$(get_pid_on_port 8000)
        echo -e "${GREEN}●${NC} Frontend: RUNNING (port 8000, PID: $PID)"
    else
        echo -e "${RED}●${NC} Frontend: STOPPED"
    fi
    
    echo ""
    
    # Database status
    if [ -f "$REPO_DIR/backend/aim_shield.db" ]; then
        SIZE=$(du -h "$REPO_DIR/backend/aim_shield.db" | awk '{print $1}')
        echo -e "${GREEN}●${NC} Database: OK ($SIZE)"
    else
        echo -e "${YELLOW}●${NC} Database: NOT INITIALIZED"
    fi
    
    echo ""
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}ENDPOINTS${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if check_port 8000; then
        echo -e "${PURPLE}🌐 FRONTEND:${NC}"
        echo "   http://localhost:8000/frontend_advanced.html"
        echo ""
    fi
    
    if check_port 5000; then
        echo -e "${PURPLE}🔌 BACKEND API:${NC}"
        echo "   http://localhost:5000"
        echo "   ws://localhost:5000/socket.io (WebSocket)"
        echo ""
        echo -e "${PURPLE}📊 API ENDPOINTS:${NC}"
        echo "   GET  /api/health       - System status"
        echo "   GET  /api/metrics      - Current metrics"
        echo "   GET  /api/logs         - Recent logs"
        echo "   GET  /api/alerts       - Active alerts"
        echo "   POST /api/alerts/ack   - Acknowledge alert"
        echo "   GET  /api/history      - Historical data"
        echo ""
    fi
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}USAGE${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Commands:"
    echo "  ./aim-shield.sh start              Start all services"
    echo "  ./aim-shield.sh stop               Stop all services"
    echo "  ./aim-shield.sh restart            Restart all services"
    echo "  ./aim-shield.sh status             Show this status"
    echo "  ./aim-shield.sh logs               View all logs"
    echo "  ./aim-shield.sh test               Run system tests"
    echo ""
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

show_logs() {
    show_banner
    echo -e "${CYAN}Tailing logs (Ctrl+C to exit)${NC}"
    echo ""
    tail -f "$REPO_DIR/logs/backend.log" "$REPO_DIR/logs/frontend.log" 2>/dev/null || \
    echo "No logs found. Ensure services are running first."
}

test_system() {
    show_banner
    
    echo -e "${CYAN}Testing AIM-SHIELD System${NC}"
    echo ""
    
    # Test backend
    echo -e "${BLUE}[→]${NC} Testing Backend API..."
    HEALTH=$(curl -s http://localhost:5000/api/health 2>/dev/null)
    if [ ! -z "$HEALTH" ]; then
        echo -e "${GREEN}[✓]${NC} Backend responding"
    else
        echo -e "${RED}[✗]${NC} Backend not responding"
    fi
    
    # Test metrics endpoint
    echo -e "${BLUE}[→]${NC} Testing Metrics Endpoint..."
    METRICS=$(curl -s http://localhost:5000/api/metrics 2>/dev/null)
    if [ ! -z "$METRICS" ]; then
        echo -e "${GREEN}[✓]${NC} Metrics endpoint working"
    else
        echo -e "${RED}[✗]${NC} Metrics endpoint not responding"
    fi
    
    # Test frontend
    echo -e "${BLUE}[→]${NC} Testing Frontend..."
    FE=$(curl -s http://localhost:8000/frontend_advanced.html 2>/dev/null | grep -c "frontend_advanced" || echo "0")
    if [ "$FE" -gt "0" ]; then
        echo -e "${GREEN}[✓]${NC} Frontend accessible"
    else
        echo -e "${RED}[✗]${NC} Frontend not responding"
    fi
    
    # Test database
    echo -e "${BLUE}[→]${NC} Testing Database..."
    if [ -f "$REPO_DIR/backend/aim_shield.db" ]; then
        echo -e "${GREEN}[✓]${NC} Database file exists"
    else
        echo -e "${RED}[✗]${NC} Database not found"
    fi
    
    echo ""
    echo -e "${CYAN}System tests complete${NC}"
}

# ==============================================================================
# MAIN SCRIPT
# ==============================================================================

# Create logs directory
mkdir -p "$REPO_DIR/logs"

case "${1:-status}" in
    start)
        show_banner
        start_backend && start_frontend
        echo ""
        show_status
        ;;
    stop)
        show_banner
        stop_backend && stop_frontend
        echo ""
        echo -e "${GREEN}[✓]${NC} All services stopped"
        ;;
    restart)
        show_banner
        stop_backend && stop_frontend
        sleep 2
        start_backend && start_frontend
        echo ""
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_system
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        exit 1
        ;;
esac
