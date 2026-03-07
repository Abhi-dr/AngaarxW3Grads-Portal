"""
student/tests_profile_api.py
Tests for the Student Profile REST API (DRF endpoints).

Run with:
    python manage.py test student.tests_profile_api --verbosity=2
"""

import io
from PIL import Image

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def create_test_user(username="testuser", password="testpass123", **kwargs):
    """Creates and returns an active CustomUser for testing."""
    defaults = {
        "email": f"{username}@test.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
    }
    defaults.update(kwargs)
    user = CustomUser.objects.create_user(
        email=defaults.pop("email"),
        password=password,
        username=username,
        **defaults,
    )
    return user


def make_small_image_file(name="test.jpg", size=(100, 100), fmt="JPEG"):
    """Creates an in-memory image file suitable for upload tests."""
    img = Image.new("RGB", size, color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    buf.name = name
    return buf


# ─────────────────────────────────────────────────────────────────
# Test Suite
# ─────────────────────────────────────────────────────────────────

class ProfileAPITests(TestCase):
    """
    Covers all 5 Profile API endpoints:
      GET    /dashboard/api/profile/
      PATCH  /dashboard/api/profile/
      DELETE /dashboard/api/profile/
      POST   /dashboard/api/profile/change-password/
      POST   /dashboard/api/profile/upload-picture/
    """

    def setUp(self):
        self.user = create_test_user(
            username="profiletester",
            password="oldpass123",
            first_name="John",
            last_name="Doe",
        )

        # URL names (defined in student/urls.py)
        self.profile_url       = reverse("api_profile")
        self.change_pass_url   = reverse("api_change_password")
        self.upload_pic_url    = reverse("api_upload_picture")

    # ── Utility ──────────────────────────────────────────────────

    def _login(self):
        self.client.login(username=self.user.email, password="oldpass123")

    # ─────────────────────────────────────────────────────────────
    # GET  /dashboard/api/profile/
    # ─────────────────────────────────────────────────────────────

    def test_get_profile_unauthenticated(self):
        """Anonymous users must receive 403."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 403)

    def test_get_profile_authenticated(self):
        """Authenticated user gets their profile data."""
        self._login()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["first_name"], "John")
        self.assertIn("profile_score", data)
        self.assertIn("coins", data)

    # ─────────────────────────────────────────────────────────────
    # PATCH  /dashboard/api/profile/
    # ─────────────────────────────────────────────────────────────

    def test_patch_profile_valid(self):
        """PATCH updates fields and awards coins for new data."""
        self._login()
        response = self.client.patch(
            self.profile_url,
            data={
                "college": "IIT Delhi",
                "linkedin_id": "https://linkedin.com/in/john",
                "github_id": "https://github.com/john",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["college"], "IIT Delhi")
        self.assertGreater(data["coins_earned"], 0)     # coins awarded for new linkedin + github
        self.user.refresh_from_db()
        self.assertEqual(self.user.college, "IIT Delhi")

    def test_patch_profile_invalid_mobile(self):
        """Mobile number must be exactly 10 digits — returns 400."""
        self._login()
        response = self.client.patch(
            self.profile_url,
            data={"mobile_number": "12345"},             # too short
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mobile_number", response.json())

    def test_patch_profile_partial(self):
        """Only supplied fields are updated; others remain unchanged."""
        self._login()
        original_last = self.user.last_name
        response = self.client.patch(
            self.profile_url,
            data={"first_name": "Jane"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")
        self.assertEqual(self.user.last_name, original_last)   # unchanged

    def test_patch_does_not_update_username_or_coins(self):
        """Read-only fields like username and coins must not be writable."""
        self._login()
        original_username = self.user.username
        original_coins    = self.user.coins
        response = self.client.patch(
            self.profile_url,
            data={"username": "hacker", "coins": 99999},
            content_type="application/json",
        )
        # API should succeed (ignoring read-only fields), not change protected data
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, original_username)
        self.assertEqual(self.user.coins, original_coins)

    # ─────────────────────────────────────────────────────────────
    # POST  /dashboard/api/profile/change-password/
    # ─────────────────────────────────────────────────────────────

    def test_change_password_success(self):
        """Correct old password → password updated."""
        self._login()
        response = self.client.post(
            self.change_pass_url,
            data={
                "old_password": "oldpass123",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

        # Verify password actually changed in DB
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))
        self.assertTrue(self.user.is_changed_password)

    def test_change_password_wrong_old(self):
        """Wrong old password → 400 with appropriate error."""
        self._login()
        response = self.client.post(
            self.change_pass_url,
            data={
                "old_password": "wrongpassword",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.json())

    def test_change_password_mismatch(self):
        """new_password ≠ confirm_password → 400."""
        self._login()
        response = self.client.post(
            self.change_pass_url,
            data={
                "old_password": "oldpass123",
                "new_password": "newpass456",
                "confirm_password": "differentpass",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json())

    def test_change_password_same_as_old(self):
        """new_password == old_password → 400."""
        self._login()
        response = self.client.post(
            self.change_pass_url,
            data={
                "old_password": "oldpass123",
                "new_password": "oldpass123",
                "confirm_password": "oldpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.json())

    def test_change_password_unauthenticated(self):
        """Anonymous users must receive 403."""
        response = self.client.post(
            self.change_pass_url,
            data={
                "old_password": "oldpass123",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    # ─────────────────────────────────────────────────────────────
    # POST  /dashboard/api/profile/upload-picture/
    # ─────────────────────────────────────────────────────────────

    def test_upload_picture_success(self):
        """Valid image file → profile_pic updated, URL returned."""
        self._login()
        img_file = make_small_image_file()
        response = self.client.post(
            self.upload_pic_url,
            data={"profile_pic": img_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile_pic", data)
        self.assertIsNotNone(data["profile_pic"])

    def test_upload_picture_no_file(self):
        """Missing file field → 400."""
        self._login()
        response = self.client.post(self.upload_pic_url, data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    # ─────────────────────────────────────────────────────────────
    # DELETE  /dashboard/api/profile/
    # ─────────────────────────────────────────────────────────────

    def test_delete_account_correct_username(self):
        """Correct username → account deleted, session cleared."""
        self._login()
        user_id = self.user.id
        response = self.client.delete(
            self.profile_url,
            data={"username": self.user.username},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

        # User must no longer exist in DB
        self.assertFalse(CustomUser.objects.filter(id=user_id).exists())

    def test_delete_account_wrong_username(self):
        """Wrong username → 400, account NOT deleted."""
        self._login()
        response = self.client.delete(
            self.profile_url,
            data={"username": "wrongusername"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())

        # User must still exist
        self.assertTrue(CustomUser.objects.filter(id=self.user.id).exists())

    def test_delete_account_unauthenticated(self):
        """Anonymous users must receive 403."""
        response = self.client.delete(
            self.profile_url,
            data={"username": "profiletester"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


# ─────────────────────────────────────────────────────────────────
# Feedback API Test Suite
# ─────────────────────────────────────────────────────────────────

class FeedbackAPITests(TestCase):
    """
    Covers POST /dashboard/api/feedback/
    """

    def setUp(self):
        self.user = create_test_user(
            username="feedbacktester",
            password="testpass123",
        )
        self.feedback_url = reverse("api_feedback")

    def _login(self):
        self.client.login(username=self.user.email, password="testpass123")

    # ── Success ──────────────────────────────────────────────────

    def test_submit_feedback_success(self):
        """Authenticated user submits valid feedback → 201 + message."""
        self._login()
        response = self.client.post(
            self.feedback_url,
            data={"subject": "Great Platform", "message": "I love using this portal!"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("message", data)

        # Confirm the record was actually saved
        from student.models import Feedback
        self.assertTrue(
            Feedback.objects.filter(student=self.user, subject="Great Platform").exists()
        )

    # ── Unauthenticated ──────────────────────────────────────────

    def test_submit_feedback_unauthenticated(self):
        """Anonymous users must receive 403."""
        response = self.client.post(
            self.feedback_url,
            data={"subject": "Test", "message": "Test message"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    # ── Missing / blank fields ───────────────────────────────────

    def test_submit_feedback_missing_subject(self):
        """Missing subject → 400 with field error."""
        self._login()
        response = self.client.post(
            self.feedback_url,
            data={"message": "Some message without a subject"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("subject", response.json())

    def test_submit_feedback_missing_message(self):
        """Missing message → 400 with field error."""
        self._login()
        response = self.client.post(
            self.feedback_url,
            data={"subject": "A subject"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json())

    def test_submit_feedback_subject_too_long(self):
        """Subject longer than 255 chars → 400."""
        self._login()
        response = self.client.post(
            self.feedback_url,
            data={"subject": "x" * 256, "message": "Some message"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("subject", response.json())
