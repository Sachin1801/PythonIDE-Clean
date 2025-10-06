import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import db_manager


class UserManager:
    def __init__(self, db_path="server/ide.db"):
        # Use the global database manager which handles PostgreSQL/SQLite
        self.db = db_manager

    def get_connection(self):
        # Return a connection from the database manager
        return self.db.get_connection()

    def create_user(self, username, email, password, full_name, role="student"):
        """Create new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.db.is_postgres:
                    cursor.execute(
                        """
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """,
                        (username, email, password_hash.decode(), full_name, role),
                    )
            conn.commit()
            conn.close()
            return True, "User created successfully"
        except sqlite3.IntegrityError as e:
            if conn:
                conn.close()
            return False, f"User already exists: {e}"

    def authenticate(self, username, password):
        """Authenticate user and create session"""
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)

            conn.execute(
                """
                INSERT INTO sessions (session_id, username, expires_at)
                VALUES (?, ?, ?)
            """,
                (session_id, username, expires_at),
            )

            # Update last login
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?", (username,))
            conn.commit()
            conn.close()

            return {
                "success": True,
                "session_id": session_id,
                "username": username,
                "role": user["role"],
                "full_name": user["full_name"],
            }

        conn.close()
        return {"success": False, "error": "Invalid credentials"}

    def validate_session(self, session_id):
        """Check if session is valid"""
        conn = self.get_connection()
        cursor = conn.execute(
            """
            SELECT s.*, u.role, u.full_name 
            FROM sessions s
            JOIN users u ON s.username = u.username
            WHERE s.session_id = ? AND s.expires_at > CURRENT_TIMESTAMP
        """,
            (session_id,),
        )

        session = cursor.fetchone()
        conn.close()
        return dict(session) if session else None

    def logout(self, session_id):
        """Invalidate a session"""
        conn = self.get_connection()
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        return True

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        conn = self.get_connection()
        cursor = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(old_password.encode(), user["password_hash"].encode()):
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash.decode(), username))
            conn.commit()
            conn.close()
            return {"success": True, "message": "Password changed successfully"}

        conn.close()
        return {"success": False, "error": "Invalid old password"}

    def get_user(self, username):
        """Get user details"""
        conn = self.get_connection()
        cursor = conn.execute(
            "SELECT username, email, full_name, role, created_at, last_login FROM users WHERE username = ?", (username,)
        )
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
