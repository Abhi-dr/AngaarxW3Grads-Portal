"""
Migration 0010: Fix MySQL strict-mode IntegrityError on FlamesCourse

The rogue `instructor` varchar column has already been removed.
This migration fixes the remaining NOT NULL / no-DB-default columns:

  - varchar columns (subtitle, icon_class, icon_color, button_color):
    Set actual DEFAULT values — MySQL supports DEFAULT on varchar.

  - longtext columns (description, what_you_will_learn):
    MySQL < 8.0.13 cannot have DEFAULT on TEXT/BLOB. We make them
    nullable (NULL) so MySQL strict mode never fires. Django always
    writes the Python default ('') on INSERT so NULL never appears.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_cleanup_flamescourse'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Fix varchar columns: add actual DB-level defaults
                ALTER TABLE home_flamescourse
                    MODIFY COLUMN subtitle     varchar(255)  NOT NULL DEFAULT '',
                    MODIFY COLUMN icon_class   varchar(100)  NOT NULL DEFAULT 'fas fa-fire',
                    MODIFY COLUMN icon_color   varchar(50)   NOT NULL DEFAULT '#ff6b00',
                    MODIFY COLUMN button_color varchar(50)   NOT NULL DEFAULT '#ff6b00';

                -- Fix longtext columns: make nullable (MySQL can't DEFAULT on TEXT)
                ALTER TABLE home_flamescourse
                    MODIFY COLUMN description         longtext NULL,
                    MODIFY COLUMN what_you_will_learn longtext NULL;
            """,
            reverse_sql="""
                ALTER TABLE home_flamescourse
                    MODIFY COLUMN subtitle     varchar(255) NOT NULL DEFAULT '',
                    MODIFY COLUMN icon_class   varchar(100) NOT NULL DEFAULT '',
                    MODIFY COLUMN icon_color   varchar(50)  NOT NULL DEFAULT '',
                    MODIFY COLUMN button_color varchar(50)  NOT NULL DEFAULT '';

                ALTER TABLE home_flamescourse
                    MODIFY COLUMN description         longtext NOT NULL,
                    MODIFY COLUMN what_you_will_learn longtext NOT NULL;
            """,
        )
    ]
