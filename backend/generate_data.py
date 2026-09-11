import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

──────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)   # creates data/ folder if it doesn't exist
print(f"Saving data to: {DATA_DIR}")

# ── 1. METRICS DATASET (for Isolation Forest + Random Forest) ──────────────
n = 5000
rows = []
for i in range(n):
    scenario = random.choices(['normal','spike','crash'], weights=[85,10,5])[0]

    if scenario == 'normal':
        cpu     = round(random.uniform(10, 65), 2)
        mem     = round(random.uniform(20, 60), 2)
        rps     = round(random.uniform(50, 300), 2)
        latency = round(random.uniform(15, 100), 2)
        label   = 0
    elif scenario == 'spike':
        cpu     = round(random.uniform(70, 92), 2)
        mem     = round(random.uniform(60, 85), 2)
        rps     = round(random.uniform(350, 550), 2)
        latency = round(random.uniform(150, 400), 2)
        label   = 1
    else:
        cpu     = round(random.uniform(88, 100), 2)
        mem     = round(random.uniform(80, 100), 2)
        rps     = round(random.uniform(5, 50), 2)
        latency = round(random.uniform(400, 900), 2)
        label   = 1

    rows.append({
        'cpu_usage':        cpu,
        'memory_usage':     mem,
        'requests_per_sec': rps,
        'latency_ms':       latency,
        'failure_label':    label
    })

metrics_df = pd.DataFrame(rows)
metrics_df.to_csv(os.path.join(DATA_DIR, 'metrics_dataset.csv'), index=False)
print(f"metrics_dataset.csv → {len(metrics_df)} rows, {metrics_df['failure_label'].sum()} failures")

# ── 2. LOGS DATASET (for TF-IDF + Logistic Regression) ────────────────────
log_templates = {
    'normal': [
        "Service health check passed",
        "Request processed successfully in 12ms",
        "Cache hit ratio 94 percent",
        "Database query optimised response 8ms",
        "Scheduled backup completed successfully",
        "User authentication successful",
        "API gateway responded 200 OK",
        "Load balancer health check OK",
        "Service restart completed normally",
        "Configuration reload successful",
    ],
    'warning': [
        "Memory usage approaching threshold 72 percent",
        "Response latency spike detected 180ms",
        "Database connection pool near limit 85 percent",
        "Traffic spike detected 3x normal baseline",
        "Disk usage high 78 percent",
        "CPU throttling starting at 68 percent",
        "Retry attempt number 2 for service auth",
        "Slow query detected taking 450ms",
        "Connection pool exhausted retrying",
        "High memory pressure swap usage increased",
    ],
    'critical': [
        "Connection timeout on service auth ERROR",
        "Memory overflow container restarting",
        "Disk IO exceeded safe limit critical failure",
        "CPU throttling critical node crash imminent",
        "Database connection failed timeout exceeded",
        "Service crashed exit code 137 OOM killed",
        "Health check failed 3 consecutive failures",
        "Kernel panic detected system unstable",
        "Network interface down packet loss 100 percent",
        "Fatal error segmentation fault core dumped",
    ]
}

log_rows = []
for _ in range(3000):
    severity = random.choices(['normal','warning','critical'], weights=[60,25,15])[0]
    msg      = random.choice(log_templates[severity])
    noise    = random.choice(['', 'on node-1', 'on node-2', 'at 14:32', 'service-api', ''])
    msg      = msg + (' ' + noise if noise else '')
    log_rows.append({'log_message': msg.strip(), 'severity': severity})

logs_df = pd.DataFrame(log_rows)
logs_df.to_csv(os.path.join(DATA_DIR, 'logs_dataset.csv'), index=False)
print(f"logs_dataset.csv    → {len(logs_df)} rows")
print(logs_df['severity'].value_counts().to_string())
print("\nDone! Check your backend/data/ folder.")
