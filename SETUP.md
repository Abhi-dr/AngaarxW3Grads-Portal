# Certificate System — Setup & Deployment Guide

## Summary

Production-ready certificate system for The Angaar Batch, built on:
- **On-demand WeasyPrint PDF generation** (no PDFs stored on disk)
- **Redis caching** (6-hour TTL, Redis SET NX lock prevents race conditions)
- **Fire-themed `angaar_dark` certificate** (WeasyPrint-safe CSS, A4 landscape)
- **Dynamic signatories** (admin-managed, ordered M2M through model)
- **QR verification** (public `/certificate/verify/<id>/`, no login)
- **Admin controls** (approve, bulk clear cache, pre-warm, preview)

---

## 1. pip Packages Required

```bash
# Already in requirements.txt (existing):
weasyprint==66.0
django-redis==6.0.0
redis==6.4.0
celery==5.5.3
pillow==11.3.0

# NEW — add this:
pip install "qrcode[pil]"
```

After installing, add to `requirements.txt`:
```
qrcode==8.0
```

> **WeasyPrint system dependencies** (Linux VPS):
> ```bash
> sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
>     libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
> ```

---

## 2. Django Settings Additions

Add to `.env`:
```env
# Certificate system
SITE_URL=https://theangaarbatch.in   # No trailing slash
CERT_PDF_TTL=21600                   # PDF cache TTL in seconds (6 hours)
```

These are already read in `settings.py`:
```python
CERT_PDF_TTL = int(os.getenv("CERT_PDF_TTL", 21600))
SITE_URL = os.getenv("SITE_URL", "https://theangaarbatch.in")
```

Ensure `CACHES` uses `django_redis` (already configured on DB 1):
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}
```

---

## 3. Celery Worker Commands

### Main worker (existing tasks):
```bash
celery -A angaar_hai worker --loglevel=info -Q celery
```

### Certificate worker (dedicated, concurrency=2 to cap WeasyPrint memory):
```bash
celery -A angaar_hai worker \
    --loglevel=info \
    -Q certificates \
    --concurrency=2 \
    -n certificate_worker@%h
```

> **Why concurrency=2?** Each WeasyPrint generation uses ~150–300 MB RAM.
> With `concurrency=2`, peak certificate memory usage is bounded at ~600 MB.
> On a 2 GB VPS this leaves headroom for Gunicorn + Nginx + MySQL + Redis.

### Systemd service example (`/etc/systemd/system/celery-certificates.service`):
```ini
[Unit]
Description=Celery Certificate Worker
After=network.target

[Service]
Type=forking
User=www-data
WorkingDirectory=/var/www/angaar_hai
ExecStart=/var/www/angaar_hai/venv/bin/celery -A angaar_hai worker \
    -Q certificates --concurrency=2 -n certificate_worker@%%h \
    --logfile=/var/log/celery/certificates.log --loglevel=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 4. Redis Configuration

No changes needed — certificate PDFs share Redis DB 1 with Django's cache.

Redis key schema:
| Key | Content | TTL |
|-----|---------|-----|
| `cert_pdf:{certificate_id}` | Raw PDF bytes | 6 hours (CERT_PDF_TTL) |
| `cert_pdf_lock:{certificate_id}` | Generation lock ("1") | 120 seconds |

To manually inspect cached PDFs:
```bash
redis-cli -n 1 KEYS "cert_pdf:*"
redis-cli -n 1 TTL "cert_pdf:FLAMES25MERN1234"
redis-cli -n 1 DEL "cert_pdf:FLAMES25MERN1234"
```

---

## 5. Migration Notes

```bash
# The migration 0014_certificate_system_v2 has already been applied.
# For a fresh server deploy:
python manage.py migrate

# Verify:
python manage.py check   # Should show 0 issues
```

**What was migrated (0014):**
- `student_signatory` table (new)
- `student_templatesignatory` table (new, through model)
- `student_certificatetemplate` — added: `body_text`, `certificate_type`,
  `html_layout`, `org_name`, `org_logo`, `show_qr`, `show_hours`, `show_batch`,
  `hours`, `slug` (unique), `updated_at`, `signatories` M2M
- `student_certificate` — added: `template_snapshot` (JSONField)
- Removed: `html_template` raw TextField from `student_certificatetemplate`

---

## 6. URL Structure

| URL | Auth | Description |
|-----|------|-------------|
| `/dashboard/my-certificates` | Login required | Student certificate list |
| `/dashboard/event/<id>/certificate/view` | Login required | Full certificate HTML page |
| `/dashboard/certificate/<cert_id>/download/` | Login required | PDF download (Redis cached) |
| `/certificate/verify/<cert_id>/` | **Public** | Verification page (QR target) |

---

## 7. Admin Workflow

1. **Create Signatories** → Admin → Signatories → Add (upload transparent PNG signature)
2. **Create Template** → Admin → Certificate Templates → Add
   - Choose layout: `Angaar Dark (Fire Theme)`
   - Write `body_text` with `{student_name}`, `{event_name}` placeholders
   - Add Signatories inline (set order: 0 = leftmost)
3. **Create Event** → Admin → Events → assign template
4. **Bulk import certificates** → Admin → Certificates → Import (CSV: `email, event_code`)
5. **Approve** → select certs → action: `✅ Approve selected certificates`
6. **Pre-warm cache** (optional) → action: `🔥 Pre-generate PDFs (Celery async)`

---

## 8. Google Fonts in WeasyPrint

The `angaar_dark.html` template uses `@import` from Google Fonts.
WeasyPrint fetches these at generation time — your VPS needs outbound HTTPS.

If your VPS has no internet access, download fonts and serve them as static files:
```
Cinzel          → /static/fonts/Cinzel.woff2
Cormorant Garamond → /static/fonts/CormorantGaramond.woff2
Rajdhani        → /static/fonts/Rajdhani.woff2
```
Then replace `@import url(...)` in `angaar_dark.html` with local `@font-face` rules.

---

## 9. Signature Image Guidelines

- Format: PNG with **transparent background**
- Size: 400×150 px recommended (will be displayed at ~120×45 px on cert)
- Upload via Admin → Signatories → signature_image field
- On the certificate, signatures appear in `order` sequence (left to right)
