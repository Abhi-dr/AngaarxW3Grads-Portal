"""
Certificate generation pipeline — straightforward synchronous version.

Functions:
  generate_qr_bytes()       → QR code as base64 PNG string (embeds in HTML)
  build_context()           → assembles template context from live template / snapshot
  get_template_path()       → resolves layout → Django template file path
  render_certificate_html() → renders template to full HTML string
  generate_pdf_bytes()      → WeasyPrint HTML → raw PDF bytes
"""

import base64
import io
import logging

from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


# ── QR Code Generation ───────────────────────────────────────────────────────

def generate_qr_bytes(certificate) -> str:
    """
    Generate a QR code pointing to the public verification URL.
    Returns a base64-encoded PNG string for embedding as a data URI.
    """
    try:
        import qrcode
        from qrcode.image.pil import PilImage
    except ImportError:
        logger.error("qrcode not installed — run: pip install qrcode[pil]")
        return ""

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(certificate.get_verify_url())
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=PilImage,
        fill_color="#ff8c00",
        back_color="white",
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ── Context Builder ──────────────────────────────────────────────────────────

def build_context(certificate) -> dict:
    """
    Build the template context dict.

    Priority:
      1. template_snapshot (frozen at first generation — keeps old certs stable)
      2. live event.certificate_template
      3. hard-coded defaults (if no template configured)
    """
    student      = certificate.student
    event        = certificate.event
    student_name = certificate.student_full_name
    issued_date  = certificate.issued_date.strftime("%B %d, %Y")

    snapshot = certificate.template_snapshot
    if snapshot:
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
            body_text        = "This is to certify that {student_name} has successfully participated in {event_name}."
            org_name         = "The Angaar Batch"
            org_logo_url     = None
            show_qr          = True
            show_hours       = False
            show_batch       = False
            hours            = 0
            certificate_type = "completion"
            html_layout      = "angaar_dark"
            signatories_data = []

    # Resolve {placeholders} in body text
    resolved_body = (
        body_text
        .replace("{student_name}", student_name)
        .replace("{event_name}",   event.name)
        .replace("{issued_date}",  issued_date)
        .replace("{hours}",        str(hours))
        .replace("{batch_name}",   event.name)
    )

    type_display_map = {
        "completion":    "Certificate of Completion",
        "excellence":    "Certificate of Excellence",
        "participation": "Certificate of Participation",
        "achievement":   "Certificate of Achievement",
    }

    return {
        "student":           student,
        "student_name":      student_name,
        "event":             event,
        "event_name":        event.name,
        "certificate":       certificate,
        "certificate_id":    certificate.certificate_id,
        "issued_date":       issued_date,
        "verify_url":        certificate.get_verify_url(),
        "body_text":         resolved_body,
        "org_name":          org_name,
        "org_logo_url":      org_logo_url,
        "show_qr":           show_qr,
        "show_hours":        show_hours,
        "show_batch":        show_batch,
        "hours":             hours,
        "certificate_type":  certificate_type,
        "cert_type_display": type_display_map.get(certificate_type, "Certificate of Completion"),
        "html_layout":       html_layout,
        "signatories":       signatories_data,
        "qr_base64":         generate_qr_bytes(certificate) if show_qr else "",
        "site_url":          getattr(settings, "SITE_URL", "https://theangaarbatch.in"),
    }


# ── Template Path ─────────────────────────────────────────────────────────────

# Map layout key → (fragment_template, pdf_wrapper_template)
_LAYOUT_MAP = {
    "angaar_dark":  ("certificates/angaar_dark.html",  "certificates/angaar_dark_pdf.html"),
    "angaar_light": ("certificates/angaar_dark.html",  "certificates/angaar_dark_pdf.html"),  # until light is built
    "custom":       ("certificates/angaar_dark.html",  "certificates/angaar_dark_pdf.html"),
}


def _resolve_layout(certificate) -> str:
    """Returns the layout key (e.g. 'angaar_dark') for this certificate."""
    snapshot = certificate.template_snapshot
    if snapshot:
        return snapshot.get("html_layout", "angaar_dark")
    elif certificate.event.certificate_template:
        return certificate.event.certificate_template.html_layout
    return "angaar_dark"


def get_fragment_path(certificate) -> str:
    """Returns the Django template path for the certificate HTML fragment."""
    return _LAYOUT_MAP.get(_resolve_layout(certificate), _LAYOUT_MAP["angaar_dark"])[0]


def get_pdf_wrapper_path(certificate) -> str:
    """Returns the full-document template path used by WeasyPrint."""
    return _LAYOUT_MAP.get(_resolve_layout(certificate), _LAYOUT_MAP["angaar_dark"])[1]


# ── HTML Renderer ─────────────────────────────────────────────────────────────

def render_certificate_html(certificate) -> str:
    """
    Render the full-document certificate HTML string (for WeasyPrint).
    Uses the PDF wrapper which includes the certificate fragment internally.
    """
    context = build_context(certificate)
    # Pass template_path so the PDF wrapper can {% include %} the right fragment
    context["template_path"] = get_fragment_path(certificate)
    return render_to_string(get_pdf_wrapper_path(certificate), context)


# ── PDF Generator ─────────────────────────────────────────────────────────────

def generate_pdf_bytes(certificate) -> bytes:
    """
    Render the certificate HTML and convert to PDF via WeasyPrint.
    Returns raw PDF bytes. Called directly from the download view.
    """
    from weasyprint import HTML as WeasyprintHTML
    import os

    html_string = render_certificate_html(certificate)
    logger.info("Generating PDF for %s", certificate.certificate_id)

    # Replace relative media URLs with absolute local file URIs to prevent
    # WeasyPrint from deadlocking on HTTP fetches against the dev server.
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_root = getattr(settings, "MEDIA_ROOT", "")
    if media_url and media_root:
        local_media_uri = f"file://{os.path.abspath(media_root)}/"
        # e.g., src="/media/" becomes src="file:///path/to/media/"
        html_string = html_string.replace(f'src="{media_url}', f'src="{local_media_uri}')
        html_string = html_string.replace(f"src='{media_url}", f"src='{local_media_uri}")

    pdf_bytes = WeasyprintHTML(
        string=html_string,
        base_url=str(settings.BASE_DIR),
    ).write_pdf()

    logger.info("PDF ready for %s (%.1f KB)", certificate.certificate_id, len(pdf_bytes) / 1024)
    return pdf_bytes
