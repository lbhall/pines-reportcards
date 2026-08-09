"""Seed the default subjects and the 2025-26 school year. Idempotent."""
import datetime

from django.core.management.base import BaseCommand

from reportcards.models import GradingPeriod, SchoolYear, Subject

CORE_SUBJECTS = [
    # (name, subtitle)
    ('Language Arts', ''),
    ('Math', 'Pre-Algebra'),
    ('Physical Science', ''),
    ('Humanities', ''),
    ('Spanish', ''),
    ('Independent Study-Research', ''),
]

RESOURCE_SUBJECTS = [
    ('Electives', ''),
    ('Health & Fitness', ''),
    ('Guided Reflection', ''),
    ('Internship week', ''),
]

PERIODS = [
    # (name, order, start, end)
    ('Orientation', 0, datetime.date(2025, 8, 11), datetime.date(2025, 8, 30)),
    ('Quarter 1', 1, datetime.date(2025, 9, 2), None),
    ('Quarter 2', 2, None, None),
    ('Quarter 3', 3, None, None),
    ('Quarter 4', 4, None, None),
]


class Command(BaseCommand):
    help = 'Create the default subjects and the 2025-26 school year with its grading periods.'

    def handle(self, *args, **options):
        for order, (name, subtitle) in enumerate(CORE_SUBJECTS, start=1):
            Subject.objects.get_or_create(
                name=name, category=Subject.Category.CORE,
                defaults={'order': order, 'subtitle': subtitle})
        for order, (name, subtitle) in enumerate(RESOURCE_SUBJECTS, start=1):
            Subject.objects.get_or_create(
                name=name, category=Subject.Category.RESOURCE,
                defaults={'order': order, 'subtitle': subtitle})

        year, _ = SchoolYear.objects.get_or_create(
            label='2025-26',
            defaults={
                'faculty_1': 'Catherine Hall, Middle School Faculty',
                'faculty_2': 'Valerie de Grood, Middle School Faculty',
            })
        for name, order, start, end in PERIODS:
            GradingPeriod.objects.get_or_create(
                school_year=year, name=name,
                defaults={'order': order, 'start_date': start, 'end_date': end})

        self.stdout.write(self.style.SUCCESS('Defaults seeded.'))
