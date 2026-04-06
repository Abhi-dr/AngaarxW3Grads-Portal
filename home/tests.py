from django.test import TestCase
from django.urls import reverse

from home.models import FlamesCourse, FlamesEdition


class FlamesCourseOrderingHomeTests(TestCase):
    def setUp(self):
        self.active_edition = FlamesEdition.objects.create(
            year=2025,
            name='FLAMES 25',
            is_active=True,
            registration_open=True,
        )
        self.edition_2026 = FlamesEdition.objects.create(
            year=2026,
            name='FLAMES 26',
            is_active=False,
            registration_open=True,
        )

    def test_active_flames_page_uses_display_order(self):
        FlamesCourse.objects.create(
            title='Zebra Track',
            subtitle='zebra',
            description='desc',
            slug='zebra-track',
            edition=self.active_edition,
            is_active=True,
            display_order=1,
        )
        FlamesCourse.objects.create(
            title='Alpha Track',
            subtitle='alpha',
            description='desc',
            slug='alpha-track',
            edition=self.active_edition,
            is_active=True,
            display_order=2,
        )

        response = self.client.get(reverse('flames'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [course.title for course in response.context['courses']],
            ['Zebra Track', 'Alpha Track']
        )

    def test_flames26_page_uses_display_order(self):
        FlamesCourse.objects.create(
            title='Web Dev',
            subtitle='web',
            description='desc',
            slug='web-dev',
            edition=self.edition_2026,
            is_active=True,
            display_order=2,
        )
        FlamesCourse.objects.create(
            title='AI Track',
            subtitle='ai',
            description='desc',
            slug='ai-track',
            edition=self.edition_2026,
            is_active=True,
            display_order=1,
        )

        response = self.client.get(reverse('flames26'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [course.title for course in response.context['courses']],
            ['AI Track', 'Web Dev']
        )
