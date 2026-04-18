# ── FILE: certificates/certificate_generator.py ──
"""
Isolated PDF generation pipeline.

Architecture:
  build_context()         → assembles template context dict
  generate_qr_bytes()     → returns QR code as base64-encoded PNG string
  render_certificate_html() → renders Jinja/Django template to HTML string
  generate_pdf_bytes()    → WeasyPrint HTML → PDF bytes
  get_or_generate_pdf()   → Redis cache check → generate → cache → return bytes

Redis strategy:
  Key:  cert_pdf:{certificate_id}        → raw PDF bytes
  Lock: cert_pdf_lock:{certificate_id}   → SET NX, TTL=120s
  TTL:  CERT_PDF_TTL (default 21600s = 6h)

Race condition handling:
  Two simultaneous requests for the same uncached cert:
  1. Request A: acquires lock, generates PDF, stores in Redis, releases lock
  2. Request B: sees lock, polls (100ms intervals, max 30s), then reads cache
  If B times out waiting: generates directly (safety fallback) but does NOT
  store (avoids double-write, A already stored it).
"""

import base64
import io
import logging
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CERT_PDF_TTL   = getattr(settings, "CERT_PDF_TTL", 21600)   # 6 hours
LOCK_TIMEOUT   = 120    # seconds — max time we hold the generation lock
LOCK_POLL_INTERVAL = 0.1  # seconds between poll checks
LOCK_WAIT_LIMIT    = 30   # seconds — max time we wait for another thread's lock


def _get_redis():
    """Return the raw redis-py client from django-redis cache backend."""
    return cache.client.get_client(write=True)


# ── QR Code Generation ───────────────────────────────────────────────────────

