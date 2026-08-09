"""Model tests for the reportcards app."""
import datetime

from django.db import IntegrityError
from django.test import TestCase

from .models import (
    AttendanceRecord,
    CardSubject,
    Grade,
    GradingPeriod,
    ReportCard,
    SchoolYear,
    Student,
    Subject,
)


def make_student(name='Gabriel Miller', dob=datetime.date(2013, 2, 7)):
    return Student.objects.create(name=name, date_of_birth=dob)


def make_school_year(label='2025-26'):
    return SchoolYear.objects.create(label=label)


def make_period(school_year, name='Quarter 1', order=1,
                start=datetime.date(2025, 9, 2), end=datetime.date(2025, 11, 7)):
    return GradingPeriod.objects.create(
        school_year=school_year, name=name, order=order,
        start_date=start, end_date=end,
    )


def make_subject(name='Language Arts', category=Subject.Category.CORE, order=1, subtitle=''):
    return Subject.objects.create(name=name, category=category, order=order, subtitle=subtitle)


def make_report_card(student=None, school_year=None):
    student = student or make_student()
    school_year = school_year or make_school_year()
    card = ReportCard.objects.create(student=student, school_year=school_year)
    card.snapshot_subjects()
    return card


class StudentModelTests(TestCase):
    def test_str_returns_name(self):
        student = make_student(name='Gabriel Miller')
        self.assertEqual(str(student), 'Gabriel Miller')

    def test_dob_display(self):
        student = make_student(dob=datetime.date(2013, 2, 7))
        self.assertEqual(student.date_of_birth.strftime('%B %-d, %Y'), 'February 7, 2013')


class SchoolYearModelTests(TestCase):
    def test_str_returns_label(self):
        year = make_school_year(label='2025-26')
        self.assertEqual(str(year), '2025-26')

    def test_label_unique(self):
        make_school_year(label='2025-26')
        with self.assertRaises(IntegrityError):
            make_school_year(label='2025-26')

    def test_faculty_fields_default_blank(self):
        year = make_school_year()
        self.assertEqual(year.faculty_1, '')
        self.assertEqual(year.faculty_2, '')


class GradingPeriodModelTests(TestCase):
    def setUp(self):
        self.year = make_school_year()

    def test_str_includes_name_and_year(self):
        period = make_period(self.year, name='Quarter 1')
        self.assertEqual(str(period), 'Quarter 1 (2025-26)')

    def test_date_range_display(self):
        period = make_period(self.year,
                             start=datetime.date(2025, 9, 2),
                             end=datetime.date(2025, 9, 12))
        self.assertEqual(period.date_range_display, '9/2/25-9/12/25')

    def test_date_range_display_empty_without_dates(self):
        period = make_period(self.year, name='Quarter 3', order=3, start=None, end=None)
        self.assertEqual(period.date_range_display, '')

    def test_unique_name_per_year(self):
        make_period(self.year, name='Quarter 1')
        with self.assertRaises(IntegrityError):
            make_period(self.year, name='Quarter 1', order=2)

    def test_ordered_by_order(self):
        p2 = make_period(self.year, name='Quarter 2', order=2)
        p0 = make_period(self.year, name='Quarter 0', order=0)
        self.assertEqual(list(self.year.periods.all()), [p0, p2])


class SubjectModelTests(TestCase):
    def test_str_returns_name(self):
        subject = make_subject(name='Math: Pre-Algebra')
        self.assertEqual(str(subject), 'Math: Pre-Algebra')

    def test_category_helpers(self):
        core = make_subject(name='Humanities', category=Subject.Category.CORE)
        resource = make_subject(name='Electives', category=Subject.Category.RESOURCE, order=2)
        self.assertIn(core, Subject.objects.core())
        self.assertNotIn(resource, Subject.objects.core())
        self.assertIn(resource, Subject.objects.resources())

    def test_inactive_excluded_from_helpers(self):
        subject = make_subject()
        subject.active = False
        subject.save()
        self.assertNotIn(subject, Subject.objects.core())

    def test_ordered_by_order_then_name(self):
        b = make_subject(name='B Subject', order=2)
        a = make_subject(name='A Subject', order=1)
        self.assertEqual(list(Subject.objects.core()), [a, b])

    def test_display_name_with_subtitle(self):
        math = make_subject(name='Math', subtitle='Pre-Algebra')
        plain = make_subject(name='Humanities', order=2)
        self.assertEqual(math.display_name, 'Math: Pre-Algebra')
        self.assertEqual(plain.display_name, 'Humanities')


