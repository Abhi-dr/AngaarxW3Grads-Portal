import sys
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fixes MySQL M2M and FK constraints after migrating from auth.User to accounts_customuser'

    def handle(self, *args, **options):
        self.stdout.write("Starting MySQL schema alignment for CustomUser migration...\n")

        with connection.cursor() as cursor:

            # ──────────────────────────────────────────────────────────────────
            # STEP 1: Copy missing users from auth_user → accounts_customuser
            # This is required before FK rewiring because child tables (like
            # account_emailaddress, django_admin_log) reference user IDs that
            # must exist in accounts_customuser for the FK to be created.
            # ──────────────────────────────────────────────────────────────────
            cursor.execute("SHOW TABLES LIKE 'auth_user'")
            if not cursor.fetchone():
                self.stdout.write("  -> 'auth_user' table not found. Skipping user copy step.")
            else:
                cursor.execute("""
                    SELECT id FROM auth_user
                    WHERE id NOT IN (SELECT id FROM accounts_customuser)
                """)
                missing_ids = [row[0] for row in cursor.fetchall()]

                if missing_ids:
                    self.stdout.write(f"Found {len(missing_ids)} user(s) in auth_user missing from accounts_customuser. Copying them...")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

                    seen_emails = set()
                    seen_usernames = set()

                    # Fetch existing emails/usernames to avoid conflicts
                    cursor.execute("SELECT email FROM accounts_customuser")
                    seen_emails = {row[0] for row in cursor.fetchall()}
                    cursor.execute("SELECT username FROM accounts_customuser")
                    seen_usernames = {row[0] for row in cursor.fetchall()}

                    for uid in missing_ids:
                        cursor.execute("""
                            SELECT au.password, au.last_login, au.is_superuser, au.username,
                                   au.first_name, au.last_name, au.email, au.is_staff, au.is_active,
                                   au.date_joined,
                                   CASE WHEN ai.user_ptr_id IS NOT NULL THEN 'instructor'
                                        WHEN aa.user_ptr_id IS NOT NULL THEN 'admin'
                                        ELSE 'student' END AS role,
                                   COALESCE(s.mobile_number, '-') AS mobile_number,
                                   COALESCE(s.gender, COALESCE(ai.gender, COALESCE(aa.gender, 'Not Set'))) AS gender,
                                   COALESCE(s.college, COALESCE(ai.college, aa.college)) AS college,
                                   COALESCE(s.dob, COALESCE(ai.dob, aa.dob)) AS dob,
                                   COALESCE(s.profile_pic, COALESCE(ai.profile_pic, COALESCE(aa.profile_pic, '/student_profile/default.jpg'))) AS profile_pic,
                                   COALESCE(s.linkedin_id, COALESCE(ai.linkedin_id, aa.linkedin_id)) AS linkedin_id,
                                   s.github_id AS github_id,
                                   COALESCE(s.coins, 100) AS coins,
                                   COALESCE(s.is_changed_password, FALSE) AS is_changed_password
                            FROM auth_user au
                            LEFT JOIN accounts_student s ON s.user_ptr_id = au.id
                            LEFT JOIN accounts_instructor ai ON ai.user_ptr_id = au.id
                            LEFT JOIN accounts_administrator aa ON aa.user_ptr_id = au.id
                            WHERE au.id = %s
                        """, [uid])
                        row = cursor.fetchone()
                        if not row:
                            continue

                        (password, last_login, is_superuser, username, first_name, last_name,
                         email, is_staff, is_active, date_joined, role, mobile_number,
                         gender, college, dob, profile_pic, linkedin_id, github_id,
                         coins, is_changed_password) = row

                        # Safe username
                        safe_username = (username or '').strip() or f'user_{uid}'
                        if safe_username in seen_usernames:
                            safe_username = f'{safe_username}_{uid}'
                        seen_usernames.add(safe_username)

                        # Safe email
                        safe_email = (email or '').strip() or f'noemail_{uid}@placeholder.invalid'
                        if safe_email in seen_emails:
                            safe_email = f'duplicate_{uid}@placeholder.invalid'
                        seen_emails.add(safe_email)

                        try:
                            cursor.execute("""
                                INSERT INTO accounts_customuser (
                                    id, password, last_login, is_superuser, username,
                                    first_name, last_name, email, is_staff, is_active,
                                    date_joined, role, mobile_number, gender, college,
                                    dob, profile_pic, linkedin_id, github_id, coins,
                                    is_changed_password, is_email_verified
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, [uid, password, last_login, is_superuser, safe_username,
                                  first_name, last_name, safe_email, is_staff, is_active,
                                  date_joined, role, mobile_number, gender, college,
                                  dob, profile_pic, linkedin_id, github_id, coins,
                                  is_changed_password, is_active])
                            self.stdout.write(self.style.SUCCESS(f"  -> Copied user {uid} ({safe_username}) as {role}"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  -> Skipped user {uid}: {e}"))

                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                else:
                    self.stdout.write("  -> accounts_customuser already has all auth_user rows. No copy needed.")

            # ──────────────────────────────────────────────────────────────────
            # STEP 2: Rename M2M columns to customuser_id
            # Each entry: (table, old_column_name)
            # ──────────────────────────────────────────────────────────────────
            m2m_renames = [
                ('home_article_likes', 'user_id'),
                ('home_flamescourse_instructor', 'user_id'),
                # student_course_instructors uses 'instructor_id' (not user_id)
                ('student_course_instructors', 'instructor_id'),
            ]
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for t, old_col in m2m_renames:
                try:
                    cursor.execute(f"SHOW COLUMNS FROM {t};")
                    cols = [row[0] for row in cursor.fetchall()]
                    if old_col in cols and 'customuser_id' not in cols:
                        self.stdout.write(f"Renaming '{old_col}' to 'customuser_id' in {t}...")
                        try:
                            cursor.execute(f"ALTER TABLE {t} CHANGE {old_col} customuser_id BIGINT NOT NULL;")
                            # Re-wire FK to accounts_customuser
                            new_fk = f"{t}_customuser_id_fk_customuser"[:64]
                            cursor.execute(f"ALTER TABLE {t} ADD CONSTRAINT {new_fk} FOREIGN KEY (customuser_id) REFERENCES accounts_customuser(id);")
                            self.stdout.write(self.style.SUCCESS(f"  -> Renamed and rewired to accounts_customuser"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  -> Failed: {e}"))
                    elif 'customuser_id' in cols:
                        self.stdout.write(f"  -> {t}.customuser_id already exists, skipping.")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Table {t} not found or error: {e}"))
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


            # ──────────────────────────────────────────────────────────────────
            # STEP 3: Rewire Built-in FK Constraints
            # ──────────────────────────────────────────────────────────────────
            query = """
            SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = 'auth_user';
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            tables_to_rewire = [
                'account_emailaddress',
                'django_admin_log',
                'home_article_likes',
                'home_comment',
                'home_flamesteam',
                'socialaccount_socialaccount'
            ]

            for row in rows:
                table_name, col_name, constraint_name = row[0], row[1], row[2]
                if table_name in tables_to_rewire:
                    self.stdout.write(f"Rewiring {table_name}.{col_name} (Constraint: {constraint_name})")
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {constraint_name};")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  -> Error dropping old FK: {e}"))

                    cursor.execute(f"SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table_name}' AND COLUMN_NAME='{col_name}';")
                    col_info = cursor.fetchone()
                    null_str = 'NULL' if col_info and col_info[0] == 'YES' else 'NOT NULL'

                    try:
                        cursor.execute(f"ALTER TABLE {table_name} MODIFY {col_name} BIGINT {null_str};")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  -> Error modifying column type: {e}"))

                    new_fk_name = f"{table_name}_{col_name}_fk_customuser"[:64]
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} ADD CONSTRAINT {new_fk_name} FOREIGN KEY ({col_name}) REFERENCES accounts_customuser(id);")
                        self.stdout.write(self.style.SUCCESS(f"  -> Successfully rewired constraint to accounts_customuser!"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  -> Error adding new FK: {e}"))

        self.stdout.write(self.style.SUCCESS("\nSchema alignment complete! Your production database is now synced."))
