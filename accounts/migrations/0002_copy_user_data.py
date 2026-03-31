# Migration 0002: Copy all users from auth_user → accounts_customuser
# Preserves auth_user.id (PK) exactly.
# Handles duplicate emails/blank usernames gracefully with placeholder values.
# This migration is reversible.

from django.db import migrations


def copy_users_to_customuser(apps, schema_editor):
    """
    INSERT all rows from auth_user + MTI shadow tables into accounts_customuser,
    preserving PKs exactly. Merges all fields from Student/Instructor/Administrator.
    Handles duplicate emails and blank usernames safely with placeholders.
    """
    # This migration contains MySQL-specific SQL (`SHOW TABLES`, `SET FOREIGN_KEY_CHECKS`)
    # and is not compatible with sqlite. For local/dev sqlite runs, we skip the data
    # copy and keep the custom user table empty (users can be created normally).
    if schema_editor.connection.vendor == "sqlite":
        print("\ninfo: sqlite backend detected; skipping MySQL-specific user copy migration.")
        return

    with schema_editor.connection.cursor() as cursor:
        # Prevent crash on fresh databases where auth_user was never created
        cursor.execute("SHOW TABLES LIKE 'auth_user'")
        if not cursor.fetchone():
            print("\ninfo: 'auth_user' table does not exist (fresh database). Skipping data copy.")
            return

        # Check existing rows (idempotency - don't insert if already done)
        cursor.execute("SELECT COUNT(*) FROM accounts_customuser")
        existing = cursor.fetchone()[0]
        if existing > 0:
            print(f"\ninfo: accounts_customuser already has {existing} rows - skipping copy.")
            return

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Fetch all users from auth_user with relevant MTI join data
        cursor.execute("""
            SELECT
                au.id,
                au.password,
                au.last_login,
                au.is_superuser,
                au.username,
                au.first_name,
                au.last_name,
                au.email,
                au.is_staff,
                au.is_active,
                au.date_joined,

                CASE
                    WHEN ai.user_ptr_id IS NOT NULL THEN 'instructor'
                    WHEN aa.user_ptr_id IS NOT NULL THEN 'admin'
                    ELSE 'student'
                END AS role,

                COALESCE(s.mobile_number, '-')                        AS mobile_number,
                COALESCE(s.gender,
                    COALESCE(ai.gender,
                        COALESCE(aa.gender, 'Not Set')))              AS gender,
                COALESCE(s.college,
                    COALESCE(ai.college, aa.college))                 AS college,
                COALESCE(s.dob,
                    COALESCE(ai.dob, aa.dob))                         AS dob,
                COALESCE(s.profile_pic,
                    COALESCE(ai.profile_pic,
                        COALESCE(aa.profile_pic,
                        '/student_profile/default.jpg')))             AS profile_pic,
                COALESCE(s.linkedin_id,
                    COALESCE(ai.linkedin_id, aa.linkedin_id))         AS linkedin_id,
                s.github_id                                           AS github_id,
                COALESCE(s.coins, 100)                                AS coins,
                COALESCE(s.is_changed_password, FALSE)                AS is_changed_password

            FROM auth_user au
            LEFT JOIN accounts_student      s  ON s.user_ptr_id  = au.id
            LEFT JOIN accounts_instructor   ai ON ai.user_ptr_id = au.id
            LEFT JOIN accounts_administrator aa ON aa.user_ptr_id = au.id
        """)
        all_users = cursor.fetchall()

        seen_emails = set()
        seen_usernames = set()
        inserted = 0
        skipped = 0

        for row in all_users:
            (uid, password, last_login, is_superuser, username, first_name, last_name,
             email, is_staff, is_active, date_joined, role, mobile_number, gender,
             college, dob, profile_pic, linkedin_id, github_id, coins, is_changed_password) = row

            # Handle blank/duplicate usernames
            safe_username = username.strip() if username and username.strip() else f'user_{uid}'
            if safe_username in seen_usernames:
                safe_username = f'{safe_username}_{uid}'
            seen_usernames.add(safe_username)

            # Handle blank/duplicate emails
            safe_email = email.strip() if email and email.strip() else f'noemail_{uid}@placeholder.invalid'
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
                inserted += 1
            except Exception as e:
                print(f"  Warning: Skipped user {uid} ({safe_username}): {e}")
                skipped += 1

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        print(f"\nSuccess: Copied {inserted} users to accounts_customuser ({skipped} skipped)")

        cursor.execute("SELECT role, COUNT(*) FROM accounts_customuser GROUP BY role")
        for role, count in cursor.fetchall():
            print(f"   {role}: {count}")


def reverse_copy(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor != "sqlite":
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DELETE FROM accounts_customuser")
        if schema_editor.connection.vendor != "sqlite":
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Reversed: accounts_customuser cleared.")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_users_to_customuser, reverse_copy),
    ]
