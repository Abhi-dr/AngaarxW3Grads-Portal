from django.test import TestCase

from student.models import Course


class CourseSlugGenerationTests(TestCase):
	def test_duplicate_course_names_get_unique_slugs(self):
		first = Course.objects.create(name='Block Chain', description='d1')
		second = Course.objects.create(name='Block Chain', description='d2')

		self.assertEqual(first.slug, 'block-chain')
		self.assertEqual(second.slug, 'block-chain-1')

	def test_special_character_name_still_gets_valid_slug(self):
		course = Course.objects.create(name='@@@', description='symbols')
		self.assertEqual(course.slug, 'course')
