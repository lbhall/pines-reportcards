"""Add editable subtitles to subjects and card snapshots.

Existing names containing ': ' (e.g. 'Math: Pre-Algebra') are split into
name='Math', subtitle='Pre-Algebra' on both Subject and CardSubject.
"""
from django.db import migrations, models


def split_subtitles(apps, schema_editor):
    for model_name in ('Subject', 'CardSubject'):
        model = apps.get_model('reportcards', model_name)
        for obj in model.objects.filter(name__contains=': '):
            obj.name, obj.subtitle = obj.name.split(': ', 1)
            obj.save(update_fields=['name', 'subtitle'])


def join_subtitles(apps, schema_editor):
    for model_name in ('Subject', 'CardSubject'):
        model = apps.get_model('reportcards', model_name)
        for obj in model.objects.exclude(subtitle=''):
            obj.name = f'{obj.name}: {obj.subtitle}'
            obj.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('reportcards', '0004_foreign_language_to_spanish'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='subtitle',
            field=models.CharField(
                blank=True, default='', max_length=200,
                help_text='Optional, shown after the name — e.g. "Pre-Algebra" for "Math: Pre-Algebra". '
                          'Can be adjusted per report card on the entry screen.'),
        ),
        migrations.AddField(
            model_name='cardsubject',
            name='subtitle',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.RunPython(split_subtitles, join_subtitles),
    ]
