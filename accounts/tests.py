from django.test import TestCase, Client
from django.urls import reverse
from .models import Student, EmailVerificationToken
from django.core import mail

class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_registration_creates_inactive_user_and_sends_email(self):
        # 1. Register a new user
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })

        # 2. Check response - should render verification_sent page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/verification_sent.html')

        # 3. Check user created but inactive
        user = Student.objects.get(username='testuser')
        self.assertFalse(user.is_active)

        # 4. Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify Your Email', mail.outbox[0].subject)
        self.assertIn(user.email, mail.outbox[0].to)

        # 5. Check token created
        token = EmailVerificationToken.objects.filter(user=user).first()
        self.assertIsNotNone(token)

    def test_verification_activates_user(self):
        # 1. Create a user manually (inactive)
        user = Student.objects.create(
            username='verifyuser',
            email='verify@example.com',
            first_name='Verify',
            is_active=False
        )
        user.set_password('password123')
        user.save()

        # 2. Generate token
        token_str = EmailVerificationToken.create_token(user)

        # 3. Visit verification link
        verify_url = reverse('verify_email', args=[user.pk, token_str])
        response = self.client.get(verify_url, follow=True) # follow redirect

        # 4. Check user activated
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # 5. Check redirected to dashboard (student view)
        self.assertRedirects(response, reverse('student'))
        
        # 6. Check welcome email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome', mail.outbox[0].subject)

    def test_invalid_token_fails(self):
        user = Student.objects.create(username='failuser', email='fail@example.com', is_active=False)
        invalid_url = reverse('verify_email', args=[user.pk, 'invalidtoken'])
        
        response = self.client.get(invalid_url)
        
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        # Check redirects to login or shows error
        self.assertRedirects(response, reverse('login')) # View redirects to login on fail
