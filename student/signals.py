# ── FILE: certificates/signals.py ──
"""
Django signals for the certificate system.

Cache invalidation:
  When a Certificate is saved (e.g. approved flag changed, issued_date edited),
  the cached PDF is invalidated so the next download regenerates with fresh data.

  We do NOT invalidate on every save indiscriminately — only on fields
  that would change the rendered PDF.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender="student.Certificate")
def _track_certificate_changes(sender, instance, **kwargs):
    """
    Before saving, capture old field values so we can detect changes.
    """
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_issued_date = old.issued_date
            instance._old_approved    = old.approved
            instance._old_snapshot    = old.template_snapshot
        except sender.DoesNotExist:
            instance._old_issued_date = None
            instance._old_approved    = None
            instance._old_snapshot    = None
    else:
        instance._old_issued_date = None
        instance._old_approved    = None
        instance._old_snapshot    = None


@receiver(post_save, sender="student.Certificate")
def _invalidate_pdf_cache_on_change(sender, instance, created, **kwargs):
    """
    Invalidate the cached PDF when certificate data changes.

    Triggers on:
    - New certificate created (no-op — nothing cached yet)
    - issued_date changed
    - approved changed (approval triggers new download → needs fresh PDF)
    - template_snapshot changed (admin manually updated)
    """
    if created:
        # Brand new cert — nothing cached yet
        return

    old_issued_date = getattr(instance, "_old_issued_date", None)
    old_approved    = getattr(instance, "_old_approved", None)
    old_snapshot    = getattr(instance, "_old_snapshot", None)

    changed = (
        old_issued_date != instance.issued_date
        or old_approved  != instance.approved
        or old_snapshot  != instance.template_snapshot
    )

    if changed:
        try:
            instance.invalidate_pdf_cache()
            logger.info(
                "Invalidated PDF cache for certificate %s (changed fields detected)",
                instance.certificate_id,
            )
        except Exception as exc:
            # Cache invalidation must never crash the save transaction
            logger.warning(
                "Cache invalidation failed for %s: %s",
                instance.certificate_id, exc
            )
