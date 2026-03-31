"""
Migration 0012: Server-safe instructor column cleanup

On the server, the rogue `instructor varchar(200) NOT NULL` column was never
dropped (migration 0010 removed the DROP COLUMN statement after it already ran
on local by accident).

This migration uses RunPython to CHECK whether the column exists before dropping
it -- making it safe to run on BOTH the server (where it still exists) and on
any future fresh installations (where it won't exist).
"""

from django.db import migrations, connection


def drop_instructor_if_exists(apps, schema_editor):
    with connection.cursor() as cursor:
        # Check if the column exists in the actual DB table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'home_flamescourse'
              AND COLUMN_NAME  = 'instructor'
              AND DATA_TYPE    IN ('varchar', 'char', 'text')
        """)
        row = cursor.fetchone()
        if row and row[0] > 0:
            cursor.execute(
                "ALTER TABLE home_flamescourse DROP COLUMN instructor;"
            )


def restore_instructor_column(apps, schema_editor):
    # Reverse: add the column back (empty default keeps it non-blocking)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'home_flamescourse'
              AND COLUMN_NAME  = 'instructor'
        """)
        row = cursor.fetchone()
        if row and row[0] == 0:
            cursor.execute(
                "ALTER TABLE home_flamescourse "
                "ADD COLUMN instructor varchar(200) NOT NULL DEFAULT '';"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_flamescourse_level'),
    ]

    operations = [
        migrations.RunPython(
            drop_instructor_if_exists,
            restore_instructor_column,
        )
    ]
