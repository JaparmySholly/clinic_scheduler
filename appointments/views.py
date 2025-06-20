# appointments/views.py

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .forms import StudentSignUpForm, BookAppointmentForm
from .models import Appointment, AuditLog, MedicalTestSchedule
from .decorators import role_required


def home(request):
    if request.user.is_authenticated:
        return redirect('appointments:dashboard')
    return redirect('appointments:dashboard')


def register(request):
    if request.user.is_authenticated:
        return redirect('appointments:dashboard')

    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('appointments:dashboard')
    else:
        form = StudentSignUpForm()

    return render(request, 'appointments/register.html', {'form': form})


@login_required
def dashboard(request):
    role = request.user.profile.role
    if role == 'student':
        return redirect('appointments:my_appointments')
    elif role == 'staff':
        return redirect('appointments:staff_requests')
    return redirect('appointments:home')


@login_required
@role_required('student')
def my_appointments(request):
    # 1) their regular clinic appointments
    appointments = Appointment.objects.filter(
        student=request.user
    ).order_by('-date_time')

    # 2) their assigned medical-test slots via the Profile FK
    medical_tests = MedicalTestSchedule.objects.filter(
        student=request.user.profile
    ).order_by('scheduled_date', 'scheduled_time')

    return render(request, 'appointments/dashboard_student.html', {
        'appointments':  appointments,
        'medical_tests': medical_tests,
    })


@login_required
@role_required('student')
def book_appointment(request):
    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.student = request.user
            appt.status = 'pending'
            appt.save()
            AuditLog.objects.create(
                user=request.user,
                action=f"Booked appointment {appt.id}",
                details={
                    'staff': appt.staff.username,
                    'date_time': str(appt.date_time)
                }
            )
            messages.success(request,
                "Appointment request submitted. Please wait for staff approval."
            )
            return redirect('appointments:my_appointments')
    else:
        form = BookAppointmentForm()

    return render(request, 'appointments/book_appointment.html', {'form': form})


@login_required
@role_required('student')
def cancel_appointment(request, appointment_id):
    appt = get_object_or_404(Appointment,
                             id=appointment_id,
                             student=request.user)
    time_diff = appt.date_time - timezone.now()
    if time_diff.total_seconds() < 4 * 3600:
        messages.error(request,
            "Cannot cancel within 4 hours of the appointment time."
        )
    else:
        appt.status = 'cancelled'
        appt.save()
        AuditLog.objects.create(
            user=request.user,
            action=f"Cancelled appointment {appt.id}",
            details={'date_time': str(appt.date_time)}
        )
        messages.success(request, "Appointment successfully cancelled.")
    return redirect('appointments:my_appointments')


@login_required
@role_required('staff')
def staff_requests(request):
    # 1) pending clinic appointments
    pending = Appointment.objects.filter(
        staff=request.user,
        status='pending'
    ).order_by('date_time')

    # 2) confirmed upcoming appointments
    confirmed = Appointment.objects.filter(
        staff=request.user,
        status='confirmed',
        date_time__gte=timezone.now()
    ).order_by('date_time')

    # 3) this staff’s medical-test slots
    test_slots = MedicalTestSchedule.objects.filter(
        staff=request.user
    ).order_by('scheduled_date', 'scheduled_time')

    return render(request, 'appointments/dashboard_staff.html', {
        'pending_appointments':   pending,
        'confirmed_appointments': confirmed,
        'test_slots':             test_slots,
    })


@login_required
@role_required('staff')
def confirm_appointment(request, appointment_id):
    appt = get_object_or_404(Appointment,
                             id=appointment_id,
                             staff=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            appt.status = 'confirmed'
            appt.save()
            AuditLog.objects.create(
                user=request.user,
                action=f"Confirmed appointment {appt.id}",
                details={
                    'student': appt.student.username,
                    'date_time': str(appt.date_time)
                }
            )
            messages.success(request, "Appointment confirmed.")
        elif action == 'reject':
            appt.status = 'rejected'
            appt.save()
            AuditLog.objects.create(
                user=request.user,
                action=f"Rejected appointment {appt.id}",
                details={
                    'student': appt.student.username,
                    'date_time': str(appt.date_time)
                }
            )
            messages.success(request, "Appointment rejected.")
        return redirect('appointments:staff_requests')

    return render(request, 'appointments/confirm_appointment.html', {
        'appointment': appt
    })


# ----------------------------------------------------------------
# Dedicated “My Medical Schedule” page
@login_required
@role_required('student')
def my_medical_schedule(request):
    """
    Show the logged-in student their assigned medical test slots.
    """
    medical_tests = MedicalTestSchedule.objects.filter(
        student=request.user.profile
    ).order_by('scheduled_date', 'scheduled_time')

    return render(request, 'appointments/my_medical_schedule.html', {
        'medical_tests': medical_tests,
    })
