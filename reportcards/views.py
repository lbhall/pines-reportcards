from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GradingPeriodFormSet, SchoolYearForm, StudentForm, SubjectForm
from .models import AttendanceRecord, Grade, ReportCard, SchoolYear, Student, Subject


@login_required
def home(request):
    students = Student.objects.all()
    current_year = SchoolYear.objects.first()
    return render(request, 'reportcards/home.html',
                  {'students': students, 'current_year': current_year})


@login_required
def student_add(request):
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('home')
    return render(request, 'reportcards/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('home')
    return render(request, 'reportcards/student_form.html',
                  {'form': form, 'title': f'Edit {student.name}'})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        return redirect('home')
    return render(request, 'reportcards/confirm_delete.html',
                  {'object': student, 'cancel_url': 'home'})


@login_required
def subject_list(request):
    groups = [
        ('Core Subjects', Subject.objects.filter(category=Subject.Category.CORE)),
        ('Resources', Subject.objects.filter(category=Subject.Category.RESOURCE)),
    ]
    return render(request, 'reportcards/subject_list.html', {'groups': groups})


@login_required
def subject_add(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('subject_list')
    return render(request, 'reportcards/subject_form.html', {'form': form, 'title': 'Add Subject'})


@login_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('subject_list')
    return render(request, 'reportcards/subject_form.html',
                  {'form': form, 'title': f'Edit {subject.name}'})


@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'reportcards/confirm_delete.html',
                  {'object': subject, 'cancel_url': 'subject_list'})


@login_required
def year_list(request):
    return render(request, 'reportcards/year_list.html', {'years': SchoolYear.objects.all()})


@login_required
def year_add(request):
    form = SchoolYearForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        year = form.save()
        return redirect('year_edit', pk=year.pk)
    return render(request, 'reportcards/year_form.html',
                  {'form': form, 'title': 'Add School Year'})


@login_required
def year_edit(request, pk):
    year = get_object_or_404(SchoolYear, pk=pk)
    form = SchoolYearForm(request.POST or None, instance=year)
    formset = GradingPeriodFormSet(request.POST or None, instance=year, prefix='periods')
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        return redirect('year_list')
    return render(request, 'reportcards/year_form.html',
                  {'form': form, 'formset': formset, 'title': f'Edit {year.label}'})


def _valid_choice(value, choices):
    return value if value in choices.values else ''


def _to_int(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _card_context(card):
    periods = list(card.school_year.periods.all())
    subjects = list(card.card_subjects.all())
    grades = {(g.card_subject_id, g.grading_period_id): g for g in card.grades.all()}
    attendance = {a.grading_period_id: a for a in card.attendance.all()}

    def cell(subject, period):
        grade = grades.get((subject.pk, period.pk))
        return {
            'period_pk': period.pk,
            'assessment': grade.assessment if grade else '',
            'designation': grade.designation if grade else '',
            'work_habits': grade.work_habits if grade else '',
        }

    def rows(category):
        return [{'subject': s, 'cells': [cell(s, p) for p in periods]}
                for s in subjects if s.category == category]

    def att_cell(period):
        record = attendance.get(period.pk)
        return {
            'period_pk': period.pk,
            'absences': record.absences if record else 0,
            'tardies': record.tardies if record else 0,
        }

    return {
        'card': card,
        'student': card.student,
        'year': card.school_year,
        'periods': periods,
        'grouped_rows': [
            ('Core Subjects', rows(Subject.Category.CORE)),
            ('Resources', rows(Subject.Category.RESOURCE)),
        ],
        'attendance_cells': [att_cell(p) for p in periods],
    }


@login_required
def card_entry(request, student_pk, year_pk):
    student = get_object_or_404(Student, pk=student_pk)
    year = get_object_or_404(SchoolYear, pk=year_pk)
    card, _ = ReportCard.objects.get_or_create(student=student, school_year=year)
    card.snapshot_subjects()
    periods = list(year.periods.all())
    subjects = list(card.card_subjects.all())

    if request.method == 'POST':
        for subject in subjects:
            subtitle = request.POST.get(f'subtitle-{subject.pk}')
            if subtitle is not None and subtitle.strip() != subject.subtitle:
                subject.subtitle = subtitle.strip()
                subject.save(update_fields=['subtitle'])
            for period in periods:
                prefix = f'grade-{subject.pk}-{period.pk}'
                Grade.objects.update_or_create(
                    report_card=card, card_subject=subject, grading_period=period,
                    defaults={
                        'assessment': request.POST.get(f'{prefix}-assessment', '').strip(),
                        'designation': _valid_choice(
                            request.POST.get(f'{prefix}-designation', ''), Grade.Designation),
                        'work_habits': _valid_choice(
                            request.POST.get(f'{prefix}-work_habits', ''), Grade.WorkHabits),
                    })
        for period in periods:
            AttendanceRecord.objects.update_or_create(
                report_card=card, grading_period=period,
                defaults={
                    'absences': _to_int(request.POST.get(f'att-{period.pk}-absences')),
                    'tardies': _to_int(request.POST.get(f'att-{period.pk}-tardies')),
                })
        messages.success(request, 'Report card saved.')
        return redirect('card_entry', student_pk=student.pk, year_pk=year.pk)

    context = _card_context(card)
    context['designation_choices'] = Grade.Designation.choices
    context['work_habits_choices'] = Grade.WorkHabits.choices
    return render(request, 'reportcards/card_entry.html', context)


@login_required
def card_print(request, pk):
    card = get_object_or_404(
        ReportCard.objects.select_related('student', 'school_year'), pk=pk)
    return render(request, 'reportcards/card_print.html', _card_context(card))


@login_required
def year_delete(request, pk):
    year = get_object_or_404(SchoolYear, pk=pk)
    if request.method == 'POST':
        year.delete()
        return redirect('year_list')
    return render(request, 'reportcards/confirm_delete.html',
                  {'object': year, 'cancel_url': 'year_list'})
