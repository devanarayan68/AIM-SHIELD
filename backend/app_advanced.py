"""
AIM-SHIELD Backend v2 — Advanced Infrastructure Monitoring with WebSockets & Alerts
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import pickle
import numpy as np
import random
import time
import os
import json
from datetime import datetime
from database import db

# ── Flask App Setup ────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aim-shield-secret-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ── Load Models ────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

print("Loading trained models...")

with open(os.path.join(MODELS_DIR, 'isolation_forest.pkl'),    'rb') as f:
    iso_forest = pickle.load(f)
with open(os.path.join(MODELS_DIR, 'random_forest.pkl'),       'rb') as f:
    rf_model = pickle.load(f)
with open(os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl'),    'rb') as f:
    tfidf = pickle.load(f)
with open(os.path.join(MODELS_DIR, 'logistic_regression.pkl'), 'rb') as f:
    lr_model = pickle.load(f)

print("All models loaded. AIM-SHIELD v2 backend ready.")

# ── State & Config ─────────────────────────────────────────────────────────
current_state = {
    'load_factor':  0.4,
    'active_users': 120,
    'spike':        False,
    'crash':        False,
}

# Alert thresholds
THRESHOLDS = {
    'cpu_warning': 70,
    'cpu_critical': 85,
    'memory_warning': 75,
    'memory_critical': 90,
    'latency_warning': 200,
    'latency_critical': 500,
    'fail_prob_warning': 0.45,
    'fail_prob_critical': 0.70,
}

LOG_TEMPLATES = {
    'normal': [
        "Service health check passed", "Request processed successfully in 12ms",
        "Cache hit ratio 94 percent", "Database query optimised response 8ms",
        "User authentication successful", "API gateway responded 200 OK",
        "Load balancer health check OK", "Scheduled backup completed successfully",
    ],
    'warning': [
        "Memory usage approaching threshold 72 percent",
        "Response latency spike detected 180ms",
        "Database connection pool near limit 85 percent",
        "Traffic spike detected 3x normal baseline",
        "CPU throttling starting at 68 percent", "Slow query detected taking 450ms",
        "High memory pressure swap usage increased",
    ],
    'critical': [
        "Connection timeout on service auth ERROR",
        "Memory overflow container restarting",
        "CPU throttling critical node crash imminent",
        "Database connection failed timeout exceeded",
        "Service crashed exit code 137 OOM killed",
        "Health check failed 3 consecutive failures",
        "Fatal error segmentation fault core dumped",
    ]
}

def rnd(a, b):   return round(random.uniform(a, b), 2)
def clamp(v,a,b): return max(a, min(b, v))

# ── ADVANCED: Alert Management ─────────────────────────────────────────────
def check_and_create_alerts(cpu, mem, latency, fail_prob):
    """Check thresholds and create alerts."""
    alerts_created = []
    
    # CPU alerts
    if cpu >= THRESHOLDS['cpu_critical']:
        alert_id = db.create_alert('CRITICAL', 'CPU Critical', f'CPU usage at {cpu}%')
        alerts_created.append({'id': alert_id, 'severity': 'CRITICAL', 'type': 'CPU'})
    elif cpu >= THRESHOLDS['cpu_warning']:
        alert_id = db.create_alert('WARNING', 'CPU Warning', f'CPU usage at {cpu}%')
        alerts_created.append({'id': alert_id, 'severity': 'WARNING', 'type': 'CPU'})
    
    # Memory alerts
    if mem >= THRESHOLDS['memory_critical']:
        alert_id = db.create_alert('CRITICAL', 'Memory Critical', f'Memory usage at {mem}%')
        alerts_created.append({'id': alert_id, 'severity': 'CRITICAL', 'type': 'Memory'})
    elif mem >= THRESHOLDS['memory_warning']:
        alert_id = db.create_alert('WARNING', 'Memory Warning', f'Memory usage at {mem}%')
        alerts_created.append({'id': alert_id, 'severity': 'WARNING', 'type': 'Memory'})
    
    # Latency alerts
    if latency >= THRESHOLDS['latency_critical']:
        alert_id = db.create_alert('CRITICAL', 'Latency Critical', f'Latency at {latency}ms')
        alerts_created.append({'id': alert_id, 'severity': 'CRITICAL', 'type': 'Latency'})
    elif latency >= THRESHOLDS['latency_warning']:
        alert_id = db.create_alert('WARNING', 'Latency Warning', f'Latency at {latency}ms')
        alerts_created.append({'id': alert_id, 'severity': 'WARNING', 'type': 'Latency'})
    
    # Failure probability alerts
    if fail_prob >= THRESHOLDS['fail_prob_critical']:
        alert_id = db.create_alert('CRITICAL', 'Failure Risk Critical', f'Failure probability: {fail_prob*100:.1f}%')
        alerts_created.append({'id': alert_id, 'severity': 'CRITICAL', 'type': 'Prediction'})
    elif fail_prob >= THRESHOLDS['fail_prob_warning']:
        alert_id = db.create_alert('WARNING', 'Failure Risk Warning', f'Failure probability: {fail_prob*100:.1f}%')
        alerts_created.append({'id': alert_id, 'severity': 'WARNING', 'type': 'Prediction'})
    
    return alerts_created

# ── REST API ───────────────────────────────────────────────────────────────

@app.route('/api/state', methods=['POST'])
def update_state():
    data = request.get_json()
    current_state['load_factor']   = float(data.get('load_factor', 0.4))
    current_state['active_users']  = int(data.get('active_users', 120))
    current_state['spike']         = bool(data.get('spike', False))
    current_state['crash']         = bool(data.get('crash', False))
    return jsonify({'status': 'ok'})

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    lf    = current_state['load_factor']
    spike = current_state['spike']
    crash = current_state['crash']

    cpu     = clamp(round(15 + lf*55 + (28 if spike else 0) + (38 if crash else 0) + rnd(-5,5),  1), 0, 100)
    mem     = clamp(round(25 + lf*45 + (15 if spike else 0) + (20 if crash else 0) + rnd(-4,4),  1), 0, 100)
    rps     = clamp(round(50 + lf*380 + (190 if spike else 0) + (-40 if crash else 0) + rnd(-20,20), 1), 0, 600)
    latency = clamp(round(18 + lf*80 + (130 if spike else 0) + (320 if crash else 0) + rnd(-8,8), 1), 5, 900)

    metric_vector = np.array([[cpu, mem, rps, latency]])
    raw_score     = iso_forest.decision_function(metric_vector)[0]
    iso_score     = clamp(round((0.3 - raw_score) / 0.6, 3), 0, 1)
    is_anomaly    = bool(iso_forest.predict(metric_vector)[0] == -1)

    rf_proba  = rf_model.predict_proba(metric_vector)[0]
    fail_prob = round(float(rf_proba[1]), 3)

    if fail_prob > 0.70:   severity = 'CRITICAL'
    elif fail_prob > 0.45 or iso_score > 0.6: severity = 'WARNING'
    else:                  severity = 'NORMAL'

    # Save to database
    db.save_metrics(cpu, mem, rps, latency, iso_score, fail_prob, severity, is_anomaly)
    
    # Check thresholds & create alerts
    alerts = check_and_create_alerts(cpu, mem, latency, fail_prob)

    return jsonify({
        'cpu':          cpu,
        'memory':       mem,
        'rps':          rps,
        'latency':      latency,
        'active_users': current_state['active_users'],
        'iso_score':    iso_score,
        'fail_prob':    fail_prob,
        'severity':     severity,
        'is_anomaly':   is_anomaly,
        'alerts':       alerts,
        'timestamp':    time.strftime('%H:%M:%S'),
    })

@app.route('/api/log', methods=['GET'])
def get_log():
    lf    = current_state['load_factor']
    spike = current_state['spike']
    crash = current_state['crash']

    if crash:            pool = LOG_TEMPLATES['critical']
    elif spike or lf > 0.7: pool = LOG_TEMPLATES['warning'] + LOG_TEMPLATES['critical']
    elif lf > 0.4:       pool = LOG_TEMPLATES['normal'] + LOG_TEMPLATES['warning']
    else:                pool = LOG_TEMPLATES['normal']

    message = random.choice(pool)

    tfidf_vector    = tfidf.transform([message])
    predicted_class = lr_model.predict(tfidf_vector)[0]
    probabilities   = lr_model.predict_proba(tfidf_vector)[0]
    confidence      = round(float(max(probabilities)) * 100, 1)

    level_map = {'normal': 'info', 'warning': 'warn', 'critical': 'error'}
    
    # Save to database
    db.save_log(message, level_map.get(predicted_class, 'info'), predicted_class, confidence)

    return jsonify({
        'message':    message,
        'level':      level_map.get(predicted_class, 'info'),
        'tag':        predicted_class,
        'confidence': confidence,
        'timestamp':  time.strftime('%H:%M:%S'),
    })

@app.route('/api/classify_log', methods=['POST'])
def classify_log():
    data    = request.get_json()
    message = data.get('message', '')
    if not message.strip():
        return jsonify({'error': 'Empty message'}), 400

    tfidf_vector    = tfidf.transform([message])
    predicted_class = lr_model.predict(tfidf_vector)[0]
    probabilities   = lr_model.predict_proba(tfidf_vector)[0]
    classes         = list(lr_model.classes_)
    prob_dict       = {cls: round(float(p)*100, 1) for cls, p in zip(classes, probabilities)}

    return jsonify({
        'message':        message,
        'classification': predicted_class,
        'probabilities':  prob_dict,
        'timestamp':      time.strftime('%H:%M:%S'),
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    limit = request.args.get('limit', 50, type=int)
    acknowledged = request.args.get('acknowledged', None)
    if acknowledged is not None:
        acknowledged = acknowledged.lower() == 'false'
    
    alerts = db.get_alerts(limit=limit, acknowledged=acknowledged)
    return jsonify({'alerts': alerts})

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    data = request.get_json() or {}
    acknowledged_by = data.get('acknowledged_by', 'web-user')
    db.acknowledge_alert(alert_id, acknowledged_by)
    return jsonify({'status': 'acknowledged'})

@app.route('/api/history/metrics', methods=['GET'])
def metrics_history():
    hours = request.args.get('hours', 24, type=int)
    history = db.get_metrics_history(hours=hours)
    return jsonify({'metrics': history})

@app.route('/api/history/logs', methods=['GET'])
def logs_history():
    hours = request.args.get('hours', 24, type=int)
    history = db.get_logs_history(hours=hours)
    return jsonify({'logs': history})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = db.get_statistics()
    return jsonify(stats)

@app.route('/api/health', methods=['GET'])
def health():
    stats = db.get_statistics()
    return jsonify({
        'status':  'running',
        'models':  ['IsolationForest', 'RandomForest', 'TfidfVectorizer', 'LogisticRegression'],
        'message': 'AIM-SHIELD v2 backend is live',
        'stats': stats
    })

# ── WebSocket Events ───────────────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_response', {'data': 'Connected to AIM-SHIELD'})

@socketio.on('join_metrics')
def on_join_metrics():
    join_room('metrics_room')
    emit('status', {'msg': 'Joined metrics stream'})

@socketio.on('join_alerts')
def on_join_alerts():
    join_room('alerts_room')
    emit('status', {'msg': 'Joined alerts stream'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

# ── Background emission of metrics & alerts via WebSocket ──────────────────

import threading

def emit_metrics_loop():
    """Emit metrics every 2 seconds to all connected clients."""
    while True:
        try:
            lf    = current_state['load_factor']
            spike = current_state['spike']
            crash = current_state['crash']

            cpu     = clamp(round(15 + lf*55 + (28 if spike else 0) + (38 if crash else 0) + rnd(-5,5),  1), 0, 100)
            mem     = clamp(round(25 + lf*45 + (15 if spike else 0) + (20 if crash else 0) + rnd(-4,4),  1), 0, 100)
            rps     = clamp(round(50 + lf*380 + (190 if spike else 0) + (-40 if crash else 0) + rnd(-20,20), 1), 0, 600)
            latency = clamp(round(18 + lf*80 + (130 if spike else 0) + (320 if crash else 0) + rnd(-8,8), 1), 5, 900)

            metric_vector = np.array([[cpu, mem, rps, latency]])
            raw_score     = iso_forest.decision_function(metric_vector)[0]
            iso_score     = clamp(round((0.3 - raw_score) / 0.6, 3), 0, 1)
            is_anomaly    = bool(iso_forest.predict(metric_vector)[0] == -1)
            rf_proba      = rf_model.predict_proba(metric_vector)[0]
            fail_prob     = round(float(rf_proba[1]), 3)

            if fail_prob > 0.70:   severity = 'CRITICAL'
            elif fail_prob > 0.45 or iso_score > 0.6: severity = 'WARNING'
            else:                  severity = 'NORMAL'

            db.save_metrics(cpu, mem, rps, latency, iso_score, fail_prob, severity, is_anomaly)
            alerts = check_and_create_alerts(cpu, mem, latency, fail_prob)

            socketio.emit('metrics_update', {
                'cpu': cpu, 'memory': mem, 'rps': rps, 'latency': latency,
                'active_users': current_state['active_users'],
                'iso_score': iso_score, 'fail_prob': fail_prob,
                'severity': severity, 'is_anomaly': is_anomaly,
                'alerts': alerts, 'timestamp': datetime.now().isoformat()
            }, room='metrics_room')

            if alerts:
                socketio.emit('new_alerts', {'alerts': alerts}, room='alerts_room')

            time.sleep(2)
        except Exception as e:
            print(f"Error in metrics emission: {e}")
            time.sleep(2)

# Start background thread
metrics_thread = threading.Thread(target=emit_metrics_loop, daemon=True)
metrics_thread.start()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("AIM-SHIELD v2 Backend running on http://localhost:5000")
    print("WebSocket Support: Enabled")
    print("Database: SQLite (aim_shield.db)")
    print("="*60)
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
