#!/usr/bin/env python3
"""Initialize PostgreSQL with test users"""

import os
import sys
import psycopg2
from urllib.parse import urlparse
import bcrypt

# Get DATABASE_URL from environment or command line
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL and len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

if not DATABASE_URL:
    print("Usage: python init_postgres_users.py <DATABASE_URL>")
    print("Or set DATABASE_URL environment variable")
    sys.exit(1)

# Parse database URL
url = urlparse(DATABASE_URL)
conn = psycopg2.connect(
    host=url.hostname,
    port=url.port or 5432,
    database=url.path[1:],
    user=url.username,
    password=url.password
)

cursor = conn.cursor()

# Create test users
test_users = [
    ('professor', 'prof123', 'professor'),
    ('sa9082', 'student123', 'student'),
    ('jd1234', 'student123', 'student'),
    ('student1', 'test123', 'student'),
    ('student2', 'test123', 'student'),
]

for username, password, role in test_users:
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (username, password_hash, role)
        )
        print(f"Created user: {username} (role: {role})")
    except Exception as e:
        print(f"Error creating {username}: {e}")

conn.commit()
cursor.close()
conn.close()

print("\nTest users created!")
print("Login credentials:")
print("  Professor: professor / prof123")
print("  Students: sa9082 / student123")
print("           jd1234 / student123")