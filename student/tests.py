from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from home.models import FlamesCourse, FlamesEdition
from practice.models import MCQQuestion
from student.models import Assignment, Course, CourseSheet


class JovacMcqNavigationTests(TestCase):
	def setUp(self):
		self.student = CustomUser.objects.create_user(
			email='student@example.com',
			password='testpass123',
			role='student',
			username='student_user'
		)
		self.client.force_login(self.student)

		self.course = Course.objects.create(name='JOVAC Student Course', description='desc')
		self.sheet = CourseSheet.objects.create(
			name='Mixed Order Sheet',
			created_by=self.student,
			is_enabled=True,
			is_approved=True,
		)
		self.sheet.course.add(self.course)

		self.mcq = MCQQuestion.objects.create(
			question_text='What is 2 + 2?',
			option_a='3',
			option_b='4',
			option_c='5',
			option_d='6',
			correct_option='B',
			is_approved=True,
		)
		self.sheet.mcq_questions.add(self.mcq)

		course_ct = ContentType.objects.get_for_model(Course)
		self.assignment = Assignment.objects.create(
			content_type=course_ct,
			object_id=self.course.id,
			title='Assignment After MCQ',
			description='Solve task',
			assignment_type='Coding',
			status='Published',
			max_score=100,
			is_tutorial=False,
		)
		self.assignment.course_sheets.add(self.sheet)

		self.sheet.custom_order = {
			f'mcq_{self.mcq.id}': 0,
			f'assignment_{self.assignment.id}': 1,
		}
		self.sheet.save()

	def test_jovac_mcq_page_has_next_url_for_next_assignment(self):
		response = self.client.get(
			reverse('mcq_question', kwargs={'sheet_slug': self.sheet.slug, 'slug': self.mcq.slug})
		)

		self.assertEqual(response.status_code, 200)
		expected_next = f"{reverse('submit_assignment', kwargs={'assignment_id': self.assignment.id})}?sheet={self.sheet.slug}"
		self.assertEqual(response.context['next_question_url'], expected_next)


class FlamesCourseOrderingStudentTests(TestCase):
	def setUp(self):
		self.student = CustomUser.objects.create_user(
			email='ordered-student@example.com',
			password='testpass123',
			role='student',
			username='ordered_student'
		)
		self.client.force_login(self.student)

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

	def test_student_flames_dashboard_available_courses_use_display_order(self):
		FlamesCourse.objects.create(
			title='Zeta Batch',
			subtitle='zeta',
			description='desc',
			slug='zeta-batch',
			edition=self.active_edition,
			is_active=True,
			display_order=1,
		)
		FlamesCourse.objects.create(
			title='Alpha Batch',
			subtitle='alpha',
			description='desc',
			slug='alpha-batch',
			edition=self.active_edition,
			is_active=True,
			display_order=2,
		)

		response = self.client.get(reverse('student_flames'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			[course.title for course in response.context['available_courses']],
			['Zeta Batch', 'Alpha Batch']
		)

	def test_student_flames26_dashboard_available_courses_use_display_order(self):
		FlamesCourse.objects.create(
			title='Web Track',
			subtitle='web',
			description='desc',
			slug='web-track',
			edition=self.edition_2026,
			is_active=True,
			display_order=2,
		)
		FlamesCourse.objects.create(
			title='AI Track',
			subtitle='ai',
			description='desc',
			slug='ai-track-student',
			edition=self.edition_2026,
			is_active=True,
			display_order=1,
		)

		response = self.client.get(reverse('student_flames26'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			[course.title for course in response.context['available_courses']],
			['AI Track', 'Web Track']
		)
