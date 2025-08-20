"""Configuration settings for Python IDE server"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Server configuration"""
    
    # Server settings
    PORT = int(os.getenv('PORT', 8080))
    HOST = os.getenv('HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pythonide')
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', 2))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', 10))
    DB_KEEPALIVE_IDLE = int(os.getenv('DB_KEEPALIVE_IDLE', 30))
    DB_KEEPALIVE_INTERVAL = int(os.getenv('DB_KEEPALIVE_INTERVAL', 10))
    DB_KEEPALIVE_COUNT = int(os.getenv('DB_KEEPALIVE_COUNT', 5))
    
    # WebSocket settings
    WS_PING_INTERVAL = int(os.getenv('WS_PING_INTERVAL', 30))  # seconds
    WS_PONG_TIMEOUT = int(os.getenv('WS_PONG_TIMEOUT', 60))    # seconds
    WS_MAX_CONNECTIONS = int(os.getenv('WS_MAX_CONNECTIONS', 100))
    
    # Resource limits
    MAX_CONCURRENT_EXECUTIONS = int(os.getenv('MAX_CONCURRENT_EXECUTIONS', 60))
    EXECUTION_TIMEOUT = int(os.getenv('EXECUTION_TIMEOUT', 30))  # seconds
    MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', 128))
    MAX_PROCESS_AGE = int(os.getenv('MAX_PROCESS_AGE', 1800))  # 30 minutes
    MAX_REPL_AGE = int(os.getenv('MAX_REPL_AGE', 3600))       # 60 minutes
    
    # Health monitoring
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))  # seconds
    IDLE_TIMEOUT = int(os.getenv('IDLE_TIMEOUT', 3600))  # 1 hour
    MEMORY_THRESHOLD = int(os.getenv('MEMORY_THRESHOLD', 85))  # percent
    CPU_THRESHOLD = int(os.getenv('CPU_THRESHOLD', 90))  # percent
    
    # Cleanup settings
    CLEANUP_INTERVAL_MS = int(os.getenv('CLEANUP_INTERVAL_MS', 300000))  # 5 minutes
    RESOURCE_CHECK_INTERVAL_MS = int(os.getenv('RESOURCE_CHECK_INTERVAL_MS', 60000))  # 1 minute
    
    # Security settings
    SECRET_KEY = os.getenv('IDE_SECRET_KEY', 'development-secret-key')
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 86400))  # 24 hours
    
    # Railway specific
    RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT')
    IS_PRODUCTION = RAILWAY_ENVIRONMENT == 'production'
    
    @classmethod
    def log_config(cls):
        """Log configuration (hiding sensitive values)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Configuration loaded:")
        logger.info(f"  Environment: {'Production' if cls.IS_PRODUCTION else 'Development'}")
        logger.info(f"  Port: {cls.PORT}")
        logger.info(f"  Max concurrent executions: {cls.MAX_CONCURRENT_EXECUTIONS}")
        logger.info(f"  Execution timeout: {cls.EXECUTION_TIMEOUT}s")
        logger.info(f"  Memory limit: {cls.MEMORY_LIMIT_MB}MB")
        logger.info(f"  WebSocket ping interval: {cls.WS_PING_INTERVAL}s")
        logger.info(f"  Database pool: {cls.DB_POOL_MIN}-{cls.DB_POOL_MAX} connections")

config = Config()