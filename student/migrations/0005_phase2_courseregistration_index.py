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
                ALTER TABLE student_courseregistration
                ADD INDEX idx_coursereg_student_course (student_id, course_id, is_active),
                ALGORITHM=INPLACE, LOCK=NONE
            """,
            reverse_sql="ALTER TABLE student_courseregistration DROP INDEX idx_coursereg_student_course",
        ),
    ]
