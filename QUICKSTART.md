# 🚀 AIM-SHIELD v2 Quick Start Guide

## What's Running Now?

✅ **Backend v2** (Advanced) — http://localhost:5000
- WebSocket real-time streaming enabled
- SQLite database active (persistent storage)
- Alert management system running
- All 4 AI models loaded

✅ **Frontend v2** (Advanced) — http://localhost:8000/frontend_advanced.html
- Multi-tab dashboard (Dashboard/Alerts/History/Models)
- Real-time metrics with WebSocket
- Alert management interface
- Historical data explorer

---

## 🎯 Key Features to Try

### 1. **Real-Time Metrics (Dashboard Tab)**
- See CPU, Memory, RPS, Latency update in real-time
- Anomaly detection score
- Failure probability prediction
- System severity indicator

### 2. **System Simulation Controls**
- **Load Factor Slider** — Simulate 0% to 100% system load
- **Spike Toggle** — Simulate 3x traffic spike
- **Crash Toggle** — Simulate system failure mode
- Watch how AI models react to different scenarios

### 3. **Alerts Management (Alerts Tab)**
- Automatic alerts when thresholds exceeded
- View unacknowledged alerts count
- Acknowledge alerts with one click
- Historical alert browsing

### 4. **Historical Data (History Tab)**
- Query metrics from any time range (1-168 hours)
- Visualize CPU, Memory, Latency trends
- Date-range filtering

### 5. **System Statistics (Models Tab)**
- Database statistics (metrics, logs, alerts stored)
- Model information (IsolationForest, RandomForest, TF-IDF+LogReg)
- Unacknowledged alert count
- Average anomaly score

---

## 📊 Real-Time Examples

### Example 1: Trigger CPU Warning
1. Set Load Factor to **0.7**
2. Watch CPU metric exceed **70%**
3. See **WARNING** severity in AI Predictions
4. Check Alerts tab for CPU Warning alert

### Example 2: Trigger Critical State
1. Toggle **Spike ON**
2. Toggle **Crash ON**
3. Watch metrics spike (CPU >80%, Latency >300ms)
4. See **CRITICAL** severity
5. Multiple CRITICAL alerts will appear

### Example 3: Acknowledge Alerts
1. Go to **Alerts Tab**
2. Click **"Acknowledge"** button on any alert
3. See it move to acknowledged status
4. Alert count in sidebar decreases

---

## 🔧 Configuration

### Customize Alert Thresholds

Edit `.env` file in project root:

```bash
# Example: Make alerts more sensitive
CPU_WARNING=50
CPU_CRITICAL=70
LATENCY_WARNING=100
LATENCY_CRITICAL=300
```

Then restart backend:
```bash
python backend/app_advanced.py
```

### Change WebSocket Update Frequency

Edit `.env`:
```bash
# Updates every 1 second instead of 2
METRICS_EMISSION_INTERVAL=1
```

---

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Get Current Metrics
```bash
curl http://localhost:5000/api/metrics
```

### List Active Alerts
```bash
curl http://localhost:5000/api/alerts?limit=10
```

### Get System Statistics
```bash
curl http://localhost:5000/api/stats
```

### Classify a Log Message
```bash
curl -X POST http://localhost:5000/api/classify_log \
  -H "Content-Type: application/json" \
  -d '{"message":"Connection timeout on service auth ERROR"}'
```

---

## 🗄️ Database Access

### Check Stored Metrics
```bash
sqlite3 backend/aim_shield.db
sqlite> SELECT COUNT(*) FROM metrics_history;
sqlite> SELECT * FROM metrics_history ORDER BY timestamp DESC LIMIT 5;
```

### View Alerts
```bash
sqlite> SELECT * FROM alerts ORDER BY created_at DESC;
```

### Clear Database (Reset Everything)
```bash
rm backend/aim_shield.db
# Backend will auto-recreate empty database on restart
```

---

## 🐳 Docker Option

### Run Everything in Docker

