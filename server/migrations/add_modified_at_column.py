#!/usr/bin/env python3
"""
Add modified_at column to files table
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_modified_at_column():
    """Add modified_at column to files table if it doesn't exist"""
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    # For local development, replace internal Railway hostname with public one
    if 'postgres.railway.internal' in database_url:
        # Try to use the public URL instead
        database_public_url = os.environ.get('DATABASE_PUBLIC_URL')
        if database_public_url:
            database_url = database_public_url
            print("Using public database URL for connection")
        else:
            print("WARNING: Using internal Railway URL, this may not work locally")
            print("Set DATABASE_PUBLIC_URL environment variable for local access")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='files' AND column_name='modified_at'
        """)
        
        if cur.fetchone():
            print("Column 'modified_at' already exists in 'files' table")
        else:
            # Add the column
            print("Adding 'modified_at' column to 'files' table...")
            cur.execute("""
                ALTER TABLE files 
                ADD COLUMN modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            # Update existing rows to have current timestamp
            cur.execute("""
                UPDATE files 
                SET modified_at = CURRENT_TIMESTAMP 
                WHERE modified_at IS NULL
            """)
            
            conn.commit()
            print("Successfully added 'modified_at' column to 'files' table")
        
        # Also check and add created_at if missing
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='files' AND column_name='created_at'
        """)
        
        if cur.fetchone():
            print("Column 'created_at' already exists in 'files' table")
        else:
            print("Adding 'created_at' column to 'files' table...")
            cur.execute("""
                ALTER TABLE files 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            cur.execute("""
                UPDATE files 
                SET created_at = CURRENT_TIMESTAMP 
                WHERE created_at IS NULL
            """)
            
            conn.commit()
            print("Successfully added 'created_at' column to 'files' table")
        
        # Close connection
        cur.close()
        conn.close()
        
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = add_modified_at_column()
    sys.exit(0 if success else 1)