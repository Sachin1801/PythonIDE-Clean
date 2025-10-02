import os
import sqlite3
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, RealDictRow
from urllib.parse import urlparse
from contextlib import contextmanager
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.is_postgres = True  # Always use PostgreSQL
        self.connection_pool = None
        
        # Azure PostgreSQL URL format detection and conversion
        if self.database_url and 'database.azure.com' in self.database_url:
            logger.info("Azure PostgreSQL detected, configuring for Azure")
            # Azure requires SSL
            if 'sslmode=' not in self.database_url:
                self.database_url += '&sslmode=require' if '?' in self.database_url else '?sslmode=require'
        
        if not self.database_url:
            # Default to local PostgreSQL if no DATABASE_URL is set
            self.database_url = "postgresql://postgres:postgres@localhost:5432/pythonide"
            logger.info("No DATABASE_URL found, using default local PostgreSQL")
        
        # Initialize PostgreSQL
        try:
            connection_info = self.database_url.split('@')[1] if '@' in self.database_url else 'local'
            logger.info(f"Connecting to PostgreSQL: {connection_info}")
            self._init_postgres()
            logger.info("Connected to PostgreSQL database successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            # Parse database URL
            url = urlparse(self.database_url)
            
            # Create connection pool with keepalive settings - using config values
            try:
                from config import Config
                min_conn = Config.DB_POOL_MIN
                max_conn = Config.DB_POOL_MAX
            except ImportError:
                # Fallback to direct environment variables if config module not available
                min_conn = int(os.getenv('DB_POOL_MIN', 5))
                max_conn = int(os.getenv('DB_POOL_MAX', 25))
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                min_conn, max_conn,  # increased from 2,10 to support 40+ concurrent students
                host=url.hostname,
                port=url.port or 5432,
                database=url.path[1:],
                user=url.username,
                password=url.password,
                # Add keepalive parameters to prevent connection drops
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=10
            )
            logger.info("PostgreSQL connection pool created")
            
            # Initialize tables
            self._init_postgres_tables()
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        try:
            # Create database if it doesn't exist
            conn = sqlite3.connect(self.db_path)
            self._init_sqlite_tables(conn)
            conn.close()
            logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    def _init_postgres_tables(self):
        """Create tables for PostgreSQL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table - First try to create, then migrate if needed
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                )
            ''')
            
            # Add missing columns if they don't exist (migration)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='email'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")
                cursor.execute("UPDATE users SET email = username || '@university.edu' WHERE email IS NULL")
                cursor.execute("ALTER TABLE users ALTER COLUMN email SET NOT NULL")
                
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='full_name'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)")
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add last_activity column if it doesn't exist (migration)
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='sessions' AND column_name='last_activity'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE sessions ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # File metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, path)
                )
            ''')
            
            # Submissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    assignment_name VARCHAR(255),
                    file_path TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    grade DECIMAL(5,2),
                    feedback TEXT
                )
            ''')
            
            # Password reset tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_used BOOLEAN DEFAULT false
                )
            ''')
            
            # Create index for faster token lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at)')
            
            conn.commit()
            logger.info("PostgreSQL tables initialized")
    
    def _init_sqlite_tables(self, conn):
        """Create tables for SQLite"""
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # File metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, path)
            )
        ''')
        
        # Submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                assignment_name TEXT,
                file_path TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                grade REAL,
                feedback TEXT
            )
        ''')
        
        conn.commit()
        logger.info("SQLite tables initialized")
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool or create new one"""
        conn = None
        try:
            if self.is_postgres:
                conn = self.connection_pool.getconn()
                # Test connection is still valid
                try:
                    with conn.cursor() as cur:
                        cur.execute('SELECT 1')
                except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                    logger.warning(f"Connection invalid, recreating: {e}")
                    # Return bad connection to pool and get a new one
                    self.connection_pool.putconn(conn, close=True)
                    conn = self.connection_pool.getconn()
                
                # Set cursor factory to return dictionaries
                conn.cursor_factory = RealDictCursor
                yield conn
                conn.commit()
            else:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                if self.is_postgres:
                    # Check if connection is still good before returning to pool
                    try:
                        conn.cursor().execute('SELECT 1')
                        self.connection_pool.putconn(conn)
                    except:
                        self.connection_pool.putconn(conn, close=True)
                else:
                    conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            if self.is_postgres:
                # Use RealDictCursor for PostgreSQL
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                # For PostgreSQL with RealDictCursor, results are already dicts
                # For SQLite with Row factory, results can be accessed as dicts
                return results
            else:
                return cursor.rowcount
    
    def close(self):
        """Close all database connections"""
        if self.is_postgres and self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()