# ── FILE: certificates/event_models.py ──
"""
Certificate system models.

Design principles:
- No raw HTML stored. Template layout is a choice that maps to a Django
  template file. Body text uses safe {placeholder} syntax.
- template_snapshot (JSONField) is written at first PDF generation, freezing
  the template state so future template edits don't corrupt existing certs.
- No PDF files stored on disk. PDFs are generated on demand and cached in
  Redis (TTL = 6 hours).
- Signatories are reusable entities linked via a through model with ordering.
"""

import secrets
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from accounts.models import CustomUser


# ──────────────────────────────────────────────────────────────────────────────
# SIGNATORY
# ──────────────────────────────────────────────────────────────────────────────

class Signatory(models.Model):
    """
    A person whose signature appears on a certificate.
    Reusable across multiple templates.
    """
    name         = models.CharField(max_length=255)
    designation  = models.CharField(max_length=255, help_text="e.g. Founder, Director")
    organization = models.CharField(max_length=255, help_text="e.g. The Angaar Batch")
    signature_image = models.ImageField(
        upload_to="certificates/signatures/",
        null=True,
        blank=True,
        help_text="Transparent PNG preferred (200×100px recommended)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Signatory"
        verbose_name_plural = "Signatories"
        ordering            = ["name"]

    def __str__(self):
        return f"{self.name} — {self.designation} ({self.organization})"


# ──────────────────────────────────────────────────────────────────────────────
# CERTIFICATE TEMPLATE
# ──────────────────────────────────────────────────────────────────────────────

class CertificateTemplate(models.Model):
    """
    Structured certificate template.

    html_layout choices map to actual Django template files:
      angaar_dark  → templates/certificates/angaar_dark.html
      angaar_light → templates/certificates/angaar_light.html  (future)
      custom       → use custom_template_path field

    Body text uses simple {placeholder} syntax:
      {student_name}, {event_name}, {issued_date}, {hours}, {batch_name}
    """

    LAYOUT_CHOICES = [
        ("angaar_dark",  "Angaar Dark (Fire Theme)"),
        ("angaar_light", "Angaar Light (Clean)"),
        ("custom",       "Custom HTML Template"),
    ]

    CERT_TYPE_CHOICES = [
        ("completion",    "Certificate of Completion"),
        ("excellence",    "Certificate of Excellence"),
        ("participation", "Certificate of Participation"),
        ("achievement",   "Certificate of Achievement"),
    ]

    name             = models.CharField(max_length=255, unique=True)
    slug             = models.SlugField(unique=True, blank=True, editable=False)
    certificate_type = models.CharField(
        max_length=20, choices=CERT_TYPE_CHOICES, default="completion"
    )
    html_layout      = models.CharField(
        max_length=20, choices=LAYOUT_CHOICES, default="angaar_dark"
    )

    # Body text shown in the certificate body paragraph.
    body_text = models.TextField(
        help_text=(
            "Certificate body paragraph. Supports: {student_name}, {event_name}, "
            "{issued_date}, {hours}, {batch_name}. "
            "Example: 'This is to certify that {student_name} has successfully "
            "completed the {event_name} programme.'"
        )
    )

    # Organisation branding
    org_name = models.CharField(
        max_length=255, default="The Angaar Batch",
        help_text="Shown as the issuing organisation on the certificate"
    )
    org_logo = models.ImageField(
        upload_to="certificates/logos/", null=True, blank=True,
        help_text="Organisation logo (PNG with transparent background preferred)"
    )

    # Feature flags
    show_qr    = models.BooleanField(default=True,  help_text="Show QR verification code")
    show_hours = models.BooleanField(default=False, help_text="Show training hours")
    show_batch = models.BooleanField(default=False, help_text="Show batch name")
    hours      = models.PositiveIntegerField(
        default=0, help_text="Training hours to display if show_hours=True"
    )

    # Signatories via through model
    signatories = models.ManyToManyField(
        Signatory,
        through="TemplateSignatory",
        through_fields=("template", "signatory"),
        related_name="templates",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Certificate Template"
        verbose_name_plural = "Certificate Templates"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_certificate_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "template"
            slug = base
            counter = 1
            while CertificateTemplate.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_template_path(self):
        """Return the Django template path for this layout."""
        layout_map = {
            "angaar_dark":  "certificates/angaar_dark.html",
            "angaar_light": "certificates/angaar_light.html",
            "custom":       "certificates/angaar_dark.html",  # fallback
        }
        return layout_map.get(self.html_layout, "certificates/angaar_dark.html")

    def get_ordered_signatories(self):
        """Return signatories ordered by TemplateSignatory.order."""
        return self.signatories.filter(
            templatesignatory__template=self
        ).order_by("templatesignatory__order")

    def to_snapshot(self):
        """Serialise the template state for freezing into Certificate.template_snapshot."""
        return {
            "template_id":       self.pk,
            "template_name":     self.name,
            "certificate_type":  self.certificate_type,
            "html_layout":       self.html_layout,
            "body_text":         self.body_text,
            "org_name":          self.org_name,
            "org_logo_url":      self.org_logo.url if self.org_logo else None,
            "show_qr":           self.show_qr,
            "show_hours":        self.show_hours,
            "show_batch":        self.show_batch,
            "hours":             self.hours,
            "signatories": [
                {
                    "name":            s.name,
                    "designation":     s.designation,
                    "organization":    s.organization,
                    "signature_image_url": (
                        s.signature_image.url if s.signature_image else None
                    ),
                }
                for s in self.get_ordered_signatories()
            ],
        }


# ──────────────────────────────────────────────────────────────────────────────
# THROUGH MODEL: Template ↔ Signatory with ordering
# ──────────────────────────────────────────────────────────────────────────────

class TemplateSignatory(models.Model):
    """
    Ordered relationship between a CertificateTemplate and a Signatory.
    Lower `order` value appears first (left-to-right on the certificate).
    """
    template  = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE)
    signatory = models.ForeignKey(Signatory, on_delete=models.CASCADE)
    order     = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("template", "signatory")
        ordering        = ["order"]
        verbose_name        = "Template Signatory"
        verbose_name_plural = "Template Signatories"

    def __str__(self):
        return f"{self.template.name} — {self.signatory.name} (order={self.order})"


# ──────────────────────────────────────────────────────────────────────────────
# EVENT
# ──────────────────────────────────────────────────────────────────────────────

class Event(models.Model):
    """
    Represents a training, course, or any event for which certificates are issued.
    The certificate_template FK points to the structured CertificateTemplate.
    """
    name  = models.CharField(max_length=255, unique=True)
    code  = models.CharField(
        max_length=20, unique=True,
        help_text="Short code used in certificate IDs (e.g. 'FLAMES25MERN')"
    )
    start_date  = models.DateField()
    end_date    = models.DateField()
    description = models.TextField(blank=True)
    certificate_template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Template used for certificates. If blank, default Angaar Dark is used.",
        related_name="events",
    )

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ──────────────────────────────────────────────────────────────────────────────
# CERTIFICATE
# ──────────────────────────────────────────────────────────────────────────────

