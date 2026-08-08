"""Snapshot subjects onto report cards so editing subjects never rewrites history.

Creates CardSubject (a per-card copy of each subject), repoints Grade at it,
and migrates existing data: every card gets copies of the subjects its grades
reference plus all currently active subjects.
"""
import django.db.models.deletion
from django.db import migrations, models


def snapshot_existing_cards(apps, schema_editor):
    ReportCard = apps.get_model('reportcards', 'ReportCard')
    CardSubject = apps.get_model('reportcards', 'CardSubject')
    Subject = apps.get_model('reportcards', 'Subject')
    Grade = apps.get_model('reportcards', 'Grade')

    for card in ReportCard.objects.all():
        subject_ids = set(
            Grade.objects.filter(report_card=card).values_list('subject_id', flat=True))
        subject_ids.update(
            Subject.objects.filter(active=True).values_list('id', flat=True))
        mapping = {}
        for subject in Subject.objects.filter(id__in=subject_ids):
            mapping[subject.id] = CardSubject.objects.create(
                report_card=card, source_subject=subject,
                name=subject.name, category=subject.category, order=subject.order)
        for grade in Grade.objects.filter(report_card=card):
            grade.card_subject = mapping[grade.subject_id]
            grade.save(update_fields=['card_subject'])


class Migration(migrations.Migration):

    dependencies = [
        ('reportcards', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(choices=[('core', 'Core Subject'), ('resource', 'Resource')], max_length=10)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('report_card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_subjects', to='reportcards.reportcard')),
                ('source_subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='card_subjects', to='reportcards.subject')),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
        migrations.RemoveConstraint(
            model_name='grade',
            name='unique_grade_per_cell',
        ),
        migrations.AddField(
            model_name='grade',
            name='card_subject',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='reportcards.cardsubject'),
        ),
        migrations.RunPython(snapshot_existing_cards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='grade',
            name='card_subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='reportcards.cardsubject'),
        ),
        migrations.RemoveField(
            model_name='grade',
            name='subject',
        ),
        migrations.AddConstraint(
            model_name='grade',
            constraint=models.UniqueConstraint(fields=('card_subject', 'grading_period'), name='unique_grade_per_cell'),
        ),
    ]
