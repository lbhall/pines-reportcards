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
        self.math = make_subject(name='Math', category=Subject.Category.CORE, order=2, subtitle='Pre-Algebra')
        self.electives = make_subject(name='Electives', category=Subject.Category.RESOURCE, order=3)

    def entry_url(self):
        return reverse('card_entry', args=[self.student.pk, self.year.pk])

    def create_card(self):
        """First GET creates the card and snapshots the subjects."""
        self.client.get(self.entry_url())
        return ReportCard.objects.get(student=self.student, school_year=self.year)

    def card_subject(self, card, name):
        return card.card_subjects.get(name=name)


class CardEntryGetTests(EntryTestCase):
    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.entry_url())
        self.assertEqual(response.status_code, 302)

    def test_creates_report_card_with_subject_snapshot_on_first_visit(self):
        self.assertFalse(ReportCard.objects.exists())
        response = self.client.get(self.entry_url())
        self.assertEqual(response.status_code, 200)
        card = ReportCard.objects.get(student=self.student, school_year=self.year)
        self.assertEqual(card.card_subjects.count(), 3)

    def test_renders_editable_subtitle_input(self):
        card = self.create_card()
        math = self.card_subject(card, 'Math')
        response = self.client.get(self.entry_url())
        self.assertContains(response, f'subtitle-{math.pk}')
        self.assertContains(response, 'Pre-Algebra')

    def test_renders_subjects_periods_and_inputs(self):
        card = self.create_card()
        la = self.card_subject(card, 'Language Arts')
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Language Arts')
        self.assertContains(response, 'Electives')
        self.assertContains(response, 'Quarter 0')
        self.assertContains(response, 'Quarter 1')
        self.assertContains(response, f'grade-{la.pk}-{self.q1.pk}-assessment')
        self.assertContains(response, f'att-{self.q1.pk}-absences')

    def test_links_to_year_edit_for_quarter_dates(self):
        response = self.client.get(self.entry_url())
        self.assertContains(response, reverse('year_edit', args=[self.year.pk]))

    def test_designation_column_header_and_full_word_options(self):
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Designation')
        self.assertContains(response, '>Level</option>')
        self.assertContains(response, '>Advanced</option>')
        self.assertContains(response, '>Level/Modified</option>')
        self.assertContains(response, '>Modified</option>')

    def test_subject_inactive_before_card_creation_not_snapshotted(self):
        self.language_arts.active = False
        self.language_arts.save()
        response = self.client.get(self.entry_url())
        self.assertNotContains(response, 'Language Arts')

    def test_subject_deactivated_after_card_creation_still_rendered(self):
        self.create_card()
        self.language_arts.active = False
        self.language_arts.save()
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Language Arts')

    def test_subject_renamed_after_card_creation_keeps_old_name(self):
        self.create_card()
        self.language_arts.name = 'Literature'
        self.language_arts.save()
        response = self.client.get(self.entry_url())
        self.assertContains(response, 'Language Arts')
        self.assertNotContains(response, 'Literature')

    def test_shows_existing_values(self):
        card = self.create_card()
        Grade.objects.create(
            report_card=card, card_subject=self.card_subject(card, 'Language Arts'),
            grading_period=self.q1,
            assessment='83%', designation='L', work_habits='R')
        response = self.client.get(self.entry_url())
        self.assertContains(response, '83%')


class CardEntryPostTests(EntryTestCase):
    def setUp(self):
        super().setUp()
        self.card = self.create_card()
        self.la = self.card_subject(self.card, 'Language Arts')
        self.el = self.card_subject(self.card, 'Electives')

    def post_data(self, **overrides):
        data = {
            f'grade-{self.la.pk}-{self.q1.pk}-assessment': 'INC',
            f'grade-{self.la.pk}-{self.q1.pk}-designation': 'L',
            f'grade-{self.la.pk}-{self.q1.pk}-work_habits': 'R',
            f'att-{self.q1.pk}-absences': '3',
            f'att-{self.q1.pk}-tardies': '0',
        }
        data.update(overrides)
        return data

    def test_saves_grades_and_attendance(self):
        response = self.client.post(self.entry_url(), self.post_data())
        self.assertRedirects(response, self.entry_url())
        grade = Grade.objects.get(card_subject=self.la, grading_period=self.q1)
        self.assertEqual(grade.assessment, 'INC')
        self.assertEqual(grade.designation, 'L')
        self.assertEqual(grade.work_habits, 'R')
        att = AttendanceRecord.objects.get(report_card=self.card, grading_period=self.q1)
        self.assertEqual(att.absences, 3)
        self.assertEqual(att.tardies, 0)

    def test_updates_existing_values(self):
        self.client.post(self.entry_url(), self.post_data())
        self.client.post(self.entry_url(), self.post_data(**{
            f'grade-{self.la.pk}-{self.q1.pk}-assessment': '85%',
            f'att-{self.q1.pk}-absences': '1',
        }))
        grade = Grade.objects.get(card_subject=self.la, grading_period=self.q1)
        self.assertEqual(grade.assessment, '85%')
        self.assertEqual(
            AttendanceRecord.objects.get(
                report_card=self.card, grading_period=self.q1).absences, 1)
        self.assertEqual(Grade.objects.filter(
            card_subject=self.la, grading_period=self.q1).count(), 1)

    def test_invalid_choice_values_stored_blank(self):
        self.client.post(self.entry_url(), self.post_data(**{
            f'grade-{self.la.pk}-{self.q1.pk}-designation': 'BOGUS',
            f'grade-{self.la.pk}-{self.q1.pk}-work_habits': 'Z',
        }))
        grade = Grade.objects.get(card_subject=self.la, grading_period=self.q1)
        self.assertEqual(grade.designation, '')
        self.assertEqual(grade.work_habits, '')

    def test_non_numeric_attendance_stored_zero(self):
        self.client.post(self.entry_url(), self.post_data(**{
            f'att-{self.q1.pk}-absences': 'three',
        }))
        att = AttendanceRecord.objects.get(report_card=self.card, grading_period=self.q1)
        self.assertEqual(att.absences, 0)

    def test_blank_cells_left_empty(self):
        self.client.post(self.entry_url(), self.post_data())
        grade = Grade.objects.get(card_subject=self.el, grading_period=self.q0)
        self.assertEqual(grade.assessment, '')

    def test_subtitle_saved_per_card_without_touching_subject(self):
        math = self.card_subject(self.card, 'Math')
        self.client.post(self.entry_url(), self.post_data(**{
            f'subtitle-{math.pk}': 'Algebra I',
        }))
        math.refresh_from_db()
        self.assertEqual(math.subtitle, 'Algebra I')
        self.math.refresh_from_db()
        self.assertEqual(self.math.subtitle, 'Pre-Algebra')

    def test_subtitle_unchanged_when_not_posted(self):
        math = self.card_subject(self.card, 'Math')
        self.client.post(self.entry_url(), self.post_data())
        math.refresh_from_db()
        self.assertEqual(math.subtitle, 'Pre-Algebra')

    def test_grades_saved_for_snapshot_even_after_subject_deleted(self):
        self.language_arts.delete()
        self.client.post(self.entry_url(), self.post_data())
        grade = Grade.objects.get(card_subject=self.la, grading_period=self.q1)
        self.assertEqual(grade.assessment, 'INC')
