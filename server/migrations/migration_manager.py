#!/usr/bin/env python3
"""
Automatic Database Migration Manager
Runs migrations on server startup to ensure schema is always current
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from typing import List, Dict, Tuple
import hashlib
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations automatically"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent

    def ensure_migrations_table(self, cursor):
        """Create migrations tracking table if it doesn't exist"""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                migration_hash VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT true
            )
        """
        )
        logger.info("Migrations tracking table ensured")

    def get_migration_hash(self, migration_content: str) -> str:
        """Generate hash for migration content to detect changes"""
        return hashlib.sha256(migration_content.encode()).hexdigest()

    def is_migration_applied(self, cursor, migration_name: str, migration_hash: str) -> bool:
        """Check if migration has been applied"""
        cursor.execute(
            """
            SELECT migration_hash FROM schema_migrations 
            WHERE migration_name = %s AND success = true
        """,
            (migration_name,),
        )

        result = cursor.fetchone()
        if not result:
            return False

        stored_hash = result[0]
        if stored_hash != migration_hash:
            logger.warning(f"Migration {migration_name} content has changed!")
            logger.warning(f"Stored hash: {stored_hash}")
            logger.warning(f"Current hash: {migration_hash}")
            return False

        return True

    def record_migration(self, cursor, migration_name: str, migration_hash: str, success: bool = True):
        """Record migration application"""
        cursor.execute(
            """
            INSERT INTO schema_migrations (migration_name, migration_hash, success)
            VALUES (%s, %s, %s)
            ON CONFLICT (migration_name) 
            DO UPDATE SET 
                migration_hash = EXCLUDED.migration_hash,
                applied_at = CURRENT_TIMESTAMP,
                success = EXCLUDED.success
        """,
            (migration_name, migration_hash, success),
        )

    def get_pending_migrations(self) -> List[Tuple[str, str]]:
        """Get list of pending migrations with their content"""
        migrations = []

        # Define migration order and content
        migration_definitions = [
            ("001_ensure_users_table", self._migration_001_users),
            ("002_ensure_files_table", self._migration_002_files),
            ("003_ensure_sessions_table", self._migration_003_sessions),
            ("004_add_filename_column", self._migration_004_filename),
            ("005_add_missing_columns", self._migration_005_missing_columns),
            ("006_fix_null_filenames", self._migration_006_fix_null_filenames),
            ("007_admin_sessions", self._migration_007_admin_sessions),
            ("008_admin_audit_log", self._migration_008_admin_audit_log),
            ("009_login_history", self._migration_009_login_history),
            ("010_file_access_log", self._migration_010_file_access_log),
            ("011_execution_log", self._migration_011_execution_log),
        ]

        for name, migration_func in migration_definitions:
            content = migration_func()
            migrations.append((name, content))

        return migrations

    def run_migrations(self) -> bool:
        """Run all pending migrations"""
        try:
            logger.info("Starting database migration check...")

            conn = psycopg2.connect(self.database_url)
            conn.autocommit = False
            cursor = conn.cursor()

            # Ensure migrations table exists
            self.ensure_migrations_table(cursor)
            conn.commit()

            # Get pending migrations
            migrations = self.get_pending_migrations()

            applied_count = 0
            for migration_name, migration_content in migrations:
                migration_hash = self.get_migration_hash(migration_content)

                if self.is_migration_applied(cursor, migration_name, migration_hash):
                    logger.debug(f"Migration {migration_name} already applied")
                    continue

                logger.info(f"Applying migration: {migration_name}")

                try:
                    # Execute migration
                    cursor.execute(migration_content)

                    # Record successful migration
                    self.record_migration(cursor, migration_name, migration_hash, True)

                    conn.commit()
                    applied_count += 1
                    logger.info(f"✅ Migration {migration_name} applied successfully")

                except Exception as e:
                    logger.error(f"❌ Migration {migration_name} failed: {e}")
                    conn.rollback()

                    # Record failed migration
                    self.record_migration(cursor, migration_name, migration_hash, False)
                    conn.commit()

                    raise e

            cursor.close()
            conn.close()

            if applied_count > 0:
                logger.info(f"✅ Applied {applied_count} database migrations successfully")
            else:
                logger.info("✅ Database schema is up to date")

            return True

        except Exception as e:
            logger.error(f"❌ Migration system failed: {e}")
            return False

    # Migration Definitions
    # ====================

    def _migration_001_users(self) -> str:
        """Ensure users table exists with correct schema"""
        return """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            role VARCHAR(20) CHECK(role IN ('student', 'professor')) DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """

    def _migration_002_files(self) -> str:
        """Ensure files table exists with correct schema"""
        return """
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            path VARCHAR(500) NOT NULL,
            size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_files_user_path ON files(user_id, path);
        """

    def _migration_003_sessions(self) -> str:
        """Ensure sessions table exists with correct schema"""
        return """
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        """

    def _migration_004_filename(self) -> str:
        """Add filename column if missing and populate it"""
        return """
        DO $$ 
        BEGIN
            -- Add filename column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='files' AND column_name='filename'
            ) THEN
                ALTER TABLE files ADD COLUMN filename VARCHAR(255);
                
                -- Populate filename from existing paths
                UPDATE files SET filename = 
                    CASE 
                        WHEN path LIKE '%/%' THEN 
                            substring(path from '[^/]*$')
                        ELSE 
                            path
                    END
                WHERE filename IS NULL;
                
                -- Make filename NOT NULL after populating
                ALTER TABLE files ALTER COLUMN filename SET NOT NULL;
                
                -- Create index for filename
                CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
                
                RAISE NOTICE 'Added filename column to files table';
            END IF;
        END $$;
        """

    def _migration_005_missing_columns(self) -> str:
        """Add any missing columns to existing tables"""
        return """
        DO $$ 
        BEGIN
            -- Add mime_type if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='files' AND column_name='mime_type'
            ) THEN
                ALTER TABLE files ADD COLUMN mime_type VARCHAR(100);
                RAISE NOTICE 'Added mime_type column to files table';
            END IF;
            
            -- Add updated_at if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='files' AND column_name='updated_at'
            ) THEN
                ALTER TABLE files ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                RAISE NOTICE 'Added updated_at column to files table';
            END IF;
            
            -- Add modified_at if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='files' AND column_name='modified_at'
            ) THEN
                ALTER TABLE files ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                RAISE NOTICE 'Added modified_at column to files table';
            END IF;
            
            -- Add is_submitted if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='files' AND column_name='is_submitted'
            ) THEN
                ALTER TABLE files ADD COLUMN is_submitted BOOLEAN DEFAULT false;
                RAISE NOTICE 'Added is_submitted column to files table';
            END IF;
        END $$;
        """

    def _migration_006_fix_null_filenames(self) -> str:
        """Fix any NULL filename values that may exist"""
        return """
        -- Update any NULL filename values by extracting from path
        UPDATE files
        SET filename =
            CASE
                WHEN path LIKE '%/%' THEN
                    substring(path from '[^/]*$')
                ELSE
                    path
            END
        WHERE filename IS NULL;
        """

    def _migration_007_admin_sessions(self) -> str:
        """Create admin sessions table (separate from main IDE sessions)"""
        return """
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            is_active BOOLEAN DEFAULT true
        );

        CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(token);
        CREATE INDEX IF NOT EXISTS idx_admin_sessions_user ON admin_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_admin_sessions_active ON admin_sessions(is_active);
        """

    def _migration_008_admin_audit_log(self) -> str:
        """Create admin audit log table for tracking all admin actions"""
        return """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id SERIAL PRIMARY KEY,
            admin_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action_type VARCHAR(50) NOT NULL,
            target_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            target_path VARCHAR(500),
            details JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_audit_admin_user ON admin_audit_log(admin_user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_target_user ON admin_audit_log(target_user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_action_type ON admin_audit_log(action_type);
        CREATE INDEX IF NOT EXISTS idx_audit_created_at ON admin_audit_log(created_at);
        """

    def _migration_009_login_history(self) -> str:
        """Create login history table for tracking user logins"""
        return """
        CREATE TABLE IF NOT EXISTS login_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            success BOOLEAN DEFAULT true,
            login_type VARCHAR(20) DEFAULT 'ide'
        );

        CREATE INDEX IF NOT EXISTS idx_login_user ON login_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_login_time ON login_history(login_time);
        CREATE INDEX IF NOT EXISTS idx_login_success ON login_history(success);
        """

    def _migration_010_file_access_log(self) -> str:
        """Create file access log table for tracking file operations"""
        return """
        CREATE TABLE IF NOT EXISTS file_access_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            file_path VARCHAR(500) NOT NULL,
            action VARCHAR(20) NOT NULL,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details JSONB
        );

        CREATE INDEX IF NOT EXISTS idx_file_access_user ON file_access_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_file_access_path ON file_access_log(file_path);
        CREATE INDEX IF NOT EXISTS idx_file_access_time ON file_access_log(accessed_at);
        CREATE INDEX IF NOT EXISTS idx_file_access_action ON file_access_log(action);
        """

    def _migration_011_execution_log(self) -> str:
        """Create execution log table for tracking code executions"""
        return """
        CREATE TABLE IF NOT EXISTS execution_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            file_path VARCHAR(500),
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_ms INTEGER,
            exit_code INTEGER,
            stdout_preview TEXT,
            stderr_preview TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_execution_user ON execution_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_execution_time ON execution_log(execution_time);
        CREATE INDEX IF NOT EXISTS idx_execution_exit_code ON execution_log(exit_code);
        """


def run_auto_migrations(database_url: str) -> bool:
    """Entry point for automatic migrations"""
    manager = MigrationManager(database_url)
    return manager.run_migrations()


if __name__ == "__main__":
    # For manual execution
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    success = run_auto_migrations(database_url)
    sys.exit(0 if success else 1)
