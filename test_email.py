import os
import django
from django.core.mail import send_mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')
django.setup()

try:
    print("Attempting to send test email...")
    send_mail(
        'Test Email from Angaar Batch',
        'If you receive this, your email configuration is working!',
        'noreply@theangaarbatch.in',
        ['himanshudev@gmail.com'], # Replace with a test email if needed
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    import traceback
    print("FAILED TO SEND EMAIL:")
    traceback.print_exc()
