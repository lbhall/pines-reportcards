from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GradingPeriodFormSet, SchoolYearForm, StudentForm, SubjectForm
from .models import SchoolYear, Student, Subject


@login_required
def home(request):
    students = Student.objects.all()
    return render(request, 'reportcards/home.html', {'students': students})


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


@login_required
def year_delete(request, pk):
    year = get_object_or_404(SchoolYear, pk=pk)
    if request.method == 'POST':
        year.delete()
        return redirect('year_list')
    return render(request, 'reportcards/confirm_delete.html',
                  {'object': year, 'cancel_url': 'year_list'})
