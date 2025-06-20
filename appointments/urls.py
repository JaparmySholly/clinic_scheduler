from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('staff/requests/', views.staff_requests, name='staff_requests'),
    path('staff/confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('medical-schedule/', views.my_medical_schedule, name='my_medical_schedule'),
]
