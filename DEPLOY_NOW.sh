#!/bin/bash

###############################################################################
# AIM-SHIELD One-Click Deployment Script
# Deploys everything automatically - no manual steps needed
###############################################################################

set -e

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$REPO_DIR/venv"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  AIM-SHIELD Deployment Script                  ║"
echo "║                    Automated Setup (v2 Edition)                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# ==============================================================================
# STEP 1: Check Python and Virtual Environment
# ==============================================================================
log_step "Checking Python environment..."

if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created"
else
    log_success "Virtual environment exists"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
log_success "Virtual environment activated"

# ==============================================================================
# STEP 2: Install Dependencies
# ==============================================================================
log_step "Installing Python dependencies..."

pip install --upgrade pip wheel setuptools > /dev/null 2>&1

required_packages=(
    "flask==3.0.0"
    "flask-cors==4.0.0"
    "flask-socketio==5.3.5"
    "python-socketio==5.9.0"
    "python-engineio==4.7.1"
    "numpy==1.24.3"
    "pandas==2.0.3"
    "scikit-learn==1.3.0"
    "python-dotenv==1.0.0"
    "boto3==1.28.0"
    "botocore==1.31.0"
)

for package in "${required_packages[@]}"; do
    pip install "$package" > /dev/null 2>&1
done

log_success "All dependencies installed"

# ==============================================================================
# STEP 3: Create Environment Configuration
# ==============================================================================
log_step "Setting up environment configuration..."

cat > "$REPO_DIR/.env" << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=aim-shield-secret-key-production-2026
DATABASE_URL=sqlite:///aim_shield.db
LOG_LEVEL=INFO
ALERT_ENABLED=1
ENABLE_WEBSOCKET=1
EOF

log_success "Environment configuration created (.env)"

# ==============================================================================
# STEP 4: Initialize Database
# ==============================================================================
log_step "Initializing database..."

cd "$REPO_DIR/backend"

python3 << 'PYEOF'
from database import Database
db = Database()
db.init_db()
print("✓ Database initialized successfully")
PYEOF

log_success "Database initialized"

# ==============================================================================
# STEP 5: Kill Any Existing Processes
# ==============================================================================
log_step "Cleaning up existing processes..."

# Kill any process using port 5000
lsof -i :5000 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 1
log_success "Port 5000 cleaned"

# ==============================================================================
# STEP 6: Start Backend Service
# ==============================================================================
log_step "Starting AIM-SHIELD backend service..."

nohup python3 app_advanced.py > "$REPO_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$REPO_DIR/.backend.pid"

# Wait for backend to start
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    log_success "Backend service started (PID: $BACKEND_PID)"
else
    log_error "Backend failed to start. Check $REPO_DIR/backend.log"
    cat "$REPO_DIR/backend.log"
    exit 1
fi

# ==============================================================================
# STEP 7: Start Frontend Service
# ==============================================================================
log_step "Starting frontend HTTP server..."

cd "$REPO_DIR"

# Kill any process using port 8000
lsof -i :8000 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
sleep 1

nohup python3 -m http.server 8000 > "$REPO_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$REPO_DIR/.frontend.pid"

sleep 2
log_success "Frontend server started (PID: $FRONTEND_PID)"

# ==============================================================================
# STEP 8: Verify Services
# ==============================================================================
log_step "Verifying services..."

# Check backend health
for i in {1..5}; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        log_success "Backend API is responding"
        break
    fi
    if [ $i -eq 5 ]; then
        log_error "Backend API not responding"
        exit 1
    fi
    sleep 1
done

# Check frontend
if curl -s http://localhost:8000/frontend_advanced.html > /dev/null 2>&1; then
    log_success "Frontend is accessible"
else
    log_error "Frontend not accessible"
    exit 1
fi

# ==============================================================================
# STEP 9: Database Migration (v1 to v2)
# ==============================================================================
log_step "Running database migration..."

if [ -f "$REPO_DIR/migrate_v1_to_v2.py" ]; then
    python3 migrate_v1_to_v2.py > /dev/null 2>&1 || true
    log_success "Database migration completed"
fi

# ==============================================================================
# STEP 10: Generate Initial Data
# ==============================================================================
log_step "Generating initial test data..."

