"""Tests for the printable report card page."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AttendanceRecord, Grade, ReportCard, Subject
from .tests import make_period, make_school_year, make_student, make_subject


class CardPrintTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='teacher', password='test-pass-123')
        self.client.login(username='teacher', password='test-pass-123')
        self.student = make_student()  # Gabriel Miller, DOB 2013-02-07
        self.year = make_school_year()
        self.year.faculty_1 = 'Catherine Hall, Middle School Faculty'
        self.year.faculty_2 = 'Valerie de Grood, Middle School Faculty'
        self.year.save()
        self.q1 = make_period(self.year, name='Quarter 1', order=1)
        self.math = make_subject(name='Math: Pre-Algebra', category=Subject.Category.CORE)
        self.card = ReportCard.objects.create(student=self.student, school_year=self.year)
        self.card.snapshot_subjects()
        Grade.objects.create(
            report_card=self.card,
            card_subject=self.card.card_subjects.get(name='Math: Pre-Algebra'),
            grading_period=self.q1,
            assessment='83%', designation='L', work_habits='R')
        AttendanceRecord.objects.create(
            report_card=self.card, grading_period=self.q1, absences=3, tardies=1)

    def url(self):
        return reverse('card_print', args=[self.card.pk])

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_renders_header_and_student(self):
        response = self.client.get(self.url())
        self.assertContains(response, 'Pines Montessori School')
        self.assertContains(response, 'Middle School Report Card')
        self.assertContains(response, 'Gabriel Miller')
        self.assertContains(response, 'February 7, 2013')

    def test_renders_grades(self):
        response = self.client.get(self.url())
        self.assertContains(response, 'Math: Pre-Algebra')
        self.assertContains(response, '83%')
        self.assertContains(response, 'Quarter 1')
        self.assertContains(response, '9/2/25-11/7/25')

    def test_renders_attendance_and_signatures(self):
        response = self.client.get(self.url())
        self.assertContains(response, 'Attendance Report')
        self.assertContains(response, 'Catherine Hall, Middle School Faculty')
        self.assertContains(response, 'Valerie de Grood, Middle School Faculty')

    def test_renders_legend(self):
        response = self.client.get(self.url())
        self.assertContains(response, 'M=Mastered, C=Competent, I=Improving, R=Reminders needed')
        self.assertContains(response, 'Dsgn=Designation')

    def test_report_card_shows_designation_letter(self):
        response = self.client.get(self.url())
        self.assertContains(response, '<td>L</td>', html=True)

    def test_print_uses_snapshot_after_subject_rename(self):
        self.math.name = 'Math: Algebra I'
        self.math.save()
        response = self.client.get(self.url())
        self.assertContains(response, 'Math: Pre-Algebra')
        self.assertNotContains(response, 'Math: Algebra I')
        self.assertContains(response, '83%')
