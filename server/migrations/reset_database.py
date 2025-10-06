#!/usr/bin/env python3
"""
Reset database - drops all tables and recreates them with correct schema
WARNING: This will delete all data!
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_database():
    """Drop all tables and recreate with correct schema"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            logger.info("Dropping existing tables...")

            # Drop tables in correct order (respecting foreign keys)
            cursor.execute("DROP TABLE IF EXISTS file_submissions CASCADE")
            cursor.execute("DROP TABLE IF EXISTS files CASCADE")
            cursor.execute("DROP TABLE IF EXISTS sessions CASCADE")
            cursor.execute("DROP TABLE IF EXISTS users CASCADE")

            logger.info("Tables dropped successfully")

            # Recreate tables with correct schema
            logger.info("Creating users table...")
            cursor.execute(
                """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                )
            """
            )

            logger.info("Creating sessions table...")
            cursor.execute(
                """
                CREATE TABLE sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                )
            """
            )

            logger.info("Creating files table...")
            cursor.execute(
                """
                CREATE TABLE files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    path VARCHAR(500) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    size INTEGER,
                    mime_type VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT false,
                    UNIQUE(user_id, path)
                )
            """
            )

            logger.info("Creating file_submissions table...")
            cursor.execute(
                """
                CREATE TABLE file_submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    assignment_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    submission_id VARCHAR(100) UNIQUE NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    grade DECIMAL(5,2),
                    feedback TEXT,
                    graded_at TIMESTAMP,
                    graded_by INTEGER REFERENCES users(id)
                )
            """
            )

            # Create indexes for better performance
            logger.info("Creating indexes...")
            cursor.execute("CREATE INDEX idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX idx_sessions_token ON sessions(token)")
            cursor.execute("CREATE INDEX idx_files_user_path ON files(user_id, path)")
            cursor.execute("CREATE INDEX idx_submissions_user ON file_submissions(user_id)")

            conn.commit()
            logger.info("Database reset completed successfully!")

            # Show table structure
            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
            )

            tables = cursor.fetchall()
            logger.info(f"\nCreated {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


if __name__ == "__main__":
    response = input("WARNING: This will DELETE all data! Type 'yes' to continue: ")
    if response.lower() == "yes":
        logger.info("Starting database reset...")
        reset_database()
        logger.info("Database reset complete! Run create_users.py to add default users.")
    else:
        logger.info("Database reset cancelled.")
