# Local Docker Test Accounts

These accounts are specifically for testing the **main IDE** on your local Docker setup (localhost:10086).

## Quick Setup

Run this command while your Docker containers are running:

```bash
docker exec pythonide-app python init_local_test_accounts.py
```

This will create/update local test accounts with simple passwords.

## Test Credentials

### Student Accounts (for testing student features)

| Username | Password | Full Name |
|----------|----------|-----------|
| **local_student1** | test123 | Local Test Student 1 |
| **local_student2** | test123 | Local Test Student 2 |
| **local_student3** | test123 | Local Test Student 3 |

### Professor Account (for testing admin features)

| Username | Password | Full Name |
|----------|----------|-----------|
| **local_prof** | prof123 | Local Test Professor |

## Access

- **URL**: http://localhost:10086
- **Database**: Local PostgreSQL (separate from production)
- **Storage**: Docker volume `pythonide-clean_user_files`

## Features

Each test account gets:
- Personal directory at `Local/{username}/`
- Sample `welcome.py` file
- Full access to IDE features
- Isolated from production accounts

## Notes

- These accounts use `.local` email domain to distinguish them from production
- Passwords are intentionally simple for easy local testing
- Safe to delete/recreate anytime without affecting production
- The script can be run multiple times (it updates existing accounts)

## Differences from Production

| Aspect | Local Test | Production (AWS) |
|--------|-----------|------------------|
| Database | Local PostgreSQL | AWS RDS |
| Port | 10086 | 80/443 via ALB |
| Accounts | `local_*` test accounts | Real student accounts |
| Storage | Docker volume | AWS EFS |
| Domain | `*.test.local` | `*.college.edu` |

## Production Accounts

The production accounts (from CSV file) like `sa8820`, `test_1`, etc. may also exist in your local database, but their passwords are complex and stored in the CSV file at:

```
adminData/docker_local_credentials_20251013_170659.csv
```

**Use the `local_*` accounts for easy testing instead!**
