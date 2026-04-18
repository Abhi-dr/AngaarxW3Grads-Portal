# ── FILE: certificates/tasks.py ──
"""
Celery tasks for the certificate system.

Queue: "certificates"
Worker concurrency: 2 (limits WeasyPrint memory usage)

Pre-warming use case:
  After bulk certificate approval, an admin action can trigger
  pre_warm_certificate_pdf() for each cert to populate the Redis cache
  before students start downloading. This makes the first download instant.
"""

import logging
from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    queue="certificates",
    max_retries=3,
    default_retry_delay=30,
    name="certificates.pre_warm_certificate_pdf",
)
def pre_warm_certificate_pdf(self, certificate_pk: int):
    """
    Pre-generate and cache the PDF for a certificate.

    Called optionally after bulk approval so students get instant downloads.
    If the PDF is already cached, this is a no-op.

    Args:
        certificate_pk: Primary key of the Certificate to warm.
    """
    from .event_models import Certificate
    from .certificate_generator import get_or_generate_pdf

    try:
        cert = Certificate.objects.select_related(
            "event__certificate_template", "student"
        ).get(pk=certificate_pk)

        if cert.has_cached_pdf():
            logger.info(
                "pre_warm: Cache already exists for %s — skipping",
                cert.certificate_id,
            )
            return f"already_cached:{cert.certificate_id}"

        get_or_generate_pdf(cert)
        logger.info("pre_warm: Cached PDF for %s", cert.certificate_id)
        return f"cached:{cert.certificate_id}"

    except Certificate.DoesNotExist:
        logger.error("pre_warm: Certificate pk=%d not found", certificate_pk)
        return f"not_found:{certificate_pk}"

    except Exception as exc:
        logger.exception(
            "pre_warm: Failed for certificate pk=%d: %s", certificate_pk, exc
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    queue="certificates",
    name="certificates.invalidate_certificate_cache",
)
def invalidate_certificate_cache(self, certificate_id: str):
    """
    Remove a certificate's cached PDF from Redis.

    Called when the certificate is updated or the admin manually clears cache.

    Args:
        certificate_id: The string certificate_id (e.g. "FLAMES25MERN1234")
    """
    try:
        redis_client = cache.client.get_client(write=True)
        pdf_key  = f"cert_pdf:{certificate_id}"
        lock_key = f"cert_pdf_lock:{certificate_id}"
        redis_client.delete(pdf_key, lock_key)
        logger.info("Invalidated cache for certificate %s", certificate_id)
        return f"invalidated:{certificate_id}"
    except Exception as exc:
        logger.exception("Failed to invalidate cache for %s: %s", certificate_id, exc)
        raise
