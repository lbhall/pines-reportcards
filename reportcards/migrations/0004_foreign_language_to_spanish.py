"""Move Foreign Language from Resources to Core Subjects and rename it Spanish.

Existing report cards keep their snapshot ('Foreign Language' under
Resources); only report cards created after this change see Spanish.
"""
from django.db import migrations


def foreign_language_to_spanish(apps, schema_editor):
    Subject = apps.get_model('reportcards', 'Subject')
    # Slot Spanish before Independent Study-Research in the core ordering.
    Subject.objects.filter(name='Independent Study-Research', category='core').update(order=6)
    Subject.objects.filter(name='Foreign Language').update(
        name='Spanish', category='core', order=5)


def spanish_to_foreign_language(apps, schema_editor):
    Subject = apps.get_model('reportcards', 'Subject')
    Subject.objects.filter(name='Spanish').update(
        name='Foreign Language', category='resource', order=1)
    Subject.objects.filter(name='Independent Study-Research', category='core').update(order=5)


class Migration(migrations.Migration):

    dependencies = [
        ('reportcards', '0003_rename_quarter0_orientation'),
    ]

    operations = [
        migrations.RunPython(foreign_language_to_spanish, spanish_to_foreign_language),
    ]
