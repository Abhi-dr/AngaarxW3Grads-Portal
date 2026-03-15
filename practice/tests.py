from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from accounts.models import CustomUser
from practice.models import Streak


class StreakLogicTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="streak_user@example.com",
            password="testpass123",
            first_name="Streak",
            role="student",
        )

    def test_default_streak_stays_one(self):
        streak = Streak.get_user_streak(self.user)
        self.assertEqual(streak.current_streak, 1)

    def test_consecutive_day_increments_streak(self):
        today = date(2026, 3, 15)
        streak = Streak.objects.create(
            user=self.user,
            current_streak=4,
            previous_streak=0,
            last_submission_date=today - timedelta(days=1),
        )

        with patch("practice.models.timezone.localdate", return_value=today):
            streak.update_streak()

        streak.refresh_from_db()
        self.assertEqual(streak.current_streak, 5)
        self.assertEqual(streak.previous_streak, 0)
        self.assertEqual(streak.last_submission_date, today)

    def test_can_restore_after_missing_exactly_one_day(self):
        today = date(2026, 3, 15)
        streak = Streak.objects.create(
            user=self.user,
            current_streak=5,
            previous_streak=0,
            last_submission_date=today - timedelta(days=2),
        )

        with patch("practice.models.timezone.localdate", return_value=today):
            streak.update_streak()

        streak.refresh_from_db()
        self.assertEqual(streak.current_streak, 0)
        self.assertEqual(streak.previous_streak, 5)

        with patch("practice.models.timezone.localdate", return_value=today):
            self.assertTrue(streak.can_restore_streak())

    def test_restore_streak_sets_expected_values(self):
        today = date(2026, 3, 15)
        streak = Streak.objects.create(
            user=self.user,
            current_streak=0,
            previous_streak=6,
            last_submission_date=today,
        )

        with patch("practice.models.timezone.localdate", return_value=today):
            restored = streak.restore_streak()

        streak.refresh_from_db()
        self.assertTrue(restored)
        self.assertEqual(streak.current_streak, 7)
        self.assertEqual(streak.previous_streak, 0)
        self.assertEqual(streak.last_submission_date, today)

    def test_restore_not_allowed_when_window_expired(self):
        today = date(2026, 3, 15)
        streak = Streak.objects.create(
            user=self.user,
            current_streak=0,
            previous_streak=6,
            last_submission_date=today - timedelta(days=2),
        )

        with patch("practice.models.timezone.localdate", return_value=today):
            self.assertFalse(streak.can_restore_streak())
