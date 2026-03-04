from django.db import migrations


class Migration(migrations.Migration):
    """
    Phase 2 Cleanup: Drop the old Multi-Table Inheritance (MTI) shadow tables.

    BACKGROUND:
    Before Phase 1, we had 3 separate user tables:
        auth_user           — base Django user
        accounts_student    — MTI extension with dob, coins, mobile_number, etc.
        accounts_instructor — MTI extension with instructor-specific fields
        accounts_administrator — MTI extension with admin fields

    After Phase 1:
        accounts_customuser — ONE table with ALL fields + a `role` column.
        The proxy models (Student, Instructor, Administrator) were kept as
        in-code shims but they now read from accounts_customuser.

    This migration:
    1. Deletes the proxy model definitions from Django's state (no more
       Student/Instructor/Administrator ORM classes — use CustomUser.objects.filter(role=...))
    2. Drops the old MTI physical tables from the database (they're empty
       and were only kept for rollback safety during Phase 1).
    """

    dependencies = [
        ('accounts', '0004_update_proxy_verbose_names'),
    ]

    operations = [
        # ── Step 1: Remove proxy model definitions from Django's ORM state ──
        # This means you can no longer do `from accounts.models import Student`.
        # Use `CustomUser.objects.filter(role='student')` instead.
        migrations.DeleteModel(name='Student'),
        migrations.DeleteModel(name='Instructor'),
        migrations.DeleteModel(name='Administrator'),

        # ── Step 2: Drop the physical shadow tables from the database ──
        # These tables exist because of the old MTI setup where each proxy
        # model got its own table with a user_ptr_id FK to auth_user.
        # They are now empty and unused.
        migrations.RunSQL(
            sql="SET FOREIGN_KEY_CHECKS = 0;",
            reverse_sql="",
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS accounts_student;",
            reverse_sql="-- Cannot recreate old MTI table after drop (irreversible)",
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS accounts_instructor;",
            reverse_sql="-- Cannot recreate old MTI table after drop (irreversible)",
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS accounts_administrator;",
            reverse_sql="-- Cannot recreate old MTI table after drop (irreversible)",
        ),
        migrations.RunSQL(
            sql="SET FOREIGN_KEY_CHECKS = 1;",
            reverse_sql="",
        ),
    ]
