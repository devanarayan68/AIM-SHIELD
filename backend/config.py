"""
AIM-SHIELD Configuration Module
Centralized configuration for all backend components
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'aim-shield-secret-2026')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'aim_shield.db')
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'aim_shield.log')
    
    # WebSocket
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    SOCKETIO_MESSAGE_QUEUE = os.getenv('MESSAGE_QUEUE', None)
    
    # Metrics & Data
    METRICS_HISTORY_LIMIT = int(os.getenv('METRICS_HISTORY_LIMIT', 1000))
    LOGS_HISTORY_LIMIT = int(os.getenv('LOGS_HISTORY_LIMIT', 500))
    ALERTS_RETENTION_DAYS = int(os.getenv('ALERTS_RETENTION_DAYS', 30))
    
    # Emission interval (seconds)
    METRICS_EMISSION_INTERVAL = int(os.getenv('METRICS_EMISSION_INTERVAL', 2))
    
    # Alert Thresholds
    THRESHOLDS = {
        'cpu_warning': int(os.getenv('CPU_WARNING', 70)),
        'cpu_critical': int(os.getenv('CPU_CRITICAL', 85)),
        'memory_warning': int(os.getenv('MEMORY_WARNING', 75)),
        'memory_critical': int(os.getenv('MEMORY_CRITICAL', 90)),
        'latency_warning': int(os.getenv('LATENCY_WARNING', 200)),
        'latency_critical': int(os.getenv('LATENCY_CRITICAL', 500)),
        'rps_warning': int(os.getenv('RPS_WARNING', 400)),
        'rps_critical': int(os.getenv('RPS_CRITICAL', 550)),
        'fail_prob_warning': float(os.getenv('FAIL_PROB_WARNING', 0.45)),
        'fail_prob_critical': float(os.getenv('FAIL_PROB_CRITICAL', 0.70)),
        'iso_score_warning': float(os.getenv('ISO_SCORE_WARNING', 0.5)),
        'iso_score_critical': float(os.getenv('ISO_SCORE_CRITICAL', 0.8)),
    }
    
    # Models
    MODELS_DIR = os.getenv('MODELS_DIR', 'models')
    ISOLATION_FOREST_CONTAMINATION = float(os.getenv('ISO_CONTAMINATION', 0.15))
    RANDOM_FOREST_MAX_DEPTH = int(os.getenv('RF_MAX_DEPTH', 10))
    TFIDF_MAX_FEATURES = int(os.getenv('TFIDF_MAX_FEATURES', 500))
    LOGISTIC_REGRESSION_C = float(os.getenv('LR_C', 1.0))
    
    # Feature flags
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true'
    ENABLE_DATABASE = os.getenv('ENABLE_DATABASE', 'true').lower() == 'true'
    ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'true').lower() == 'true'
    ENABLE_HISTORY = os.getenv('ENABLE_HISTORY', 'true').lower() == 'true'
    
    # Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    @staticmethod
    def get_threshold(key, default=None):
        """Safely get threshold value"""
        return Config.THRESHOLDS.get(key, default)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///test.db'
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'
    # CORS should be restricted in production
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'localhost').split(',')


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)


# Active configuration
current_config = get_config()

print(f"[CONFIG] Environment: {os.getenv('FLASK_ENV', 'development')}")
print(f"[CONFIG] Database: {current_config.DATABASE_URL}")
print(f"[CONFIG] WebSocket: {'Enabled' if current_config.ENABLE_WEBSOCKET else 'Disabled'}")
print(f"[CONFIG] Alerts: {'Enabled' if current_config.ENABLE_ALERTS else 'Disabled'}")
print(f"[CONFIG] Thresholds: CPU {current_config.THRESHOLDS['cpu_warning']}°/{current_config.THRESHOLDS['cpu_critical']}°")
