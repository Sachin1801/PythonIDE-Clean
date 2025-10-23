#!/usr/bin/env python3
"""
Initialize exam users with random passwords
Creates exam_{netid} accounts for mid-term examination
"""
import os
import sys
import psycopg2
import bcrypt
import random
import string
from datetime import datetime
import csv


def generate_random_password(length=5):
    """Generate a random 5-character password (lowercase alphanumeric)"""
    # Use lowercase letters and digits (avoid ambiguous characters like 0,o,1,l)
    chars = 'abcdefghjklmnpqrstuvwxyz23456789'
    return ''.join(random.choice(chars) for _ in range(length))


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_exam_users(reset_existing=False):
    """Initialize exam users from CSV file"""
    print("=== EXAM USER INITIALIZATION STARTED ===")

    try:
        # Get database URL from environment (same var as main server)
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("DATABASE_URL not set!")
            print("Please set: export DATABASE_URL='postgresql://user:pass@host:port/pythonide_exam'")
            return

        print(f"Connecting to exam database...")

        # Parse the database URL
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/(.+)", db_url)
        if not match:
            print("Invalid DATABASE_URL format")
            return

        user, password, host, port, database = match.groups()
        port = port or "5432"

        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        # Reset existing users if requested
        if reset_existing:
            print("Clearing existing users...")
            cursor.execute("DELETE FROM users")
            conn.commit()

        # Read credentials from CSV file
        admin_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adminData")
        csv_path = os.path.join(admin_data_dir, "exam_credentials_LATEST.csv")

        if not os.path.exists(csv_path):
            print(f"ERROR: Credentials file not found at {csv_path}")
            return

        print(f"Reading credentials from: {csv_path}")

        # Create exam users from CSV
        created_students = 0
        created_admins = 0

        with open(csv_path, 'r', newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)

            for row in csvreader:
                username = row['Username'].strip()
                password = row['Password'].strip()
                full_name = row['Full Name'].strip()
                netid = row['NetID'].strip()

                # Skip empty rows
                if not username or not password:
                    continue

                email = f"{username}@college.edu"
                password_hash = hash_password(password)

                # Determine role: professors/admins vs students
                # Admin accounts: sa9082, et2434, sl7927, admin_editor, dpp9951
                admin_netids = ['sa9082', 'et2434', 'sl7927', 'admin_editor', 'dpp9951']
                role = "professor" if netid in admin_netids else "student"

                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (username) DO UPDATE SET
                            email = EXCLUDED.email,
                            password_hash = EXCLUDED.password_hash,
                            full_name = EXCLUDED.full_name,
                            role = EXCLUDED.role
                    """, (username, email, password_hash, full_name, role))

                    print(f"Created {role}: {username} ({full_name}) - Password: {password}")

                    if role == "professor":
                        created_admins += 1
                    else:
                        created_students += 1

                except Exception as e:
                    print(f"Error creating {username}: {e}")

        conn.commit()

        # Verify - count all students and professors
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='professor'")
        prof_count = cursor.fetchone()[0]

        print(f"\n✅ Exam user initialization complete!")
        print(f"Total student accounts: {student_count} ({created_students} processed)")
        print(f"Total professor/admin accounts: {prof_count} ({created_admins} processed)")
        print(f"Credentials source: {csv_path}")
        print("\n⚠️  IMPORTANT: All passwords are from exam_credentials_LATEST.csv")

        cursor.close()
        conn.close()

        # Create directories on EFS
        create_exam_directories()

    except Exception as e:
        print(f"ERROR during exam user initialization: {e}")
        import traceback
        traceback.print_exc()


def create_exam_directories():
    """Create directories on EFS for exam users"""
    try:
        # Determine the base path for EXAM environment
        # Prioritize IDE_DATA_PATH (set in Docker), then check for EFS, then fallback to /tmp
        if "IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["IDE_DATA_PATH"], "ide", "Local")
        elif os.path.exists("/mnt/efs/pythonide-data-exam"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
        else:
            base_path = "/tmp/pythonide-data-exam/ide/Local"

        print(f"\nCreating exam directories at: {base_path}")

        # Create base Local directory only (no Example folder needed)
        os.makedirs(base_path, exist_ok=True)
        

        # Read usernames from CSV file
        admin_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "adminData")
        csv_path = os.path.join(admin_data_dir, "exam_credentials_LATEST.csv")

        exam_usernames = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', newline='') as csvfile:
                csvreader = csv.DictReader(csvfile)
                for row in csvreader:
                    username = row['Username'].strip()
                    if username:
                        exam_usernames.append(username)
            print(f"Found {len(exam_usernames)} exam accounts from CSV")
        else:
            print(f"WARNING: CSV file not found at {csv_path}, skipping directory creation")
            return

        # Create directories for each exam user
        for username in exam_usernames:
            user_dir = os.path.join(base_path, username)
            os.makedirs(user_dir, exist_ok=True)

            # Create welcome file for exam environment
            words_file = os.path.join(user_dir,"words.py")
            with open(words_file,"w") as f:
                f.write("""words = (
    "elephant",
    "beautiful",
    "conversation",
    "university",
    "imagination",
    "celebration",
    "important",
    "responsible",
    "fantastic",
    "adventure",
    "environment",
    "intelligent",
    "discovery",
    "magnificent",
    "population",
    "operation",
    "creativity",
    "electricity",
    "definition",
    "application",
    "communication",
    "generation",
    "information",
    "motivation",
    "organization",
    "delicious",
    "appreciation",
    "opportunity",
    "circumstance",
    "announcement"
)""")
            
            print(f"Created words.py for : {username}")
            
            
            names_file = os.path.join(user_dir,"names.py")
            with open(names_file,"w") as f:
                f.write("""names = (
    "Aaliyah",      # Arabic
    "Sofia",        # Spanish / Greek
    "Mei",          # Chinese
    "Amara",        # Igbo (Nigerian) / Sanskrit
    "Elena",        # Italian / Greek
    "Priya",        # Indian (Sanskrit)
    "Nora",         # Arabic / Irish
    "Yara",         # Arabic / Brazilian
    "Keiko",        # Japanese
    "Anastasia",    # Russian / Greek
    "Layla",        # Arabic
    "Chioma",       # Igbo (Nigerian)
    "Ines",         # Portuguese / Spanish
    "Zainab",       # Arabic
    "Lucía",        # Spanish
    "Maya",         # Hebrew / Sanskrit
    "Evelina",      # Swedish / Latin
    "Amina",        # Arabic / Swahili
    "Harper",       # English
    "Carmen",       # Spanish
    "Sakura",       # Japanese
    "Fatima",       # Arabic / Portuguese
    "Isabella",     # Italian / Hebrew
    "Chloe",        # Greek / English
    "Tahlia",       # Hebrew / Australian
    "Nalani",       # Hawaiian
    "Gianna",       # Italian
    "Noor",         # Arabic
    "Amelia",       # French
    "Zuri"          # Swahili)
)""")
            
            print(f"Created names.py for : {username}")
            
            nums_file = os.path.join(user_dir,"nums.py")
            with open(nums_file,"w") as f:
                f.write("""nums = (
    True,
    3.14,
    "27",
    108,
    0.001,
    "56.7",
    999,
    7.5,
    "1000",
    64,
    12.75,
    "3.14159",
    81,
    2.718,
    "450",
    2048,
    6.022e23,
    "0.0001",
    73,
    19.99,
    "2500",
    8,
    0.5,
    "123456",
    31,
    9.81,
    "42",
    100,
    4.44,
    "0"
)""")
            
            print(f"Created nums.py for : {username}")


            passwords_file = os.path.join(user_dir,"password.py")
            with open(passwords_file,"w") as f:
                f.write("""passwords = ('VA8]RrM}#>', ':tX:IH61k', '%S8', '.?60?u:B9', 'K%%;22eoiL', '&C4', 'K8?', 'NIa5@(:l:0', 'U!<G{6<[KX', '9w?&+Vw', 'q{LHP91:', '*IW1Fl', '_(5T', '9)(+Jzz7&', 'jIhU2}', 'Nu9[2AvhM', ']aHy1v_q@h', 'C/3', '%y%6=', 'Wt{9D', '/8,Y1', '0jB]fK2?oO', '<yS35V', '!C/1b#', '!A6a', '$0h', 'LD5nw1Q3a]', 'Z3n}#=d', '7/tKL', 'n<z2', 'BN(c+]!8c', 'A3-x', '2V$', 'j)A8K', '06;<W', 'rT?0K', 'J6Y{$TVC&', 'F:P2qAb%', '^3z', ',}M0Yd', '}Q7&*>', 'Gc3CV:o', '7^=xl', 'u1$UY', ')BYlT+3QV', '.u{>Qx;OQ3', '1hf&GxUh', 'Z=?9#*ed', '4W#', '<69Y4l3^', ')fkt4', '1&u}', '%1B($4bDHC', '08U18>L', '&92-VB^au', '!w2<', 'ZYYOOL%4', '8(9fSkI=w', '#2R0xNX2v', '<:5stQhM', ')gY+0', '?7d', 'Dr,9^r,Sq', '+!1Ev$', '5kU^(', '$2wLxyJ+#k', '[N9aBje=', '1?R', '0}@o', '{IiBS7[', 'e8:;', '6Z^', '7*n', 'mxp]M3;zR', 'Q*]HvR5', 'b[R3', '+IU0$sqt', '27$<m:IS', 'e>3j@22}', '6p?r+9', '?<94a', 'EN96p#3Q}', 'j2^?', 'J[4K', 'z78OW.NHZ', '[3DM]]A*', '77<X', '2:wN>f', 'ZI_5jX@k', 'E(.cB9', 'U4+', 'YP0o^aQ', 'fr3l,', 'E56by+3', 'X2$.[Aq', 'Ni(KTJ7e[', '_!H3/', 'f4JtqG?W', 'XdVNh}5U', 'AL1&?pa+3y', '%4&Mt', 'd4)Ra', 'B5q+h', 'qz5+$*$<9q', '!lop,7Xy', '>&1D', 'tv3g^G', '3f&', 'I0&t', '9#8WNX', 'S!85Ge=e', 'bM1,', 'e{hPY9,A', 'Y<t{xj5', '6oQ:z5)w', '-,.N*YX^7', 'O0C!*k', 'V9fq*', '7,-}%8Hmfn', 'bxW&6!+L%_', '7o)', 'r4_Qm', 'U(7H+K-#$n', '6o$', 'X7;:*5&F<', '4r@#n2Euc1', '#6X', 'q2^', '=3W(N', 'A9<YBR7)%<', '@l^[3', 'XVa7{81^03', 'r9{', ';4r', 'R>$!%gb1M', 'm<D7_h=Nj', '0RUU1)^r.E', 'Y*[4', 'X=v(6r8)', '*JsNX>Be@7', '_1t-G}%9w3', 'c(1n8+kX2!', 'HS12=', '6@@GZ!', 'P%0', 'T8#E&r3.', '#bl(B5=W', 'dqu1;fb', 'E^z4', '.0ZRd', 'x8TI/!(V@', '$*Z86Mj.', 'z[xD$5', 'h<a.o:o2', '$T3', '77!b', '>d9', '!y9', 'JV*1', '7f,c', '$OzGm:6', '8k[', '4a{', 'Fc1-a?', 'y0z(', '(x5', '{,=Bd0&', 'Or%1%', '?<3i', 'F1Dj7qjSv!', 'T=gR%{}d6', '$;^R(t6J4', ')T2', '<2h/z@SI)', 'R]u-1+e{', 'rU6+', 'C7o:T]C', 'Rf1+', 'rLTFU-?$<1', '0k(8%cjF', 'M>5,,', '1S%0lTwR', '(7ji!fR', '&y1Pf{IT', 's9pku.$$', 'c16?', 'rLR8A]T', '$R1?dl[vm', 'J>_Jc7', 'X4:a5];nK3', '}d7*', 'D34_?_Q1Me', '-l1-+UH', '&co-1', '8&d<x', 'Xn8;L}($', 'p8@^%X8X', 'EyX1>', '_&LKz:Q1', 'M2?<XnWj', ':4Dxi])', '=0IE', '-}bO38F', 'h9y1*ar', '*JKLLQt4', '8<S_%m[4U.', 'T0-nZ', '}:Lk9[P!N', '_6QA', '+3W', '6[rRF:[6G', 'J{97RL?.^', 'd+y9?k*Zzh', 'b=q8', '7G4D+)K,', 'wY*.&3', 'RjD.9L%?T', '7HR/1', ',b4]Oq', ':sE7', '4;2I2+', 'y9/', '[i4', '9J9m&', 'm<,fmb08n', '8({RY', 'jBr8t5#', 'C3V!?6H', 'i;q,Ak2,', 'C+J9', 'yjq3h(', 'SCZ;e33!', '8_kB:Ej3.M', '#tP3y^#', ')#B7', 'VdW>9pE', 'Nz1w%M<Ug', 'sD4>T(', '9eK*vj!nK', '9X>', 'TPw]V6zgW', '3/t', '<3aXkyJb', 'm^8&L0', 'G$:P2', '<}MfL+1', 'uq/#bm@17', '8YI,t<X3=h', 'cNN5{]', 'H&t6R')""")
            
            print(f"Created password.py for : {username}")

            items_file = os.path.join(user_dir,"items.py")
            with open(items_file,"w") as f:
                f.write("""items = (
    ("Kirkland Signature Almonds 3lb", 12.99),
    ("Organic Peanut Butter 2pk", 9.97),
    ("Rotisserie Chicken", 4.99),
    ("Toilet Paper 30 Rolls", 22.99),
    ("Kirkland Organic Eggs 24ct", 6.97),
    ("Kirkland Ground Beef 5lb", 19.00),
    ("Avocados 6ct", 8.88),
    ("Organic Strawberries 2lb", 7.99),
    ("Kirkland Olive Oil 2L", 15.97),
    ("Salmon Fillet 2lb", 24.99),
    ("Kirkland Greek Yogurt 48oz", 5.79),
    ("Frozen Pizza 4pk", 11.97),
    ("Laundry Detergent 200oz", 17.99),
    ("Paper Towels 12pk", 23.97),
    ("Protein Bars 20ct", 16.49),
    ("Organic Milk 3pk", 11.99),
    ("Kirkland Mixed Nuts 2.5lb", 14.97),
    ("Organic Spinach 1lb", 4.99),
    ("Bagels 2pk", 6.99),
    ("Kirkland Chicken Breasts 10lb", 27.00),
    ("Rice 25lb", 17.88),
    ("Kirkland Coffee 3lb", 12.99),
    ("Organic Honey 3lb", 13.97),
    ("Kirkland Maple Syrup 1L", 11.99),
    ("Pasta 6pk", 8.79),
    ("Kirkland Trail Mix 4lb", 16.97),
    ("Organic Quinoa 4.5lb", 10.97),
    ("Frozen Berries 4lb", 11.99),
    ("Kirkland Bacon 4pk", 15.97),
    ("Kirkland Laundry Pods 120ct", 21.99),
    ("Dog Food 40lb", 49.97),
    ("Cat Litter 42lb", 17.00),
    ("Water 40pk", 4.99),
    ("Kirkland Almond Butter 27oz", 8.88),
    ("Kirkland Tuna 8pk", 14.97),
    ("Organic Chicken Broth 6pk", 11.99),
    ("Kirkland Coconut Water 12pk", 15.79),
    ("Kirkland Toilet Cleaner 2pk", 7.97),
    ("Kirkland Shampoo 1L", 10.99),
    ("Kirkland Conditioner 1L", 10.99),
    ("Dishwasher Tabs 115ct", 16.97),
    ("Paper Plates 200ct", 14.97),
    ("Plastic Cups 240ct", 13.99),
    ("Kirkland Facial Tissues 12pk", 17.97),
    ("Trash Bags 200ct", 19.99),
    ("Kirkland Salmon Oil 400ct", 24.97),
    ("Kirkland Multivitamins 500ct", 15.97),
    ("Protein Powder 6lb", 39.99),
    ("Toothpaste 5pk", 12.97),
    ("Toothbrushes 8pk", 9.97),
    ("Kirkland Paper Towels 12pk", 23.99),
    ("Organic Apples 5lb", 9.97),
    ("Bananas 3lb", 1.99),
    ("Oranges 8lb", 8.99),
    ("Kirkland Cereal 2pk", 7.97),
    ("Canned Tomatoes 8pk", 10.97),
    ("Kirkland Laundry Booster 4kg", 13.00),
    ("Organic Brown Rice 12lb", 15.88),
    ("Kirkland Parmesan Cheese 1lb", 9.97),
    ("Mozzarella Cheese 2lb", 12.99),
    ("Kirkland Ice Cream Bars 18ct", 10.97),
    ("Organic Chicken Thighs 5lb", 16.97),
    ("Frozen French Fries 10lb", 8.99),
    ("Kirkland Frozen Shrimp 2lb", 18.97),
    ("Kirkland Vitamin D 600ct", 12.97),
    ("Kirkland Fish Oil 400ct", 14.97),
    ("Paper Napkins 12pk", 9.99),
    ("Kirkland Green Tea 100ct", 11.97),
    ("Organic Oats 10lb", 13.79),
    ("Kirkland Almond Flour 3lb", 13.97),
    ("Kirkland Cashews 2.5lb", 14.97),
    ("Kirkland Pistachios 3lb", 18.99),
    ("Kirkland Laundry Softener 5L", 11.97),
    ("Organic Peanut Butter Cups", 9.97),
    ("Kirkland Energy Drinks 24pk", 27.99),
    ("Kirkland Protein Shakes 18pk", 32.97),
    ("Kirkland Vitamins C 500ct", 11.99),
    ("Kirkland Melatonin 300ct", 8.97),
    ("Kirkland Ibuprofen 500ct", 9.99),
    ("Kirkland Naproxen 400ct", 12.97),
    ("Kirkland Contact Lens Solution 3pk", 13.97),
    ("Kirkland Body Wash 2pk", 10.99),
    ("Kirkland Hand Soap 2pk", 9.97),
    ("Kirkland Dish Soap 3L", 11.99),
    ("Kirkland Sponges 24ct", 13.97),
    ("Kirkland Kitchen Towels 12pk", 24.97),
    ("Kirkland Mop Refill 6pk", 17.88),
    ("Kirkland Vacuum Bags 8ct", 15.97),
    ("Kirkland Batteries AA 48ct", 18.99),
    ("Kirkland Batteries AAA 48ct", 18.99),
    ("Kirkland Batteries C 24ct", 17.97),
    ("Kirkland Batteries D 24ct", 19.97),
    ("Kirkland Batteries 9V 8ct", 13.00),
    ("Kirkland Wine Cabernet 750ml", 11.97),
    ("Kirkland Wine Chardonnay 750ml", 8.97),
    ("Kirkland Beer 24pk", 23.99),
    ("Kirkland Vodka 1.75L", 19.99),
    ("Kirkland Whiskey 1.75L", 28.97),
    ("Kirkland Tequila 1.75L", 33.97),
    ("Kirkland Rum 1.75L", 18.88),
    ("Kirkland Gin 1.75L", 17.00),
    ("Kirkland Organic Coconut Oil 84oz", 16.97),
    ("Kirkland Almond Milk 6pk", 9.99),
    ("Kirkland Cheese Sticks 48ct", 13.97),
    ("Kirkland Snack Mix 30ct", 14.97),
    ("Kirkland Trail Mix Bars 36ct", 16.99),
    ("Kirkland Fruit Snacks 90ct", 15.97),
    ("Kirkland Gummies 5lb", 8.97),
    ("Kirkland Popcorn 44pk", 13.79),
    ("Kirkland Chips Variety 54ct", 17.97),
    ("Kirkland Crackers 4pk", 9.97),
    ("Kirkland Soup Variety 8pk", 14.97),
    ("Kirkland Frozen Burgers 15ct", 23.97),
    ("Kirkland Chicken Nuggets 5lb", 15.99),
    ("Kirkland Veggie Burgers 12ct", 12.97),
    ("Kirkland Butter 4lb", 13.97),
    ("Kirkland Eggs 60ct", 12.88),
    ("Kirkland Sugar 10lb", 8.97),
    ("Kirkland Salt 3pk", 4.99),
    ("Kirkland Pepper Grinder 2pk", 7.97),
    ("Kirkland Baking Soda 13.5lb", 9.97),
    ("Kirkland Bleach 2pk", 8.79),
    ("Kirkland Disinfecting Wipes 4pk", 14.97),
    ("Kirkland Batteries Button 12ct", 10.97),
    ("Kirkland Paper Towels 18pk", 25.97),
    ("Kirkland Trash Bags 90ct", 14.97),
    ("Kirkland Laundry Pods 150ct", 27.99),
    ("Kirkland Pet Treats 2lb", 11.97),
    ("Kirkland Dog Biscuits 15lb", 18.97),
    ("Kirkland Cat Food 25lb", 23.99),
    ("Kirkland Chicken Jerky 2.5lb", 19.97),
    ("Kirkland Cat Treats 1.5lb", 8.88),
    ("Kirkland Wet Dog Food 24pk", 27.97),
    ("Kirkland Coffee Pods 120ct", 36.97),
    ("Kirkland Coffee Beans 2lb", 11.97),
    ("Kirkland Decaf Coffee 3lb", 14.97),
    ("Kirkland French Roast 3lb", 12.99),
    ("Kirkland Hazelnut Coffee 2lb", 13.97),
    ("Kirkland Colombian Coffee 3lb", 14.97),
    ("Kirkland Organic Tea 120ct", 10.97),
    ("Kirkland Organic Sugar 10lb", 9.97),
    ("Kirkland Cocoa Powder 2lb", 8.97),
    ("Kirkland Granola 2.5lb", 11.99),
    ("Kirkland Raisins 4lb", 10.97),
    ("Kirkland Dried Mango 2lb", 12.97),
    ("Kirkland Jerky 12oz", 13.99),
    ("Kirkland Apple Juice 2pk", 8.97),
    ("Kirkland Orange Juice 2pk", 9.97),
    ("Kirkland Sports Drink 24pk", 14.97),
    ("Kirkland Sparkling Water 35pk", 13.99),
    ("Kirkland Vitamins E 400ct", 12.97),
    ("Kirkland Zinc 500ct", 11.97),
    ("Kirkland Vitamin B12 600ct", 13.97),
    ("Kirkland Omega 3 400ct", 14.97),
    ("Kirkland Glucosamine 375ct", 17.97),
    ("Kirkland Calcium 500ct", 11.97),
    ("Kirkland Multivitamin Gummies", 14.97),
    ("Kirkland Protein Cookies 12ct", 11.97),
    ("Kirkland Protein Chips 24ct", 18.97),
    ("Kirkland Granola Bars 64ct", 16.97),
    ("Kirkland Applesauce 36ct", 13.99),
    ("Kirkland Peanut Butter 2pk", 8.97),
    ("Kirkland Jelly 2pk", 7.97),
    ("Kirkland Bread 2pk", 6.99),
    ("Kirkland Croissants 12ct", 6.97),
    ("Kirkland Muffins 12ct", 9.99),
    ("Kirkland Bagels 12ct", 7.99),
    ("Kirkland Cheesecake 2lb", 14.97),
    ("Kirkland Cookies 24ct", 10.97),
    ("Kirkland Brownies 12ct", 9.97),
    ("Kirkland Donuts 18ct", 8.88),
    ("Kirkland Cupcakes 12ct", 11.97),
    ("Kirkland Birthday Cake 3lb", 16.97),
    ("Kirkland Ice Cream 1.5qt", 7.99),
    ("Kirkland Frozen Yogurt 4ct", 10.97),
    ("Kirkland Pizza Rolls 120ct", 13.97),
    ("Kirkland Cheese Pizza 4pk", 11.97),
    ("Kirkland Pepperoni Pizza 4pk", 12.99),
    ("Kirkland Frozen Lasagna 2pk", 14.97),
    ("Kirkland Frozen Meatballs 6lb", 19.97),
    ("Kirkland Frozen Chicken Wings 5lb", 18.97),
    ("Kirkland Tacos 12ct", 15.97),
    ("Kirkland Burritos 12ct", 16.97),
    ("Kirkland Tamales 20ct", 19.00),
    ("Kirkland Soup Bowls 12ct", 14.97)
)
""")
            
            print(f"Created items.py for : {username}")

            # Create welcome file for exam environment
            welcome_file = os.path.join(user_dir, "welcome.py")
            with open(welcome_file, "w") as f:
                f.write("""# Welcome to the Exam IDE Environment