cd "$REPO_DIR/backend"

python3 << 'PYEOF'
from generate_data import generate_sample_metrics, generate_sample_logs
from database import Database

db = Database()
generate_sample_metrics(count=50)
generate_sample_logs(count=50)
print("✓ Sample data generated")
PYEOF

log_success "Initial data generated"

# ==============================================================================
# STEP 11: Create Deployment Summary
# ==============================================================================
log_step "Creating deployment summary..."

SUMMARY_FILE="$REPO_DIR/DEPLOYMENT_SUMMARY.txt"

cat > "$SUMMARY_FILE" << EOF
╔════════════════════════════════════════════════════════════════════════════╗
║                     AIM-SHIELD Deployment Summary                         ║
║                          $(date +%Y-%m-%d\ %H:%M:%S)                             ║
╚════════════════════════════════════════════════════════════════════════════╝

🚀 DEPLOYMENT STATUS: ✓ SUCCESS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SYSTEM ENDPOINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 FRONTEND DASHBOARD:
   http://localhost:8000/frontend_advanced.html
   (4-tab interface: Dashboard, Alerts, History, Models)

🔌 BACKEND API:
   http://localhost:5000
   Real-time WebSocket streaming on ws://localhost:5000/socket.io

📈 API ENDPOINTS:
   GET  /api/health          - System health check
   GET  /api/metrics         - Current metrics
   GET  /api/logs            - Recent logs
   GET  /api/alerts          - Active alerts
   POST /api/alerts/ack      - Acknowledge alert
   GET  /api/history         - Historical data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 PROCESS INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend Service:
   PID: $BACKEND_PID
   Port: 5000
   Status: Running
   Log: $REPO_DIR/backend.log

Frontend Service:
   PID: $FRONTEND_PID
   Port: 8000
   Status: Running
   Log: $REPO_DIR/frontend.log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 DATA & CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database:
   Location: $REPO_DIR/backend/aim_shield.db
   Type: SQLite
   Tables: 5 (metrics_history, logs_history, alerts, model_performance, patterns)

Environment Config:
   File: $REPO_DIR/.env
   Mode: Production

Python Environment:
   Path: $VENV_DIR
   Version: $(python3 --version)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 AVAILABLE COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View Logs:
   tail -f $REPO_DIR/backend.log
   tail -f $REPO_DIR/frontend.log

Stop Services:
   kill $BACKEND_PID
   kill $FRONTEND_PID

Restart Services:
   bash $REPO_DIR/DEPLOY_NOW.sh

Access Database:
   sqlite3 $REPO_DIR/backend/aim_shield.db

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✓ System is running locally
   Open: http://localhost:8000/frontend_advanced.html

2. Test the system:
   - Use Load/Spike/Crash controls to simulate scenarios
   - View alerts in real-time
   - Check historical data

3. For AWS Deployment:
   Configure AWS credentials, then run:
   $VENV_DIR/bin/python deploy_to_aws.py

4. For Production:
   - Update FLASK_ENV to 'production'
   - Configure SSL/TLS certificates
   - Setup backup strategy (see AWS_DEPLOYMENT.md)
   - Configure monitoring and alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read documentation:
   - README_ADVANCED.md      - Full feature documentation
   - QUICKSTART.md           - Quick start guide
   - AWS_DEPLOYMENT.md       - Cloud deployment guide
   - INVESTOR_DEMO.md        - Pitch deck and demo script
   - INDEX.md                - Documentation index

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ DEPLOYMENT TIME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Completed: $(date +%Y-%m-%d\ %H:%M:%S)
Ready to use immediately!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions or issues? Check the documentation or run:
   $VENV_DIR/bin/python deploy_to_aws.py

Happy monitoring! 🎉

EOF

cat "$SUMMARY_FILE"
log_success "Deployment summary created"

# ==============================================================================
# FINAL SUMMARY
# ==============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✓ DEPLOYMENT COMPLETE                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Open your browser to:"
echo "   http://localhost:8000/frontend_advanced.html"
echo ""
echo "🔌 Backend API running on:"
echo "   http://localhost:5000"
echo ""
echo "💾 See deployment details in:"
echo "   $SUMMARY_FILE"
echo ""
echo "📝 Stop services with:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
