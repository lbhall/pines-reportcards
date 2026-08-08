"""Tests for management commands."""
from django.core.management import call_command
from django.test import TestCase

from .models import SchoolYear, Subject


class SeedDefaultsTests(TestCase):
    def test_creates_default_subjects_and_year(self):
        call_command('seed_defaults')
        self.assertEqual(Subject.objects.core().count(), 5)
        self.assertEqual(Subject.objects.resources().count(), 5)
        self.assertTrue(Subject.objects.filter(name='Independent Study-Research').exists())
        self.assertTrue(Subject.objects.filter(name='Internship week').exists())

        year = SchoolYear.objects.get(label='2025-26')
        self.assertEqual(year.periods.count(), 5)
        q0 = year.periods.get(order=0)
        self.assertEqual(q0.name, 'Orientation')
        self.assertEqual(q0.date_range_display, '8/11/25-8/30/25')

    def test_idempotent(self):
        call_command('seed_defaults')
        call_command('seed_defaults')
        self.assertEqual(Subject.objects.count(), 10)
        self.assertEqual(SchoolYear.objects.count(), 1)
        self.assertEqual(SchoolYear.objects.get().periods.count(), 5)
