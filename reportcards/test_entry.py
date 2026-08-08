"""Tests for the report card entry (grade grid + attendance) view."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AttendanceRecord, Grade, ReportCard, Subject
from .tests import make_period, make_school_year, make_student, make_subject


class EntryTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='teacher', password='test-pass-123')
        self.client.login(username='teacher', password='test-pass-123')
        self.student = make_student()
        self.year = make_school_year()
        self.q0 = make_period(self.year, name='Quarter 0', order=0)
        self.q1 = make_period(self.year, name='Quarter 1', order=1)
        self.language_arts = make_subject(name='Language Arts', category=Subject.Category.CORE)
        self.electives = make_subject(name='Electives', category=Subject.Category.RESOURCE, order=2)

    def entry_url(self):
        return reverse('card_entry', args=[self.student.pk, self.year.pk])


class CardEntryGetTests(EntryTestCase):
    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.entry_url())
        self.assertEqual(response.status_code, 302)

    def test_creates_report_card_on_first_visit(self):
        self.assertFalse(ReportCard.objects.exists())
        response = self.client.get(self.entry_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ReportCard.objects.filter(student=self.student, school_year=self.year).exists())

    def test_renders_subjects_periods_and_inputs(self):
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Language Arts')
        self.assertContains(response, 'Electives')
        self.assertContains(response, 'Quarter 0')
        self.assertContains(response, 'Quarter 1')
        self.assertContains(response, f'grade-{self.language_arts.pk}-{self.q1.pk}-assessment')
        self.assertContains(response, f'att-{self.q1.pk}-absences')

    def test_designation_column_header_and_full_word_options(self):
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Designation')
        self.assertContains(response, '>Level</option>')
        self.assertContains(response, '>Advanced</option>')
        self.assertContains(response, '>Level/Modified</option>')
        self.assertContains(response, '>Modified</option>')

    def test_inactive_subject_not_rendered(self):
        self.language_arts.active = False
        self.language_arts.save()
        response = self.client.get(self.entry_url())
        self.assertNotContains(response, 'Language Arts')

    def test_shows_existing_values(self):
        card = ReportCard.objects.create(student=self.student, school_year=self.year)
        Grade.objects.create(
            report_card=card, subject=self.language_arts, grading_period=self.q1,
            assessment='83%', designation='L', work_habits='R')
        response = self.client.get(self.entry_url())
        self.assertContains(response, '83%')


class CardEntryPostTests(EntryTestCase):
    def post_data(self, **overrides):
        data = {
            f'grade-{self.language_arts.pk}-{self.q1.pk}-assessment': 'INC',
            f'grade-{self.language_arts.pk}-{self.q1.pk}-designation': 'L',
            f'grade-{self.language_arts.pk}-{self.q1.pk}-work_habits': 'R',
            f'att-{self.q1.pk}-absences': '3',
            f'att-{self.q1.pk}-tardies': '0',
        }
        data.update(overrides)
        return data

    def test_saves_grades_and_attendance(self):
        response = self.client.post(self.entry_url(), self.post_data())
        self.assertRedirects(response, self.entry_url())
        card = ReportCard.objects.get()
        grade = Grade.objects.get(report_card=card, subject=self.language_arts, grading_period=self.q1)
        self.assertEqual(grade.assessment, 'INC')
        self.assertEqual(grade.designation, 'L')
        self.assertEqual(grade.work_habits, 'R')
        att = AttendanceRecord.objects.get(report_card=card, grading_period=self.q1)
        self.assertEqual(att.absences, 3)
        self.assertEqual(att.tardies, 0)

    def test_updates_existing_values(self):
        self.client.post(self.entry_url(), self.post_data())
        self.client.post(self.entry_url(), self.post_data(**{
            f'grade-{self.language_arts.pk}-{self.q1.pk}-assessment': '85%',
            f'att-{self.q1.pk}-absences': '1',
        }))
        card = ReportCard.objects.get()
        grade = Grade.objects.get(report_card=card, subject=self.language_arts, grading_period=self.q1)
        self.assertEqual(grade.assessment, '85%')
        self.assertEqual(
            AttendanceRecord.objects.get(report_card=card, grading_period=self.q1).absences, 1)
        # No duplicate rows created
        self.assertEqual(Grade.objects.filter(
            report_card=card, subject=self.language_arts, grading_period=self.q1).count(), 1)

    def test_invalid_choice_values_stored_blank(self):
        self.client.post(self.entry_url(), self.post_data(**{
            f'grade-{self.language_arts.pk}-{self.q1.pk}-designation': 'BOGUS',
            f'grade-{self.language_arts.pk}-{self.q1.pk}-work_habits': 'Z',
        }))
        grade = Grade.objects.get(subject=self.language_arts, grading_period=self.q1)
        self.assertEqual(grade.designation, '')
        self.assertEqual(grade.work_habits, '')

    def test_non_numeric_attendance_stored_zero(self):
        self.client.post(self.entry_url(), self.post_data(**{
            f'att-{self.q1.pk}-absences': 'three',
        }))
        att = AttendanceRecord.objects.get(grading_period=self.q1)
        self.assertEqual(att.absences, 0)

    def test_blank_cells_left_empty(self):
        self.client.post(self.entry_url(), self.post_data())
        card = ReportCard.objects.get()
        grade = Grade.objects.get(report_card=card, subject=self.electives, grading_period=self.q0)
        self.assertEqual(grade.assessment, '')
