"""View tests for the reportcards app."""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import GradingPeriod, SchoolYear, Student, Subject
from .tests import make_period, make_school_year, make_student, make_subject


class AuthTestCase(TestCase):
    """Base for view tests: creates a staff user and logs in."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='teacher', password='test-pass-123')
        self.client.login(username='teacher', password='test-pass-123')


class LoginTests(TestCase):
    def test_home_redirects_anonymous_to_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log in')

    def test_login_flow(self):
        User.objects.create_user(username='teacher', password='test-pass-123')
        response = self.client.post(reverse('login'), {
            'username': 'teacher', 'password': 'test-pass-123',
        })
        self.assertRedirects(response, reverse('home'))

    def test_logout_redirects_to_login(self):
        User.objects.create_user(username='teacher', password='test-pass-123')
        self.client.login(username='teacher', password='test-pass-123')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class HomeViewTests(AuthTestCase):
    def test_lists_students(self):
        make_student(name='Gabriel Miller')
        make_student(name='Ada Lovelace', dob=datetime.date(2012, 12, 10))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gabriel Miller')
        self.assertContains(response, 'Ada Lovelace')

    def test_empty_state(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'No students yet')

    def test_report_card_link_when_year_exists(self):
        student = make_student()
        year = make_school_year()
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('card_entry', args=[student.pk, year.pk]))

    def test_no_report_card_link_without_year(self):
        make_student()
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, '/cards/')


class StudentCrudTests(AuthTestCase):
    def test_create_student(self):
        response = self.client.post(reverse('student_add'), {
            'name': 'Gabriel Miller', 'date_of_birth': '2013-02-07',
        })
        self.assertRedirects(response, reverse('home'))
        student = Student.objects.get()
        self.assertEqual(student.name, 'Gabriel Miller')
        self.assertEqual(student.date_of_birth, datetime.date(2013, 2, 7))

    def test_create_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('student_add'))
        self.assertEqual(response.status_code, 302)

    def test_edit_student(self):
        student = make_student()
        response = self.client.post(reverse('student_edit', args=[student.pk]), {
            'name': 'Gabriel A. Miller', 'date_of_birth': '2013-02-07',
        })
        self.assertRedirects(response, reverse('home'))
        student.refresh_from_db()
        self.assertEqual(student.name, 'Gabriel A. Miller')

    def test_delete_student(self):
        student = make_student()
        response = self.client.post(reverse('student_delete', args=[student.pk]))
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Student.objects.exists())

    def test_invalid_form_re_renders(self):
        response = self.client.post(reverse('student_add'), {
            'name': '', 'date_of_birth': 'not-a-date',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.exists())


class SubjectCrudTests(AuthTestCase):
    def test_list_groups_core_and_resources(self):
        make_subject(name='Language Arts', category=Subject.Category.CORE)
        make_subject(name='Foreign Language', category=Subject.Category.RESOURCE, order=2)
        response = self.client.get(reverse('subject_list'))
        self.assertContains(response, 'Language Arts')
        self.assertContains(response, 'Foreign Language')
        self.assertContains(response, 'Core Subjects')
        self.assertContains(response, 'Resources')

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('subject_list'))
        self.assertEqual(response.status_code, 302)

    def test_create_subject(self):
        response = self.client.post(reverse('subject_add'), {
            'name': 'Humanities', 'category': 'core', 'order': 4, 'active': 'on',
        })
        self.assertRedirects(response, reverse('subject_list'))
        subject = Subject.objects.get()
        self.assertEqual(subject.name, 'Humanities')
        self.assertEqual(subject.category, 'core')

    def test_edit_subject(self):
        subject = make_subject(name='Math')
        response = self.client.post(reverse('subject_edit', args=[subject.pk]), {
            'name': 'Math: Pre-Algebra', 'category': 'core', 'order': 2, 'active': 'on',
        })
        self.assertRedirects(response, reverse('subject_list'))
        subject.refresh_from_db()
        self.assertEqual(subject.name, 'Math: Pre-Algebra')

    def test_deactivate_via_edit(self):
        subject = make_subject()
        self.client.post(reverse('subject_edit', args=[subject.pk]), {
            'name': subject.name, 'category': 'core', 'order': 1,
        })
        subject.refresh_from_db()
        self.assertFalse(subject.active)

    def test_delete_subject(self):
        subject = make_subject()
        response = self.client.post(reverse('subject_delete', args=[subject.pk]))
        self.assertRedirects(response, reverse('subject_list'))
        self.assertFalse(Subject.objects.exists())


class SchoolYearCrudTests(AuthTestCase):
    def test_list_shows_years(self):
        make_school_year(label='2025-26')
        response = self.client.get(reverse('year_list'))
        self.assertContains(response, '2025-26')

    def test_create_year(self):
        response = self.client.post(reverse('year_add'), {
            'label': '2025-26',
            'faculty_1': 'Catherine Hall, Middle School Faculty',
            'faculty_2': 'Valerie de Grood, Middle School Faculty',
        })
        year = SchoolYear.objects.get()
        self.assertRedirects(response, reverse('year_edit', args=[year.pk]))
        self.assertEqual(year.label, '2025-26')

    def test_edit_year_with_period_formset(self):
        year = make_school_year()
        period = make_period(year, name='Quarter 1', order=1)
        data = {
            'label': '2025-26',
            'faculty_1': '', 'faculty_2': '',
            'periods-TOTAL_FORMS': '2',
            'periods-INITIAL_FORMS': '1',
            'periods-MIN_NUM_FORMS': '0',
            'periods-MAX_NUM_FORMS': '1000',
            'periods-0-id': str(period.pk),
            'periods-0-name': 'Quarter 1',
            'periods-0-order': '1',
            'periods-0-start_date': '2025-09-02',
            'periods-0-end_date': '2025-11-07',
            'periods-1-id': '',
            'periods-1-name': 'Quarter 2',
            'periods-1-order': '2',
            'periods-1-start_date': '',
            'periods-1-end_date': '',
        }
        response = self.client.post(reverse('year_edit', args=[year.pk]), data)
        self.assertRedirects(response, reverse('year_list'))
        self.assertEqual(year.periods.count(), 2)
        self.assertTrue(GradingPeriod.objects.filter(school_year=year, name='Quarter 2').exists())

    def test_edit_year_renders_existing_periods(self):
        year = make_school_year()
        make_period(year, name='Quarter 0', order=0)
        response = self.client.get(reverse('year_edit', args=[year.pk]))
        self.assertContains(response, 'Quarter 0')

    def test_delete_year(self):
        year = make_school_year()
        response = self.client.post(reverse('year_delete', args=[year.pk]))
        self.assertRedirects(response, reverse('year_list'))
        self.assertFalse(SchoolYear.objects.exists())
