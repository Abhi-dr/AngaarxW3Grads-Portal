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
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #0f172a; color: #f8fafc;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #0f172a; padding: 30px; text-align: center; border-bottom: 2px solid #3498DB;">
                <img src="https://theangaarbatch.in/static/img/home/angaari_logo.png" alt="The Angaar Batch Logo" style="width: 100px;">
                <h1 style="color: #ffffff; margin-top: 15px; font-size: 24px;">Welcome to The Angaar Batch🔥</h1>
            </div>
            <div style="padding: 40px 30px; text-align: center;">
                <h2 style="color: #ffffff; font-size: 22px; margin-top: 0;">Hi {name}!</h2>
                <p style="font-size: 16px; color: #cbd5e1; line-height: 1.6;">We're thrilled to have you on board. Get ready to dive into an exciting journey of learning, coding, and growth.</p>
                <p style="font-size: 16px; color: #cbd5e1; line-height: 1.6;">Stay curious, stay passionate, and let's build something amazing together!</p>
                <a href="https://theangaarbatch.in/accounts/login" style="background-color: #3498DB; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; font-weight: bold; display: inline-block; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(52, 152, 219, 0.4);">Go to Dashboard</a>
                <p style="font-size: 14px; color: #94a3b8; margin-top: 35px; border-top: 1px solid #334155; padding-top: 20px;">If you have any questions, feel free to reply to this email.</p>
                <p style="font-size: 14px; color: #94a3b8; font-weight: bold;">Happy Coding! 🚀</p>
            </div>
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
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #0f172a; color: #f8fafc;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #0f172a; padding: 30px; text-align: center; border-bottom: 2px solid #ff6b35;">
                <img src="https://theangaarbatch.in/static/img/home/angaari_logo.png" alt="The Angaar Batch Logo" style="width: 100px;">
                <h1 style="color: #ff6b35; margin-top: 15px; font-size: 24px; text-shadow: 0 0 10px rgba(255,107,53,0.3);">🔥 BIGGER, BETTER, BOLDER! 🔥</h1>
            </div>
            <div style="padding: 40px 30px; text-align: center;">
                <h2 style="color: #ffffff; font-size: 22px; margin-top: 0;">{name}, You're All Set!</h2>
                <div style="color: #ff6b35; font-weight: bold; margin-bottom: 20px;">{course_info}</div>
                <div style="background-color: rgba(255,107,53,0.1); border-left: 4px solid #ff6b35; padding: 20px; margin: 25px 0; text-align: left; border-radius: 0 8px 8px 0;">
                    <p style="font-size: 17px; color: #ffffff; font-weight: bold; margin-top: 0;">The fire has been lit! Your payment is confirmed and your spot is secured.</p>
                    <p style="font-size: 16px; color: #cbd5e1; line-height: 1.6;">Get ready to ignite your potential and transform your skills into blazing talent.</p>
                </div>
                <p style="font-size: 16px; color: #cbd5e1; line-height: 1.6;">This is where ordinary coders become extraordinary developers.</p>
                <p style="font-size: 16px; color: #cbd5e1; line-height: 1.6; font-style: italic;">Remember: The flame that burns brightest requires the most fuel. Bring your dedication!</p>
                <a href="https://theangaarbatch.in/accounts/login" style="background-color: #ff6b35; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; font-weight: bold; display: inline-block; margin-top: 25px; box-shadow: 0 4px 10px rgba(255, 107, 53, 0.4);">ACCESS YOUR DASHBOARD</a>
                <div style="margin-top: 40px; padding-top: 25px; border-top: 1px solid #334155;">
                    <p style="font-size: 14px; color: #94a3b8; margin-bottom: 10px;">Mark your calendar! Classes begin soon. Check your dashboard for schedule details.</p>
                    <p style="font-size: 14px; color: #94a3b8;">Questions? Reach out to us at theangaarbatch@gmail.com</p>
                    <p style="font-size: 16px; color: #ff6b35; font-weight: bold; margin-top: 15px;">READY TO BURN BRIGHT! 🚀🔥</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"\nFLAMES CONFIRMATION EMAIL SENT! to {to_email} \n")






