import os
from io import BytesIO
from django.db import models
from django.template.loader import get_template
from django.conf import settings
from django.utils import timezone
from weasyprint import HTML

from accounts.models import Student 


class Event(models.Model):
    """Represents a training, course, or any event for which certificates are issued."""
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code used in certificate IDs (e.g., 'FLAMES25MERN')."
    )

    start_date = models.DateField(
        help_text="Date when the event starts. Used for certificate validity."
    )
    end_date = models.DateField(
        help_text="Date when the event ends. Used for certificate validity."
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class CertificateTemplate(models.Model):
    """HTML template for rendering certificates."""
    name = models.CharField(max_length=255, unique=True)
    html_template = models.TextField(
        help_text="HTML with Jinja-style placeholders: {{ student.full_name }}, {{ event.name }}, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Certificate(models.Model):
    """Certificate record — PDF is generated on-demand."""
    certificate_id = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
        help_text="Auto-generated: EVENTCODE + STUDENTPK"
    )
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="certificates")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="certificates")
    issued_date = models.DateField(default=timezone.now)
    approved = models.BooleanField(default=False)
    template_version = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.PROTECT,
        help_text="Template used for rendering this certificate."
    )

    class Meta:
        unique_together = ("event", "student")
        indexes = [
            models.Index(fields=["certificate_id"]),
            models.Index(fields=["approved"]),
        ]
        ordering = ["-issued_date"]

    def __str__(self):
        return f"{self.student.first_name } – {self.certificate_id}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"{self.event.code}{self.student.pk}"
        super().save(*args, **kwargs)

    from weasyprint import HTML

def generate_pdf(self):
    """Render certificate as a PDF in memory using WeasyPrint."""
    template = get_template_from_db(self.template_version.html_template)
    context = {
        "student": self.student,
        "event": self.event,
        "issued_date": self.issued_date.strftime("%B %d, %Y"),
        "certificate_id": self.certificate_id,
    }

    html_string = template.render(context)
    
    # If your templates refer to static/media files, you need base_url for resolving
    # Typically, you can pass settings.STATIC_ROOT or your project root folder here.
    # For example, if you want URLs in your template like /static/css/style.css, base_url helps WeasyPrint find them.
    base_url = settings.STATIC_ROOT  # or os.path.join(settings.BASE_DIR, 'static')

    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

    return BytesIO(pdf_bytes)


    def _link_callback(self, uri, rel):
        """Resolve static/media paths so xhtml2pdf can embed images & CSS."""
        if uri.startswith(settings.MEDIA_URL):
            return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            return os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
        return uri


# Helper to render a template stored in DB
from django.template import engines
def get_template_from_db(template_string):
    django_engine = engines["django"]
    return django_engine.from_string(template_string)
