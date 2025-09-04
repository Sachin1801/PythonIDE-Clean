#!/usr/bin/env python3
"""
Initialize users directly in AWS RDS
Run this after making RDS publicly accessible
"""
import psycopg2
import bcrypt

# AWS RDS Configuration
RDS_HOST = "pythonide-db.c1u6aa2mqwwf.us-east-2.rds.amazonaws.com"
RDS_PORT = 5432
RDS_DATABASE = "pythonide"
RDS_USERNAME = "pythonide_admin"
RDS_PASSWORD = "Sachinadlakha9082"

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_users():
    """Initialize all users in AWS RDS"""
    try:
        print(f"Connecting to AWS RDS at {RDS_HOST}...")
        conn = psycopg2.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            database=RDS_DATABASE,
            user=RDS_USERNAME,
            password=RDS_PASSWORD
        )
        cursor = conn.cursor()
        print("✓ Connected successfully!")
        
        # Create tables if they don't exist
        print("Creating tables...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
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
        
        conn.commit()
        print("✓ Tables created/verified")
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            response = input(f"Found {existing_count} existing users. Delete and recreate? (yes/no): ")
            if response.lower() == 'yes':
                cursor.execute("DELETE FROM users")
                conn.commit()
                print("✓ Existing users deleted")
            else:
                print("Keeping existing users")
                cursor.close()
                conn.close()
                return
        
        # Create admin users
        print("\nCreating admin users...")
        admins = [
            ('sl7927', 'Susan Liao', 'Admin@sl7927', 'professor'),
            ('sa9082', 'Sachin Adlakha', 'Admin@sa9082', 'professor'),
            ('et2434', 'Ethan Tan', 'Admin@et2434', 'professor')
        ]
        
        for username, full_name, password, role in admins:
            email = f"{username}@college.edu"
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE
                SET password_hash = EXCLUDED.password_hash,
                    full_name = EXCLUDED.full_name,
                    role = EXCLUDED.role
            ''', (username, email, password_hash, full_name, role))
            print(f"  ✓ Created admin: {username} ({full_name})")
        
        # Create student users
        print("\nCreating student users...")
        students = [
            ('sa8820', 'Syed Ahnaf Ul Ahsan', 'student@sa8820'),
            ('na3649', 'Nicole Akmetov', 'student@na3649'),
            ('ntb5594', 'Nabi Burns-Min', 'student@ntb5594'),
            ('hrb9324', 'Harry Byala', 'student@hrb9324'),
            ('nd2560', 'Nikita Drovin-skiy', 'student@nd2560'),
            ('ag11389', 'Adrian Garcia', 'student@ag11389'),
            ('arg9667', 'Aarav Gupta', 'student@arg9667'),
            ('lh4052', 'Liisa Hambazaza', 'student@lh4052'),
            ('jh9963', 'Justin Hu', 'student@jh9963'),
            ('ch5315', 'Rami Hu', 'student@ch5315'),
            ('wh2717', 'Weijie Huang', 'student@wh2717'),
            ('bsj5539', 'Maybelina J', 'student@bsj5539'),
            ('fk2248', 'Falisha Khan', 'student@fk2248'),
            ('nvk9963', 'Neil Khandelwal', 'student@nvk9963'),
            ('sil9056', 'Simon Levine', 'student@sil9056'),
            ('hl6459', 'Haoru Li', 'student@hl6459'),
            ('zl3894', 'Jenny Li', 'student@zl3894'),
            ('jom2045', 'Janell Magante', 'student@jom2045'),
            ('arm9283', 'Amelia Mappus', 'student@arm9283'),
            ('zm2525', 'Zhou Meng', 'student@zm2525'),
            ('im2420', 'Ishaan Mukherjee', 'student@im2420'),
            ('jn3143', 'Janvi Nagpal', 'student@jn3143'),
            ('jn9106', 'Jacob Nathan', 'student@jn9106'),
            ('djp10030', 'Darius Partovi', 'student@djp10030'),
            ('ap10062', 'Alexandar Pelletier', 'student@ap10062'),
            ('bap9618', 'Benjamin Piquet', 'student@bap9618'),
            ('fp2331', 'Federico Pirelli', 'student@fp2331'),
            ('srp8204', 'Shaina Pollak', 'student@srp8204'),
            ('agr8457', 'Alex Reber', 'student@agr8457'),
            ('shs9941', 'Suzie Sanford', 'student@shs9941'),
            ('as19217', 'Albert Sun', 'student@as19217'),
            ('mat9481', 'Mario Toscano', 'student@mat9481'),
            ('cw4715', 'Chun-Hsiang Wang', 'student@cw4715'),
            ('jw9248', 'Jingyuan Wang', 'student@jw9248'),
            ('sz4766', 'Shengbo Zhang', 'student@sz4766')
        ]
        
        for username, full_name, password in students:
            email = f"{username}@college.edu"
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE
                SET password_hash = EXCLUDED.password_hash,
                    full_name = EXCLUDED.full_name
            ''', (username, email, password_hash, full_name, 'student'))
            print(f"  ✓ Created student: {username}")
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'professor'")
        admin_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print(f"Created {admin_count} admin users")
        print(f"Created {student_count} student users")
        print(f"Total: {admin_count + student_count} users")
        print("="*60)
        
        print("\nYou can now test login at:")
        print("http://pythonide-alb-456687384.us-east-2.elb.amazonaws.com")
        print("\nTest credentials:")
        print("  Admin: sa9082 / Admin@sa9082")
        print("  Student: na3649 / student@na3649")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you've made RDS publicly accessible:")
        print("1. RDS Console → Select database → Modify")
        print("2. Set 'Public access' to Yes")
        print("3. Update security group to allow port 5432 from your IP")

if __name__ == "__main__":
    init_users()