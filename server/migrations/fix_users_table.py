#!/usr/bin/env python3
"""
Migration to fix the users table schema
Adds missing email and full_name columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add missing columns to users table"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if email column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='email'
            """)
            
            if not cursor.fetchone():
                logger.info("Adding email column to users table...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN email VARCHAR(100)
                """)
                # Set default email for existing users
                cursor.execute("""
                    UPDATE users 
                    SET email = username || '@university.edu' 
                    WHERE email IS NULL
                """)
                # Make it NOT NULL after setting defaults
                cursor.execute("""
                    ALTER TABLE users 
                    ALTER COLUMN email SET NOT NULL
                """)
                logger.info("Email column added successfully")
            else:
                logger.info("Email column already exists")
            
            # Check if full_name column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='full_name'
            """)
            
            if not cursor.fetchone():
                logger.info("Adding full_name column to users table...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN full_name VARCHAR(100)
                """)
                # Set default full_name for existing users
                cursor.execute("""
                    UPDATE users 
                    SET full_name = username 
                    WHERE full_name IS NULL
                """)
                logger.info("Full_name column added successfully")
            else:
                logger.info("Full_name column already exists")
            
            conn.commit()
            logger.info("Migration completed successfully!")
            
            # Show current table structure
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            
            logger.info("\nCurrent users table structure:")
            for row in cursor.fetchall():
                logger.info(f"  {row[0]}: {row[1]}({row[2]}) {'NULL' if row[3] == 'YES' else 'NOT NULL'}")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting users table migration...")
    migrate()
    logger.info("Migration complete!")