# This is your isolated workspace for examinations.
# Only you and the instructors can access files in this directory.

print("Welcome to the Exam IDE!")
print("This environment is isolated and secure.")
print("You can write and test your Python code here.")
print("Good luck on your exam!")
""")

            print(f"Created welcome.py for : {username}")
            print(f"✓ Created exam directory for: {username}")

        print("✅ All exam directories created")

    except Exception as e:
        print(f"Error creating exam directories: {e}")


def reset_exam_files():
    """Reset exam files before the actual exam (run this right before exam)"""
    print("=== RESETTING EXAM FILES FOR ACTUAL EXAM ===")

    try:
        if os.path.exists("/mnt/efs"):
            base_path = "/mnt/efs/pythonide-data-exam/ide/Local"
        elif "EXAM_IDE_DATA_PATH" in os.environ:
            base_path = os.path.join(os.environ["EXAM_IDE_DATA_PATH"], "ide", "Local")
        else:
            base_path = "/tmp/pythonide-data-exam/ide/Local"

        # Get actual exam questions from a file (you'll create this)
        exam_content = """# Mid-Term Exam - ACTUAL QUESTIONS
# Name: {username}
# Date: {date}
# Time Limit: 75 minutes

# INSTRUCTIONS:
# - Complete all functions below
# - You may NOT use external resources
# - Test your code before submission
# - Save your work frequently (Ctrl+S)

