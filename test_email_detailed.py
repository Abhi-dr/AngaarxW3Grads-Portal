import os
import django
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')
django.setup()

def test_detailed_email():
    subject = 'Detailed Test Email - The Angaar Batch'
    from_email = 'noreply@theangaarbatch.in'
    to_email = ['himanshudev@gmail.com'] # Using the same test email as before
    
    from_name = "The Angaar Batch "
    from_email_full = f"{from_name} <{from_email}>"

    html_content = """
    <html>
    <body>
        <h1>Detailed Test Email</h1>
        <p>This mimics the verification email structure.</p>
    </body>
    </html>
    """

    try:
        print(f"Attempting to send email from: {from_email_full}")
        email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
        email.attach_alternative(html_content, 'text/html')
        email.send()
        print("Email sent successfully!")
    except Exception as e:
        import traceback
        print("FAILED TO SEND EMAIL:")
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_email()
