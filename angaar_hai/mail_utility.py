from django.core.mail import EmailMultiAlternatives

# =========================================== WELCOME MAIL =======================================

def send_welcome_mail(to, name):

    subject = 'Welcome to The Angaar Batch!🔥'
    from_email = 'noreply@theangaarbatch.in'
    to_email = [to]
    
    from_name = "The Angaar Batch "
    from_email_full = f"{from_name} <{from_email}>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
        <img src="https://theangaarbatch.in/static/img/home/angaari_logo.png" alt="The Angaar Batch Logo" style="width: 120px; margin-bottom: 20px;">
        <h1 style="color: #2C3E50;">Welcome to The Angaar Batch🔥, {name}!</h1>
        <p style="font-size: 16px; color: #555555;">We're thrilled to have you on board. Get ready to dive into an exciting journey of learning, coding, and growth.</p>
        <p style="font-size: 16px; color: #555555;">Stay curious, stay passionate, and let's build something amazing together!</p>
        <a href="https://theangaarbatch.in/accounts/login" style="background-color: #3498DB; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px; display: inline-block; margin-top: 20px;">Go to Dashboard</a>
        <p style="font-size: 14px; color: #777777; margin-top: 30px;">If you have any questions, feel free to reply to this email.</p>
        <p style="font-size: 14px; color: #777777;">Happy Coding! 🚀</p>
        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"\nEMAIL SENT! to {to_email} \n")

# ================================= FLAMES REGISTRATION PAYMENT MAIL =============================

def send_flames_confirmation_mail(to, name, course_name=None):
    
    subject = 'Your Flames Registration is Confirmed!🔥'
    from_email = 'noreply@theangaarbatch.in'
    to_email = [to]
    
    from_name = "The Angaar Batch"
    from_email_full = f"{from_name} <{from_email}>"

    course_info = ""
    if course_name:
        course_info = f"<p style='font-size: 16px; color: #ff6b35;'><strong>Course: {course_name}</strong></p>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
        <div style="background: linear-gradient(to bottom, #1b1f23, #000000); padding: 25px; text-align: center; border-radius: 10px;">
        <img src="demo_static/img/student/flames25.png" alt="The Angaar Batch Logo" style="width: 15%; margin-bottom: 20px;">
        <h1 style="color: #ff6b35; text-shadow: 0 0 5px rgba(255,107,53,0.3);">🔥BIGGER, BETTER, BOLDER!🔥</h1>
        <h2 style="color: #ffffff;">{name}, You're All Set!</h2>
        <p style="color: #f8f8f8">{course_info}</p>
        <div style="background-color: rgba(255,107,53,0.1); border-left: 4px solid #ff6b35; padding: 15px; margin: 20px 0; text-align: left;">
            <p style="font-size: 17px; color: #f8f8f8; font-weight: bold;">The fire has been lit! Your payment is confirmed and your spot is secured.</p>
            <p style="font-size: 16px; color: #dddddd;">Get ready to ignite your potential and transform your skills into blazing talent.</p>
        </div>
        <p style="font-size: 16px; color: #e0e0e0;">This is where ordinary coders become extraordinary developers.</p>
        <p style="font-size: 16px; color: #e0e0e0;">Remember: The flame that burns brightest requires the most fuel. Bring your dedication!</p>
        <a href="https://theangaarbatch.in/accounts/login" style="background-color: #ff6b35; color: #ffffff; text-decoration: none; padding: 12px 25px; border-radius: 5px; font-size: 16px; display: inline-block; margin-top: 25px; font-weight: bold; box-shadow: 0 4px 8px rgba(255, 107, 53, 0.5); transition: all 0.3s;">ACCESS YOUR DASHBOARD</a>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
            <p style="font-size: 15px; color: #b0b0b0;">Mark your calendar! Classes begin soon. Check your dashboard for schedule details.</p>
            <p style="font-size: 14px; color: #b0b0b0;">Questions? Reach out to us at theangaarbatch@gmail.com</p>
            <p style="font-size: 16px; color: #ff6b35; font-weight: bold; margin-top: 15px;">READY TO BURN BRIGHT! 🚀🔥</p>
        </div>
        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"\nFLAMES CONFIRMATION EMAIL SENT! to {to_email} \n")






