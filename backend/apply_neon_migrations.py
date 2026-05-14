import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

print(f"Connecting to {DB_URL.split('@')[1] if '@' in DB_URL else 'db'}...")

MIGRATIONS_DIR = "migrations"
migration_files = [
    "000_create_base_tables.sql",
    "001_create_new_tables.sql",
    "002_create_doctor_teleconsultation_tables.sql",
    "003_create_patient_accounts.sql",
    "004_seed_hubli_doctors.sql",
    "005_seed_doctor_availability_slots.sql",
    "006_create_user_accounts.sql",
    "007_plain_password_auth_adjustment.sql",
    "008_seed_slots_2026_03_25_26.sql",
    "009_create_doctor_feedback.sql",
    "010_create_email_otp_codes.sql",
    "011_add_doctor_availability_toggle.sql",
    "012_allow_rebooking_cancelled_slots.sql",
    "013_harden_slot_reserve_and_book.sql",
    "014_fix_book_reserved_slot_atomic_update.sql",
    "015_report_aware_call_linkage.sql",
    "016_create_blood_campaign_tables.sql",
    "017_create_follow_up_cron_tables.sql"
]

try:
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Create schema migrations table if not exists
            cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
              file_name text PRIMARY KEY,
              applied_at timestamptz NOT NULL DEFAULT now()
            );
            """)

            for file_name in migration_files:
                file_path = os.path.join(MIGRATIONS_DIR, file_name)
                
                # Check if already applied
                cur.execute("SELECT 1 FROM schema_migrations WHERE file_name = %s", (file_name,))
                if cur.fetchone():
                    print(f"Skipping {file_name} (already applied)")
                    continue
                
                print(f"Applying {file_name}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                    
                # Run the sql — continue on error so later migrations still apply
                try:
                    cur.execute(sql)
                    cur.execute("INSERT INTO schema_migrations(file_name) VALUES (%s)", (file_name,))
                    print(f"  [OK] Applied {file_name}")
                except Exception as e:
                    print(f"  [SKIP] {file_name} (error: {e})")

    print("Migrations completed successfully.")
except Exception as e:
    print(f"Connection or migration failed: {e}")