class ReportCardModelTests(TestCase):
    def test_str(self):
        card = make_report_card()
        self.assertEqual(str(card), 'Gabriel Miller — 2025-26')

    def test_unique_per_student_and_year(self):
        card = make_report_card()
        with self.assertRaises(IntegrityError):
            ReportCard.objects.create(student=card.student, school_year=card.school_year)

    def test_snapshot_copies_active_subjects(self):
        make_subject(name='Language Arts', category=Subject.Category.CORE)
        make_subject(name='Electives', category=Subject.Category.RESOURCE, order=2)
        inactive = make_subject(name='Old Subject', order=9)
        inactive.active = False
        inactive.save()
        card = make_report_card()
        names = list(card.card_subjects.values_list('name', flat=True))
        self.assertIn('Language Arts', names)
        self.assertIn('Electives', names)
        self.assertNotIn('Old Subject', names)

    def test_snapshot_is_idempotent(self):
        make_subject(name='Language Arts')
        card = make_report_card()
        card.snapshot_subjects()
        self.assertEqual(card.card_subjects.count(), 1)

    def test_renaming_subject_does_not_change_existing_card(self):
        subject = make_subject(name='Math: Pre-Algebra')
        card = make_report_card()
        subject.name = 'Math: Algebra I'
        subject.save()
        self.assertEqual(card.card_subjects.get().name, 'Math: Pre-Algebra')

    def test_deleting_subject_keeps_card_history(self):
        subject = make_subject(name='Humanities')
        card = make_report_card()
        subject.delete()
        self.assertEqual(card.card_subjects.get().name, 'Humanities')

    def test_new_card_sees_edited_subjects(self):
        subject = make_subject(name='Math: Pre-Algebra')
        old_card = make_report_card()
        subject.name = 'Math: Algebra I'
        subject.save()
        new_card = make_report_card(
            student=make_student(name='Ada Lovelace'),
            school_year=old_card.school_year)
        self.assertEqual(new_card.card_subjects.get().name, 'Math: Algebra I')


class GradeModelTests(TestCase):
    def setUp(self):
        make_subject(name='Language Arts')
        self.card = make_report_card()
        self.period = make_period(self.card.school_year)
        self.card_subject = self.card.card_subjects.get()

    def test_create_grade_with_choices(self):
        grade = Grade.objects.create(
            report_card=self.card, card_subject=self.card_subject, grading_period=self.period,
            assessment='83%', designation=Grade.Designation.LEVEL,
            work_habits=Grade.WorkHabits.REMINDERS,
        )
        self.assertEqual(grade.designation, 'L')
        self.assertEqual(grade.work_habits, 'R')
        self.assertEqual(grade.get_work_habits_display(), 'Reminders Needed')

    def test_blank_values_allowed(self):
        grade = Grade.objects.create(
            report_card=self.card, card_subject=self.card_subject, grading_period=self.period,
        )
        self.assertEqual(grade.assessment, '')
        self.assertEqual(grade.designation, '')
        self.assertEqual(grade.work_habits, '')

    def test_work_habits_choices(self):
        labels = dict(Grade.WorkHabits.choices)
        self.assertEqual(labels, {
            'M': 'Mastered', 'C': 'Competent', 'I': 'Improving', 'R': 'Reminders Needed',
        })

    def test_designation_choices(self):
        labels = dict(Grade.Designation.choices)
        self.assertEqual(labels, {
            'L': 'Level', 'A': 'Advanced', 'L/M': 'Level/Modified', 'M': 'Modified',
        })

    def test_unique_per_cell(self):
        Grade.objects.create(
            report_card=self.card, card_subject=self.card_subject, grading_period=self.period,
        )
        with self.assertRaises(IntegrityError):
            Grade.objects.create(
                report_card=self.card, card_subject=self.card_subject, grading_period=self.period,
            )

    def test_card_subject_snapshot_fields(self):
        self.assertEqual(self.card_subject.name, 'Language Arts')
        self.assertEqual(self.card_subject.category, CardSubject.Category.CORE)
        self.assertIsNotNone(self.card_subject.source_subject)

    def test_snapshot_copies_subtitle_and_display_name(self):
        make_subject(name='Math', subtitle='Pre-Algebra', order=2)
        card = make_report_card(
            student=make_student(name='Ada Lovelace'),
            school_year=make_school_year(label='2026-27'))
        math = card.card_subjects.get(name='Math')
        self.assertEqual(math.subtitle, 'Pre-Algebra')
        self.assertEqual(math.display_name, 'Math: Pre-Algebra')

    def test_card_subtitle_editable_without_touching_source(self):
        make_subject(name='Math', subtitle='Pre-Algebra', order=2)
        card = make_report_card(
            student=make_student(name='Ada Lovelace'),
            school_year=make_school_year(label='2026-27'))
        math = card.card_subjects.get(name='Math')
        math.subtitle = 'Algebra I'
        math.save()
        self.assertEqual(math.display_name, 'Math: Algebra I')
        self.assertEqual(Subject.objects.get(name='Math').subtitle, 'Pre-Algebra')


class AttendanceRecordModelTests(TestCase):
    def setUp(self):
        self.card = make_report_card()
        self.period = make_period(self.card.school_year)

    def test_defaults_to_zero(self):
        record = AttendanceRecord.objects.create(
            report_card=self.card, grading_period=self.period,
        )
        self.assertEqual(record.absences, 0)
        self.assertEqual(record.tardies, 0)

    def test_unique_per_period(self):
        AttendanceRecord.objects.create(report_card=self.card, grading_period=self.period)
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(report_card=self.card, grading_period=self.period)
