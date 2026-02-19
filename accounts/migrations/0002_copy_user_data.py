# Migration 0002: Copy all users from auth_user → accounts_customuser
# Preserves auth_user.id (PK) exactly.
# Uses raw SQL for performance on 6000+ users.
# This migration is reversible.

from django.db import migrations


def copy_users_to_customuser(apps, schema_editor):
    """
    INSERT all rows from auth_user + MTI shadow tables into accounts_customuser,
    preserving PKs exactly. Merges all fields from Student/Instructor/Administrator.
    """
    with schema_editor.connection.cursor() as cursor:

        # Safety check: no duplicate emails in auth_user
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT email FROM auth_user
                GROUP BY email HAVING COUNT(*) > 1
            ) dupes
        """)
        duplicate_count = cursor.fetchone()[0]
        if duplicate_count > 0:
            raise Exception(
                f"MIGRATION ABORTED: Found {duplicate_count} duplicate email(s) in auth_user. "
                "Resolve duplicates before running this migration."
            )

        # Check existing rows (idempotency — don't insert if already done)
        cursor.execute("SELECT COUNT(*) FROM accounts_customuser")
        existing = cursor.fetchone()[0]
        if existing > 0:
            print(f"\nℹ️  accounts_customuser already has {existing} rows — skipping copy.")
            return

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        cursor.execute("""
            INSERT INTO accounts_customuser (
                id,
                password,
                last_login,
                is_superuser,
                username,
                first_name,
                last_name,
                email,
                is_staff,
                is_active,
                date_joined,
                role,
                mobile_number,
                gender,
                college,
                dob,
                profile_pic,
                linkedin_id,
                github_id,
                coins,
                is_changed_password,
                is_email_verified
            )
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

                -- Role: check which MTI shadow table the user appears in
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
                COALESCE(s.is_changed_password, FALSE)                AS is_changed_password,
                au.is_active                                          AS is_email_verified

            FROM auth_user au
            LEFT JOIN accounts_student      s  ON s.user_ptr_id  = au.id
            LEFT JOIN accounts_instructor   ai ON ai.user_ptr_id = au.id
            LEFT JOIN accounts_administrator aa ON aa.user_ptr_id = au.id
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # Verify counts match
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        auth_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM accounts_customuser")
        custom_count = cursor.fetchone()[0]

        if auth_count != custom_count:
            raise Exception(
                f"MIGRATION FAILED: auth_user={auth_count} rows, "
                f"accounts_customuser={custom_count} rows. Rolling back."
            )

        print(f"\n✅ Copied {custom_count}/{auth_count} users to accounts_customuser")

        cursor.execute("SELECT role, COUNT(*) FROM accounts_customuser GROUP BY role")
        for role, count in cursor.fetchall():
            print(f"   {role}: {count}")


def reverse_copy(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DELETE FROM accounts_customuser")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Reversed: accounts_customuser cleared.")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_users_to_customuser, reverse_copy),
    ]
