import tornado.web
import json
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.database import db_manager

logger = logging.getLogger(__name__)


class SetupHandler(tornado.web.RequestHandler):
    def get(self):
        """Initialize database and create default users"""
        try:
            # Check if setup already done
            manager = UserManager()
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]

                if count > 0:
                    self.write(
                        json.dumps(
                            {
                                "status": "already_setup",
                                "message": f"Database already has {count} users",
                                "users": ["professor", "sa9082"],
                            }
                        )
                    )
                    return

            # Create default users
            results = []

            # Create professor account
            try:
                manager.create_user(
                    username="professor",
                    email="professor@university.edu",
                    password="ChangeMeASAP2024!",
                    full_name="Professor Account",
                    role="professor",
                )
                results.append("✓ Created professor account")
            except Exception as e:
                results.append(f"✗ Professor: {str(e)}")

            # Create student account
            try:
                manager.create_user(
                    username="sa9082",
                    email="sa9082@university.edu",
                    password="sa90822024",
                    full_name="Sachin Adlakha",
                    role="student",
                )
                results.append("✓ Created student account (sa9082)")
            except Exception as e:
                results.append(f"✗ Student: {str(e)}")

            # Create directories
            base_path = "server/projects/ide"
            if not os.path.exists(base_path):
                base_path = "projects/ide"

            directories = [
                os.path.join(base_path, "Local"),
                os.path.join(base_path, "Local", "professor"),
                os.path.join(base_path, "Local", "sa9082"),
                os.path.join(base_path, "Lecture Notes"),
                os.path.join(base_path, "Assignments"),
                os.path.join(base_path, "Tests"),
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                results.append(f"✓ Created directory: {directory}")

            self.write(
                json.dumps(
                    {
                        "status": "success",
                        "message": "Setup completed successfully",
                        "results": results,
                        "login_info": {
                            "professor": {"username": "professor", "password": "ChangeMeASAP2024!"},
                            "student": {"username": "sa9082", "password": "sa90822024"},
                        },
                    },
                    indent=2,
                )
            )

        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"status": "error", "message": str(e)}))


class ResetDatabaseHandler(tornado.web.RequestHandler):
    def get(self):
        """Reset database - drops and recreates all tables"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                logger.info("Resetting database...")

                # Drop all tables
                cursor.execute("DROP TABLE IF EXISTS file_submissions CASCADE")
                cursor.execute("DROP TABLE IF EXISTS files CASCADE")
                cursor.execute("DROP TABLE IF EXISTS sessions CASCADE")
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")

                # Recreate tables with correct schema
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

                conn.commit()

                # Now create default users
                manager = UserManager()

                manager.create_user(
                    username="professor",
                    email="professor@university.edu",
                    password="ChangeMeASAP2024!",
                    full_name="Professor Account",
                    role="professor",
                )

                manager.create_user(
                    username="sa9082",
                    email="sa9082@university.edu",
                    password="sa90822024",
                    full_name="Sachin Adlakha",
                    role="student",
                )

                self.write(
                    json.dumps(
                        {
                            "status": "success",
                            "message": "Database reset and users created successfully",
                            "login_info": {
                                "professor": {"username": "professor", "password": "ChangeMeASAP2024!"},
                                "student": {"username": "sa9082", "password": "sa90822024"},
                            },
                        },
                        indent=2,
                    )
                )

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            self.set_status(500)
            self.write(json.dumps({"status": "error", "message": str(e)}))
