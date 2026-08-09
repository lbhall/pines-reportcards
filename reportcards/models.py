from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolYear(models.Model):
    label = models.CharField(max_length=20, unique=True)
    faculty_1 = models.CharField(
        max_length=200, blank=True, default='',
        help_text='First signature line, e.g. "Catherine Hall, Middle School Faculty"')
    faculty_2 = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Second signature line')

    class Meta:
        ordering = ['-label']

    def __str__(self):
        return self.label


class GradingPeriod(models.Model):
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['school_year', 'name'], name='unique_period_name_per_year'),
        ]

    def __str__(self):
        return f'{self.name} ({self.school_year})'

    @property
    def date_range_display(self):
        if not (self.start_date and self.end_date):
            return ''
        def short(d):
            return f'{d.month}/{d.day}/{d.strftime("%y")}'
        return f'{short(self.start_date)}-{short(self.end_date)}'


class SubjectQuerySet(models.QuerySet):
    def core(self):
        return self.filter(category=Subject.Category.CORE, active=True)

    def resources(self):
        return self.filter(category=Subject.Category.RESOURCE, active=True)


class Subject(models.Model):
    class Category(models.TextChoices):
        CORE = 'core', 'Core Subject'
        RESOURCE = 'resource', 'Resource'

    name = models.CharField(max_length=200)
    subtitle = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Optional, shown after the name — e.g. "Pre-Algebra" for "Math: Pre-Algebra". '
                  'Can be adjusted per report card on the entry screen.')
    category = models.CharField(max_length=10, choices=Category.choices)
    order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    objects = SubjectQuerySet.as_manager()

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return f'{self.name}: {self.subtitle}' if self.subtitle else self.name


class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='report_cards')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='report_cards')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'school_year'], name='unique_card_per_student_year'),
        ]

    def __str__(self):
        return f'{self.student} — {self.school_year}'

    def snapshot_subjects(self):
        """Copy the currently active subjects onto this card, once.

        Grades attach to the copies, so later edits to the Subject list only
        affect report cards created afterwards.
        """
        if self.card_subjects.exists():
            return
        for subject in Subject.objects.filter(active=True):
            CardSubject.objects.create(
                report_card=self, source_subject=subject,
                name=subject.name, subtitle=subject.subtitle,
                category=subject.category, order=subject.order)


class CardSubject(models.Model):
    """A subject as it existed when a report card was created."""

    Category = Subject.Category

    report_card = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name='card_subjects')
    source_subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='card_subjects')
    name = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=10, choices=Subject.Category.choices)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.display_name} ({self.report_card})'

    @property
    def display_name(self):
        return f'{self.name}: {self.subtitle}' if self.subtitle else self.name


class Grade(models.Model):
    class Designation(models.TextChoices):
        LEVEL = 'L', 'Level'
        ADVANCED = 'A', 'Advanced'
        LEVEL_MODIFIED = 'L/M', 'Level/Modified'
        MODIFIED = 'M', 'Modified'

    class WorkHabits(models.TextChoices):
        MASTERED = 'M', 'Mastered'
        COMPETENT = 'C', 'Competent'
        IMPROVING = 'I', 'Improving'
        REMINDERS = 'R', 'Reminders Needed'

    report_card = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name='grades')
    card_subject = models.ForeignKey(CardSubject, on_delete=models.CASCADE, related_name='grades')
    grading_period = models.ForeignKey(GradingPeriod, on_delete=models.CASCADE, related_name='grades')
    assessment = models.CharField(
        max_length=20, blank=True, default='',
        help_text='Free-form grade, e.g. "83%", "P", "INC", "N/A"')
    designation = models.CharField(max_length=3, choices=Designation.choices, blank=True, default='')
    work_habits = models.CharField(max_length=1, choices=WorkHabits.choices, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['card_subject', 'grading_period'],
                name='unique_grade_per_cell'),
        ]

    def __str__(self):
        return f'{self.report_card} / {self.card_subject.name} / {self.grading_period.name}'


class AttendanceRecord(models.Model):
    report_card = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name='attendance')
    grading_period = models.ForeignKey(GradingPeriod, on_delete=models.CASCADE, related_name='attendance')
    absences = models.PositiveSmallIntegerField(default=0)
    tardies = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['report_card', 'grading_period'],
                name='unique_attendance_per_period'),
        ]

    def __str__(self):
        return f'{self.report_card} / {self.grading_period.name}'
