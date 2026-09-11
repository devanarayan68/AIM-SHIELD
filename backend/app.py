"""
AIM-SHIELD Backend — Flask API Server
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pickle
import numpy as np
import random
import time
import os

app = Flask(__name__)
CORS(app)

# ── Load models using path relative to THIS file ──────────────────────────
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

print("All models loaded. AIM-SHIELD backend ready.")

# ── State ─────────────────────────────────────────────────────────────────
current_state = {
    'load_factor':  0.4,
    'active_users': 120,
    'spike':        False,
    'crash':        False,
}

LOG_TEMPLATES = {
    'normal': [
        "Service health check passed",
        "Request processed successfully in 12ms",
        "Cache hit ratio 94 percent",
        "Database query optimised response 8ms",
        "User authentication successful",
        "API gateway responded 200 OK",
        "Load balancer health check OK",
        "Scheduled backup completed successfully",
    ],
    'warning': [
        "Memory usage approaching threshold 72 percent",
        "Response latency spike detected 180ms",
        "Database connection pool near limit 85 percent",
        "Traffic spike detected 3x normal baseline",
        "CPU throttling starting at 68 percent",
        "Slow query detected taking 450ms",
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

    # Real Isolation Forest
    metric_vector = np.array([[cpu, mem, rps, latency]])
    raw_score     = iso_forest.decision_function(metric_vector)[0]
    iso_score     = clamp(round((0.3 - raw_score) / 0.6, 3), 0, 1)
    is_anomaly    = bool(iso_forest.predict(metric_vector)[0] == -1)

    # Real Random Forest
    rf_proba  = rf_model.predict_proba(metric_vector)[0]
    fail_prob = round(float(rf_proba[1]), 3)

    # Severity
    if fail_prob > 0.70:   severity = 'CRITICAL'
    elif fail_prob > 0.45 or iso_score > 0.6: severity = 'WARNING'
    else:                  severity = 'NORMAL'

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

    # Real TF-IDF + Logistic Regression
    tfidf_vector    = tfidf.transform([message])
    predicted_class = lr_model.predict(tfidf_vector)[0]
    probabilities   = lr_model.predict_proba(tfidf_vector)[0]
    confidence      = round(float(max(probabilities)) * 100, 1)

    level_map = {'normal': 'info', 'warning': 'warn', 'critical': 'error'}

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


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status':  'running',
        'models':  ['IsolationForest', 'RandomForest', 'TfidfVectorizer', 'LogisticRegression'],
        'message': 'AIM-SHIELD backend is live'
    })


if __name__ == '__main__':
    print("\nAIM-SHIELD Backend running on http://localhost:5000")
    app.run(debug=True, port=5000)
