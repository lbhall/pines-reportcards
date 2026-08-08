from django.contrib import admin

from .models import (
    AttendanceRecord,
    Grade,
    GradingPeriod,
    ReportCard,
    SchoolYear,
    Student,
    Subject,
)


class GradingPeriodInline(admin.TabularInline):
    model = GradingPeriod
    extra = 0


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ['label', 'faculty_1', 'faculty_2']
    inlines = [GradingPeriodInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_of_birth']
    search_fields = ['name']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'active']
    list_filter = ['category', 'active']


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0


class AttendanceInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['student', 'school_year']
    list_filter = ['school_year']
    inlines = [GradeInline, AttendanceInline]