class Certificate(models.Model):
    """
    A certificate issued to a student for an event.

    PDF is generated on-demand and cached in Redis. No PDF file is stored.

    template_snapshot (JSONField):
        Written at first PDF generation, freezing the template state.
        Allows future template edits without corrupting existing PDFs.
        If null, the live template is used (first generation hasn't happened yet).
    """
    certificate_id = models.CharField(
        max_length=100, unique=True, editable=False,
        help_text="Auto-generated: EVENTCODE + STUDENTPK"
    )
    event   = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="certificates")
    student = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="certificates")

    issued_date = models.DateField(default=timezone.now)
    approved    = models.BooleanField(default=False, db_index=True)

    # Frozen template state — written at PDF generation time
    template_snapshot = models.JSONField(
        null=True, blank=True,
        help_text=(
            "Frozen copy of the template at PDF generation time. "
            "Null until the first PDF is generated. "
            "Prevents future template edits from changing existing certs."
        )
    )

    class Meta:
        unique_together = ("event", "student")
        indexes = [
            models.Index(fields=["certificate_id"]),
            models.Index(fields=["approved"]),
            models.Index(fields=["student", "approved"]),
        ]
        ordering = ["-issued_date"]

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.certificate_id}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"{self.event.code}{self.student.pk}"
        super().save(*args, **kwargs)

    @property
    def student_full_name(self):
        name = self.student.get_full_name().strip()
        return name if name else self.student.username

    def get_verify_url(self):
        from django.conf import settings
        base = getattr(settings, "SITE_URL", "https://theangaarbatch.in")
        return f"{base}/certificate/verify/{self.certificate_id}/"

    def get_download_url(self):
        from django.urls import reverse
        return reverse("download_certificate", kwargs={"cert_id": self.certificate_id})

    def get_view_url(self):
        return f"/dashboard/event/{self.pk}/certificate/view"

    def invalidate_pdf_cache(self):
        """Remove the cached PDF from Redis."""
        from django.core.cache import cache
        redis_client = cache.client.get_client(write=True)
        redis_client.delete(f"cert_pdf:{self.certificate_id}")
        redis_client.delete(f"cert_pdf_lock:{self.certificate_id}")

    def has_cached_pdf(self):
        """Check if a cached PDF exists in Redis."""
        from django.core.cache import cache
        redis_client = cache.client.get_client()
        return redis_client.exists(f"cert_pdf:{self.certificate_id}") == 1


# ──────────────────────────────────────────────────────────────────────────────
# Import resource helper (kept for django-import-export compatibility)
# ──────────────────────────────────────────────────────────────────────────────

from django.template import engines as _django_engines


def get_template_from_db(template_string):
    """Compile a template string stored in the DB using Django's template engine."""
    engine = _django_engines["django"]
    return engine.from_string(template_string)
