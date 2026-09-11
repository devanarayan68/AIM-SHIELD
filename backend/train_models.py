import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ── Use paths relative to THIS file — works on any computer ───────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 50)
print("AIM-SHIELD — Training AI Models")
print("=" * 50)
print(f"Loading data from:  {DATA_DIR}")
print(f"Saving models to:   {MODELS_DIR}")

# ── MODEL 1: Isolation Forest ─────────────────────────────────────────────
print("\n[1/3] Training Isolation Forest for anomaly detection...")

metrics_df = pd.read_csv(os.path.join(DATA_DIR, 'metrics_dataset.csv'))
features   = ['cpu_usage', 'memory_usage', 'requests_per_sec', 'latency_ms']
X_metrics  = metrics_df[features].values
X_normal   = metrics_df[metrics_df['failure_label'] == 0][features].values

iso_forest = IsolationForest(n_estimators=100, contamination=0.15, random_state=42)
iso_forest.fit(X_normal)

preds        = iso_forest.predict(X_metrics)
preds_binary = (preds == -1).astype(int)
actual       = metrics_df['failure_label'].values
acc          = (preds_binary == actual).sum() / len(actual)
print(f"  Accuracy: {acc*100:.1f}%")
print(f"  Anomalies detected: {preds_binary.sum()} / {len(preds_binary)}")

with open(os.path.join(MODELS_DIR, 'isolation_forest.pkl'), 'wb') as f:
    pickle.dump(iso_forest, f)
print("  Saved isolation_forest.pkl")

# ── MODEL 2: Random Forest ────────────────────────────────────────────────
print("\n[2/3] Training Random Forest for failure prediction...")

X = metrics_df[features].values
y = metrics_df['failure_label'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_model.fit(X_train, y_train)

acc = accuracy_score(y_test, rf_model.predict(X_test))
print(f"  Accuracy: {acc*100:.1f}%")
print("  Feature importances:")
for feat, imp in zip(features, rf_model.feature_importances_):
    print(f"    {feat}: {imp*100:.1f}%")

with open(os.path.join(MODELS_DIR, 'random_forest.pkl'), 'wb') as f:
    pickle.dump(rf_model, f)
print("  Saved random_forest.pkl")

# ── MODEL 3: TF-IDF + Logistic Regression ────────────────────────────────
print("\n[3/3] Training TF-IDF + Logistic Regression for log classification...")

logs_df = pd.read_csv(os.path.join(DATA_DIR, 'logs_dataset.csv'))
tfidf   = TfidfVectorizer(max_features=500, ngram_range=(1,2), stop_words='english')

X_logs  = tfidf.fit_transform(logs_df['log_message'].values)
y_logs  = logs_df['severity'].values
X_train_l, X_test_l, y_train_l, y_test_l = train_test_split(
    X_logs, y_logs, test_size=0.2, random_state=42
)

lr_model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
lr_model.fit(X_train_l, y_train_l)

acc = accuracy_score(y_test_l, lr_model.predict(X_test_l))
print(f"  Accuracy: {acc*100:.1f}%")

with open(os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl'), 'wb') as f:
    pickle.dump(tfidf, f)
with open(os.path.join(MODELS_DIR, 'logistic_regression.pkl'), 'wb') as f:
    pickle.dump(lr_model, f)
print("  Saved tfidf_vectorizer.pkl")
print("  Saved logistic_regression.pkl")

print("\n" + "=" * 50)
print("All 4 models trained and saved successfully!")
print("Check your backend/models/ folder.")
print("=" * 50)
