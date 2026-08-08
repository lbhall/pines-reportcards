from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('years/', views.year_list, name='year_list'),
    path('years/add/', views.year_add, name='year_add'),
    path('years/<int:pk>/edit/', views.year_edit, name='year_edit'),
    path('years/<int:pk>/delete/', views.year_delete, name='year_delete'),
]