# Question 1 (20 points): String Manipulation
def reverse_words(sentence):
    '''
    Given a sentence, reverse each word individually.
    Example: "Hello World" -> "olleH dlroW"
    '''
    pass

# Question 2 (25 points): List Processing
def find_duplicates(lst):
    '''
    Find all duplicate elements in a list.
    Return a list of duplicates (no repetition).
    Example: [1,2,3,2,4,3] -> [2,3]
    '''
    pass

# Question 3 (25 points): Dictionary Operations
def merge_inventories(inv1, inv2):
    '''
    Merge two inventory dictionaries by adding quantities.
    Example: {'apple': 5}, {'apple': 3, 'banana': 2} -> {'apple': 8, 'banana': 2}
    '''
    pass

# Question 4 (30 points): File Handling
def process_scores(filename):
    '''
    Read a file with student scores (name,score per line).
    Return the average score and the highest scorer's name.
    '''
    pass

# TEST YOUR FUNCTIONS HERE:
# print(reverse_words("Hello World"))
# print(find_duplicates([1,2,3,2,4,3]))
# print(merge_inventories({'apple': 5}, {'apple': 3, 'banana': 2}))
"""

        # Reset each student's exam file
        import glob
        from datetime import datetime

        for user_dir in glob.glob(os.path.join(base_path, "exam_*")):
            username = os.path.basename(user_dir)
            exam_file = os.path.join(user_dir, "midterm_exam.py")

            # Clear any other files (keep directory clean)
            for file in glob.glob(os.path.join(user_dir, "*")):
                if file != exam_file:
                    os.remove(file)

            # Write the actual exam content
            with open(exam_file, "w") as f:
                f.write(exam_content.format(
                    username=username,
                    date=datetime.now().strftime("%Y-%m-%d")
                ))

            print(f"Reset exam file for: {username}")

        print("✅ All exam files reset for actual exam")

    except Exception as e:
        print(f"Error resetting exam files: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Manage exam users')
    parser.add_argument('--reset', action='store_true', help='Reset existing exam users')
    parser.add_argument('--reset-files', action='store_true', help='Reset exam files for actual exam')

    args = parser.parse_args()

    if args.reset_files:
        reset_exam_files()
    else:
        init_exam_users(reset_existing=args.reset)