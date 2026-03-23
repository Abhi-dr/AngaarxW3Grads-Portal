from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from practice.models import MCQQuestion, Question
from student.models import Assignment, Course, CourseSheet


class AdminReorderSheetItemsTests(TestCase):
	def setUp(self):
		self.admin_user = CustomUser.objects.create_user(
			email='admin@example.com',
			password='testpass123',
			role='admin',
			username='admin_user'
		)
		self.admin_user.is_staff = True
		self.admin_user.save()
		self.client.force_login(self.admin_user)

		self.course = Course.objects.create(name='JOVAC Test', description='Course for testing')
		self.sheet = CourseSheet.objects.create(name='Sheet A', created_by=self.admin_user)
		self.sheet.course.add(self.course)

		course_ct = ContentType.objects.get_for_model(Course)
		self.assignment = Assignment.objects.create(
			content_type=course_ct,
			object_id=self.course.id,
			title='Assignment 1',
			description='Desc',
			assignment_type='Coding',
			status='Draft',
			max_score=100,
			is_tutorial=False,
		)
		self.assignment.course_sheets.add(self.sheet)

		self.mcq = MCQQuestion.objects.create(
			question_text='What is Python?',
			option_a='A',
			option_b='B',
			option_c='C',
			option_d='D',
			correct_option='A',
		)
		self.sheet.mcq_questions.add(self.mcq)

		self.coding_question = Question.objects.create(
			title='Two Sum',
			description='Solve two sum',
			difficulty_level='Easy',
		)
		self.sheet.coding_questions.add(self.coding_question)

	def test_reorder_page_shows_mcq_and_other_item_types(self):
		response = self.client.get(
			reverse('reorder_course_sheet_assignments', kwargs={'slug': self.sheet.slug})
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'data-id="assignment_{self.assignment.id}"')
		self.assertContains(response, f'data-id="mcq_{self.mcq.id}"')
		self.assertContains(response, f'data-id="coding_{self.coding_question.id}"')

	def test_update_order_persists_mixed_item_ids(self):
		url = reverse('update_course_sheet_order', kwargs={'id': self.sheet.id})
		response = self.client.post(url, {
			'order[]': [
				f'mcq_{self.mcq.id}',
				f'assignment_{self.assignment.id}',
				f'coding_{self.coding_question.id}',
			]
		})

		self.assertEqual(response.status_code, 200)
		self.sheet.refresh_from_db()
		self.assertEqual(
			self.sheet.custom_order,
			{
				f'mcq_{self.mcq.id}': 0,
				f'assignment_{self.assignment.id}': 1,
				f'coding_{self.coding_question.id}': 2,
			}
		)

	def test_update_order_accepts_legacy_numeric_assignment_ids(self):
		url = reverse('update_course_sheet_order', kwargs={'id': self.sheet.id})
		response = self.client.post(url, {
			'order[]': [str(self.assignment.id)]
		})

		self.assertEqual(response.status_code, 200)
		self.sheet.refresh_from_db()
		self.assertEqual(self.sheet.custom_order, {f'assignment_{self.assignment.id}': 0})