```bash
# Build and start
docker-compose up --build

# Services will be available at:
# Backend: http://localhost:5000
# Frontend: http://localhost:8080

# Stop everything
docker-compose down
```

---

## ☸️ Kubernetes Option

### Deploy to Kubernetes Cluster

```bash
# Apply deployment manifests
kubectl apply -f k8s-deployment.yaml

# Check deployments
kubectl get deployments

# Get service endpoints
kubectl get svc

# View logs
kubectl logs -f deployment/aim-shield-backend

# Port forward for local access
kubectl port-forward svc/aim-shield-backend-svc 5000:5000
```

---

## 🔍 Troubleshooting

### Issue: "WebSocket Disconnected" in Sidebar

**Cause**: Backend not running or connection failed

**Solution**:
```bash
# Check if backend is running
curl http://localhost:5000/api/health

# Restart backend if needed
python backend/app_advanced.py
```

### Issue: No Data Appearing

**Cause**: Frontend not connected to backend

**Solution**:
1. Check browser console (F12) for errors
2. Ensure backend is running on port 5000
3. Clear browser cache and reload
4. Check CORS in .env file

### Issue: "Address already in use" (Port 5000)

**Cause**: Another application using port 5000

**Solution**:
```bash
# Kill process using port 5000
lsof -i :5000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

### Issue: Database Locked Error

**Cause**: Multiple connections to SQLite

**Solution**:
```bash
# Close other connections and restart backend
rm backend/aim_shield.db
python backend/app_advanced.py
```

---

## 📈 Monitoring Backend

### Watch Real-Time Logs
```bash
tail -f logs/aim_shield.log
```

### Check Database Size
```bash
ls -lh backend/aim_shield.db
```

### Monitor Memory Usage
```bash
top -p $(pgrep -f "app_advanced.py")
```

---

## 🎓 Advanced Usage

### Export Metrics to CSV
```python
import sqlite3
import csv

conn = sqlite3.connect('backend/aim_shield.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM metrics_history')
rows = cursor.fetchall()

with open('metrics_export.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'cpu', 'memory', 'rps', 'latency', ...])
    writer.writerows(rows)
```

### Implement Custom Alert Handler
Edit `backend/app_advanced.py` and modify `check_and_create_alerts()`:

```python
def check_and_create_alerts(cpu, mem, latency, fail_prob):
    # Add custom logic here
    if cpu > 90:
        send_email_alert()  # Custom function
        send_slack_alert()  # Custom function
```

### Add New API Endpoint
```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({'custom': 'data'})
```

---

## 📚 Documentation

For complete documentation:
- **README_ADVANCED.md** — Full feature guide
- **UPGRADE_SUMMARY.md** — What changed in v2
- **.env.example** — All configuration options
- **k8s-deployment.yaml** — Kubernetes setup

---

## 💡 Pro Tips

1. **Dashboard Refresh Rate**: Update frequency is 2 seconds (configurable in .env)
2. **Alert History**: Alerts are stored in SQLite (survives restarts)
3. **Performance**: CPU usage stays low even with hundreds of metrics
4. **Scalability**: Ready for Kubernetes multi-pod deployments
5. **Customization**: All thresholds adjustable via .env without code changes

---

## 🚀 Next Steps

1. **Explore Dashboard** — Try different load scenarios
2. **Check Database** — Run sample SQLite queries
3. **Review Code** — Look at `backend/app_advanced.py` and `frontend_advanced.html`
4. **Deploy to Docker** — Test `docker-compose up --build`
5. **Deploy to Kubernetes** — Use `kubectl apply -f k8s-deployment.yaml`
6. **Extend System** — Add new models, endpoints, or features

---

## 🤝 Need Help?

- Check `/api/health` endpoint for system status
- Review browser DevTools Network tab for WebSocket issues
- Check terminal logs from backend process
- See README_ADVANCED.md for full documentation

---

**🎉 You're ready to explore AIM-SHIELD v2!**

Start with the **Dashboard** tab and use the controls to simulate different system states. Watch how the AI models predict failures in real-time! 🚀