def generate_qr_bytes(certificate) -> str:
    """
    Generate a QR code for the verification URL.
    Returns a base64-encoded PNG string (for embedding in HTML as data URI).
    """
    try:
        import qrcode
        from qrcode.image.pil import PilImage
    except ImportError:
        logger.error("qrcode package not installed. Run: pip install qrcode[pil]")
        return ""

    verify_url = certificate.get_verify_url()

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    # Fire orange fill on transparent background
    img = qr.make_image(
        image_factory=PilImage,
        fill_color="#ff8c00",
        back_color="white",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


# ── Context Builder ──────────────────────────────────────────────────────────

def build_context(certificate) -> dict:
    """
    Build the full template context for rendering a certificate.

    Uses template_snapshot if available (previously frozen state).
    Falls back to the live template if snapshot is null.
    """
    student = certificate.student
    event   = certificate.event

    student_name = certificate.student_full_name
    issued_date  = certificate.issued_date.strftime("%B %d, %Y")

    # ── Resolve template data ─────────────────────────────────────────────
    snapshot = certificate.template_snapshot
    if snapshot:
        # Use frozen state
        body_text        = snapshot.get("body_text", "")
        org_name         = snapshot.get("org_name", "The Angaar Batch")
        org_logo_url     = snapshot.get("org_logo_url")
        show_qr          = snapshot.get("show_qr", True)
        show_hours       = snapshot.get("show_hours", False)
        show_batch       = snapshot.get("show_batch", False)
        hours            = snapshot.get("hours", 0)
        certificate_type = snapshot.get("certificate_type", "completion")
        html_layout      = snapshot.get("html_layout", "angaar_dark")
        signatories_data = snapshot.get("signatories", [])
    else:
        # Use live template
        tmpl = event.certificate_template
        if tmpl:
            body_text        = tmpl.body_text
            org_name         = tmpl.org_name
            org_logo_url     = tmpl.org_logo.url if tmpl.org_logo else None
            show_qr          = tmpl.show_qr
            show_hours       = tmpl.show_hours
            show_batch       = tmpl.show_batch
            hours            = tmpl.hours
            certificate_type = tmpl.certificate_type
            html_layout      = tmpl.html_layout
            signatories_data = [
                {
                    "name":                s.name,
                    "designation":         s.designation,
                    "organization":        s.organization,
                    "signature_image_url": s.signature_image.url if s.signature_image else None,
                }
                for s in tmpl.get_ordered_signatories()
            ]
        else:
            # Absolute fallback — no template configured
            body_text        = (
                f"This is to certify that {{student_name}} has successfully "
                f"participated in {{event_name}}."
            )
            org_name         = "The Angaar Batch"
            org_logo_url     = None
            show_qr          = True
            show_hours       = False
            show_batch       = False
            hours            = 0
            certificate_type = "completion"
            html_layout      = "angaar_dark"
            signatories_data = []

    # ── Resolve body text placeholders ────────────────────────────────────
    resolved_body = body_text.replace("{student_name}", student_name)
    resolved_body = resolved_body.replace("{event_name}", event.name)
    resolved_body = resolved_body.replace("{issued_date}", issued_date)
    resolved_body = resolved_body.replace("{hours}", str(hours))
    resolved_body = resolved_body.replace("{batch_name}", event.name)

    # ── Certificate type display ──────────────────────────────────────────
    type_display_map = {
        "completion":    "Certificate of Completion",
        "excellence":    "Certificate of Excellence",
        "participation": "Certificate of Participation",
        "achievement":   "Certificate of Achievement",
    }
    cert_type_display = type_display_map.get(certificate_type, "Certificate of Completion")

    # ── QR Code ───────────────────────────────────────────────────────────
    qr_base64 = ""
    if show_qr:
        qr_base64 = generate_qr_bytes(certificate)

    return {
        # Student
        "student":          student,
        "student_name":     student_name,
        # Event
        "event":            event,
        "event_name":       event.name,
        # Certificate metadata
        "certificate":      certificate,
        "certificate_id":   certificate.certificate_id,
        "issued_date":      issued_date,
        "verify_url":       certificate.get_verify_url(),
        # Template state (from snapshot or live)
        "body_text":        resolved_body,
        "org_name":         org_name,
        "org_logo_url":     org_logo_url,
        "show_qr":          show_qr,
        "show_hours":       show_hours,
        "show_batch":       show_batch,
        "hours":            hours,
        "certificate_type": certificate_type,
        "cert_type_display": cert_type_display,
        "html_layout":      html_layout,
        "signatories":      signatories_data,
        "qr_base64":        qr_base64,
        # Site
        "site_url": getattr(settings, "SITE_URL", "https://theangaarbatch.in"),
    }


def get_template_path(certificate) -> str:
    """Determine which HTML template file to use."""
    snapshot = certificate.template_snapshot
    if snapshot:
        layout = snapshot.get("html_layout", "angaar_dark")
    elif certificate.event.certificate_template:
        layout = certificate.event.certificate_template.html_layout
    else:
        layout = "angaar_dark"

    layout_map = {
        "angaar_dark":  "certificates/angaar_dark.html",
        "angaar_light": "certificates/angaar_dark.html",  # fallback until light is built
        "custom":       "certificates/angaar_dark.html",
    }
    return layout_map.get(layout, "certificates/angaar_dark.html")


# ── HTML Renderer ────────────────────────────────────────────────────────────

def render_certificate_html(certificate) -> str:
    """
    Render the certificate as a full standalone HTML page.
    Uses the template determined by the certificate's template layout choice.
    """
    context = build_context(certificate)
    template_path = get_template_path(certificate)
    return render_to_string(template_path, context)


# ── PDF Generator ────────────────────────────────────────────────────────────

def generate_pdf_bytes(certificate) -> bytes:
    """
    Render the certificate HTML and convert to PDF via WeasyPrint.
    Returns raw PDF bytes.

    IMPORTANT: This is the CPU/memory-heavy operation. It is called:
    - Directly from download_certificate view (on cache miss, inside a thread)
    - This keeps Gunicorn workers unblocked for other requests while the
      PDF is generating in an OS thread.
    """
    from weasyprint import HTML as WeasyprintHTML

    html_string = render_certificate_html(certificate)
    base_url = str(settings.BASE_DIR)

    logger.info("Generating PDF for certificate %s", certificate.certificate_id)
    pdf_bytes = WeasyprintHTML(
        string=html_string,
        base_url=base_url
    ).write_pdf()
    logger.info(
        "PDF generated for %s (%.1f KB)",
        certificate.certificate_id,
        len(pdf_bytes) / 1024,
    )
    return pdf_bytes


# ── Redis-Cached Entry Point ─────────────────────────────────────────────────

def get_or_generate_pdf(certificate) -> bytes:
    """
    Main entry point for serving a certificate PDF.

    Flow:
      1. Check Redis for cached PDF bytes
      2. If HIT  → return immediately
      3. If MISS → acquire Redis lock → generate → store → release → return
      4. If another thread holds the lock → poll until released → return cache

    Thread-safe via Redis SET NX lock.
    """
    redis   = _get_redis()
    pdf_key  = f"cert_pdf:{certificate.certificate_id}"
    lock_key = f"cert_pdf_lock:{certificate.certificate_id}"

    # ── 1. Cache hit check ────────────────────────────────────────────────
    cached = redis.get(pdf_key)
    if cached:
        logger.debug("Cache HIT for %s", certificate.certificate_id)
        return cached  # raw bytes from Redis

    # ── 2. Acquire lock (SET NX = set only if not exists) ─────────────────
    lock_acquired = redis.set(lock_key, "1", nx=True, ex=LOCK_TIMEOUT)

    if lock_acquired:
        # We won the lock — generate the PDF
        try:
            # Double-check cache (another request may have populated it
            # between our first check and our lock acquisition)
            cached = redis.get(pdf_key)
            if cached:
                return cached

            # Take a snapshot of the template state and save it
            _freeze_snapshot(certificate)

            pdf_bytes = generate_pdf_bytes(certificate)

            # Store raw bytes in Redis with TTL
            redis.set(pdf_key, pdf_bytes, ex=CERT_PDF_TTL)
            logger.info(
                "Cached PDF for %s (TTL=%ds)", certificate.certificate_id, CERT_PDF_TTL
            )
            return pdf_bytes

        except Exception as exc:
            logger.exception("PDF generation failed for %s: %s", certificate.certificate_id, exc)
            raise

        finally:
            redis.delete(lock_key)

    else:
        # Another thread/process is generating — poll for the result
        logger.debug(
            "Lock held for %s — polling for cached result", certificate.certificate_id
        )
        waited = 0.0
        while waited < LOCK_WAIT_LIMIT:
            time.sleep(LOCK_POLL_INTERVAL)
            waited += LOCK_POLL_INTERVAL

            cached = redis.get(pdf_key)
            if cached:
                logger.debug(
                    "Got cached PDF for %s after %.1fs wait",
                    certificate.certificate_id, waited
                )
                return cached

            # Check if lock is gone (generation finished, but cache not yet set — edge case)
            if not redis.exists(lock_key):
                cached = redis.get(pdf_key)
                if cached:
                    return cached
                # Lock released but no cache — generator must have failed.
                # Fall through and generate ourselves.
                break

        # Fallback: generate directly (lock holder timed out or crashed)
        logger.warning(
            "Timed out waiting for lock on %s — generating directly",
            certificate.certificate_id
        )
        _freeze_snapshot(certificate)
        pdf_bytes = generate_pdf_bytes(certificate)
        # Try to store it (may overwrite a partial result, but that's fine)
        redis.set(pdf_key, pdf_bytes, ex=CERT_PDF_TTL)
        return pdf_bytes


def _freeze_snapshot(certificate):
    """
    If the certificate has no template_snapshot yet, write one now.
    Uses database-level update to avoid race condition with concurrent saves.
    """
    from .event_models import Certificate
    if certificate.template_snapshot:
        return  # Already frozen

    tmpl = certificate.event.certificate_template
    if tmpl:
        snapshot = tmpl.to_snapshot()
    else:
        snapshot = {
            "template_id":       None,
            "template_name":     "Default",
            "certificate_type":  "completion",
            "html_layout":       "angaar_dark",
            "body_text":         (
                "This is to certify that {student_name} has successfully "
                "participated in {event_name}."
            ),
            "org_name":          "The Angaar Batch",
            "org_logo_url":      None,
            "show_qr":           True,
            "show_hours":        False,
            "show_batch":        False,
            "hours":             0,
            "signatories":       [],
        }

    # Use update() to avoid triggering full save() and signals
    Certificate.objects.filter(pk=certificate.pk).update(template_snapshot=snapshot)
    certificate.template_snapshot = snapshot  # update in-memory too
