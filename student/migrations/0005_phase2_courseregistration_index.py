"""
Phase 2 — DB Hardening: student_courseregistration composite index.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_fk_rewire_to_customuser'),
    ]

    operations = [
        # Powers: "show all courses for this student" and enrollment lookups
        migrations.RunSQL(
            sql="""
                CREATE INDEX idx_coursereg_student_course
                ON student_courseregistration (student_id, course_id, status);
            """,
            reverse_sql="DROP INDEX idx_coursereg_student_course ON student_courseregistration;",
        ),
    ]
