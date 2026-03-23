from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
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
