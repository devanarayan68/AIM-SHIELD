"""
Database layer for AIM-SHIELD — SQLite for metrics, logs, and alerts
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'aim_shield.db')

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        """Initialize database with all required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Metrics history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    requests_per_sec REAL,
                    latency_ms REAL,
                    iso_score REAL,
                    fail_prob REAL,
                    severity TEXT,
                    is_anomaly INTEGER
                )
            ''')

            # Logs history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message TEXT,
                    predicted_level TEXT,
                    predicted_tag TEXT,
                    confidence REAL
                )
            ''')

            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    is_acknowledged INTEGER DEFAULT 0,
                    acknowledged_at DATETIME,
                    acknowledged_by TEXT
                )
            ''')

            # Model performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    accuracy REAL,
                    precision REAL,
                    recall REAL,
                    f1_score REAL
                )
            ''')

            # Anomaly patterns (for clustering)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anomaly_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    pattern_type TEXT,
                    feature_values TEXT,
                    frequency INTEGER,
                    last_seen DATETIME
                )
            ''')

            conn.commit()

    def save_metrics(self, cpu, memory, rps, latency, iso_score, fail_prob, severity, is_anomaly):
        """Save metrics to history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics_history 
                (cpu_usage, memory_usage, requests_per_sec, latency_ms, iso_score, fail_prob, severity, is_anomaly)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cpu, memory, rps, latency, iso_score, fail_prob, severity, int(is_anomaly)))

    def save_log(self, message, predicted_level, predicted_tag, confidence):
        """Save log classification to history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs_history 
                (message, predicted_level, predicted_tag, confidence)
                VALUES (?, ?, ?, ?)
            ''', (message, predicted_level, predicted_tag, confidence))

    def create_alert(self, severity, title, description):
        """Create a new alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (severity, title, description)
                VALUES (?, ?, ?)
            ''', (severity, title, description))
            return cursor.lastrowid

    def get_alerts(self, limit=50, acknowledged=None):
        """Fetch recent alerts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM alerts'
            params = []
            
            if acknowledged is not None:
                query += ' WHERE is_acknowledged = ?'
                params.append(int(acknowledged))
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id, acknowledged_by='system'):
        """Mark alert as acknowledged."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET is_acknowledged = 1, acknowledged_at = CURRENT_TIMESTAMP, acknowledged_by = ?
                WHERE id = ?
            ''', (acknowledged_by, alert_id))

    def get_metrics_history(self, hours=24):
        """Fetch metrics from the last N hours."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT * FROM metrics_history 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT 1000
            ''', (cutoff.isoformat(),))
            return [dict(row) for row in cursor.fetchall()]

    def get_logs_history(self, hours=24):
        """Fetch logs from the last N hours."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT * FROM logs_history 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT 500
            ''', (cutoff.isoformat(),))
            return [dict(row) for row in cursor.fetchall()]

    def save_model_performance(self, model_name, accuracy, precision, recall, f1):
        """Track model performance metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_performance 
                (model_name, accuracy, precision, recall, f1_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_name, accuracy, precision, recall, f1))

    def get_model_performance(self, model_name, hours=24):
        """Get performance history for a model."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT * FROM model_performance 
                WHERE model_name = ? AND timestamp > ? 
                ORDER BY timestamp DESC
            ''', (model_name, cutoff.isoformat()))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self):
        """Get system statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM metrics_history')
            metrics_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM logs_history')
            logs_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE is_acknowledged = 0')
            unack_alerts = cursor.fetchone()['count']
            
            cursor.execute('SELECT AVG(iso_score) as avg_anomaly FROM metrics_history WHERE is_anomaly = 1')
            avg_anomaly = cursor.fetchone()['avg_anomaly'] or 0
            
            return {
                'metrics_stored': metrics_count,
                'logs_stored': logs_count,
                'unacknowledged_alerts': unack_alerts,
                'avg_anomaly_score': round(avg_anomaly, 3)
            }

# Global instance
db = Database()
