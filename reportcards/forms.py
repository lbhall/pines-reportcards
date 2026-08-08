from django import forms
from django.forms import inlineformset_factory

from .models import GradingPeriod, SchoolYear, Student, Subject


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'date_of_birth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'category', 'order', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ['label', 'faculty_1', 'faculty_2']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-26'}),
            'faculty_1': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty_2': forms.TextInput(attrs={'class': 'form-control'}),
        }


GradingPeriodFormSet = inlineformset_factory(
    SchoolYear, GradingPeriod,
    fields=['name', 'order', 'start_date', 'end_date'],
    widgets={
        'name': forms.TextInput(attrs={'class': 'form-control'}),
        'order': forms.NumberInput(attrs={'class': 'form-control'}),
        'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    },
    extra=1, can_delete=True,
)
