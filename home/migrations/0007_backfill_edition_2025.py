"""
Zero-data-loss backfill migration.

All existing FlamesCourse, FlamesRegistration, FlamesTeam, and ReferralCode rows
were created in April–November 2025 (confirmed by DB audit) and belong entirely
to FLAMES 2025 (edition id=1, year=2025).

This migration assigns edition=FLAMES 2025 to all unlinked rows in one bulk UPDATE
per table. It is fully reversible by nulling the FK back out.
"""

from django.db import migrations


def backfill_to_2025(apps, schema_editor):
    FlamesEdition      = apps.get_model('home', 'FlamesEdition')
    FlamesRegistration = apps.get_model('home', 'FlamesRegistration')
    FlamesCourse       = apps.get_model('home', 'FlamesCourse')
    FlamesTeam         = apps.get_model('home', 'FlamesTeam')
    ReferralCode       = apps.get_model('home', 'ReferralCode')

    try:
        ed_2025 = FlamesEdition.objects.get(year=2025)
    except FlamesEdition.DoesNotExist:
        raise RuntimeError(
            "FLAMES 2025 edition row not found. "
            "Run the seed script before applying this migration:\n"
            "  python manage.py shell -c \""
            "from home.models import FlamesEdition; "
            "FlamesEdition.objects.get_or_create(year=2025, defaults={'name': 'FLAMES 25'})"
            "\""
        )

    regs  = FlamesRegistration.objects.filter(edition__isnull=True).update(edition=ed_2025)
    crs   = FlamesCourse.objects.filter(edition__isnull=True).update(edition=ed_2025)
    teams = FlamesTeam.objects.filter(edition__isnull=True).update(edition=ed_2025)
    refs  = ReferralCode.objects.filter(edition__isnull=True).update(edition=ed_2025)

    print(
        f"\n[backfill_edition_2025] Assigned FLAMES 25 to:\n"
        f"  FlamesRegistration: {regs}\n"
        f"  FlamesCourse:       {crs}\n"
        f"  FlamesTeam:         {teams}\n"
        f"  ReferralCode:       {refs}\n"
    )


def reverse_backfill(apps, schema_editor):
    """Safely undo: null out all edition FKs."""
    FlamesRegistration = apps.get_model('home', 'FlamesRegistration')
    FlamesCourse       = apps.get_model('home', 'FlamesCourse')
    FlamesTeam         = apps.get_model('home', 'FlamesTeam')
    ReferralCode       = apps.get_model('home', 'ReferralCode')

    FlamesRegistration.objects.all().update(edition=None)
    FlamesCourse.objects.all().update(edition=None)
    FlamesTeam.objects.all().update(edition=None)
    ReferralCode.objects.all().update(edition=None)

    print("[reverse_backfill] All edition FKs nulled out.")


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_add_flames_edition_and_fks'),
    ]

    operations = [
        migrations.RunPython(backfill_to_2025, reverse_backfill),
    ]
