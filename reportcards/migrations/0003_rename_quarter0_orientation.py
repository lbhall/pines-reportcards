"""Rename existing 'Quarter 0' grading periods to 'Orientation'."""
from django.db import migrations


def rename_quarter0(apps, schema_editor):
    GradingPeriod = apps.get_model('reportcards', 'GradingPeriod')
    GradingPeriod.objects.filter(name='Quarter 0').update(name='Orientation')


def rename_back(apps, schema_editor):
    GradingPeriod = apps.get_model('reportcards', 'GradingPeriod')
    GradingPeriod.objects.filter(name='Orientation').update(name='Quarter 0')


class Migration(migrations.Migration):

    dependencies = [
        ('reportcards', '0002_cardsubject_snapshot'),
    ]

    operations = [
        migrations.RunPython(rename_quarter0, rename_back),
    ]
