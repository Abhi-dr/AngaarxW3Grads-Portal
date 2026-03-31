"""
Enforce NOT NULL on edition FK for FlamesRegistration, FlamesCourse, and FlamesTeam.

Safe to run only after migration 0007 has been verified to produce 0 unlinked rows.
ReferralCode.edition intentionally stays nullable (codes may be reused across editions).
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_backfill_edition_2025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flamesregistration',
            name='edition',
            field=models.ForeignKey(
                to='home.FlamesEdition',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='registrations',
                # null removed — field is now required
            ),
        ),
        migrations.AlterField(
            model_name='flamescourse',
            name='edition',
            field=models.ForeignKey(
                to='home.FlamesEdition',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='courses',
            ),
        ),
        migrations.AlterField(
            model_name='flamesteam',
            name='edition',
            field=models.ForeignKey(
                to='home.FlamesEdition',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='teams',
            ),
        ),
    ]
