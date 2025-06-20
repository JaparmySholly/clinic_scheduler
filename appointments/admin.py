# appointments/admin.py

from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
import csv, io, chardet

from .models import Profile, Appointment, AuditLog, MedicalTestSchedule


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role', 'matric_no', 'department', 'phone_number')
    list_filter   = ('role', 'department')
    search_fields = ('user__username', 'matric_no')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('student', 'staff', 'date_time', 'status')
    list_filter   = ('status', 'staff')
    search_fields = ('student__username', 'staff__username')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'action', 'timestamp')
    search_fields = ('user__username', 'action')


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        help_text="Upload a CSV file with columns: full name, matric_no, department"
    )


@admin.register(MedicalTestSchedule)
class MedicalTestScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'student_matric_no',
        'student_department',
        'scheduled_date',
        'scheduled_time',
        'staff',
        'ward_number',
    )
    list_filter = (
        'staff',
        'student__department',
    )
    search_fields = (
        'student__matric_no',
        'student__user__username',
    )

    change_list_template = "admin/appointments/medicaltestschedule_changelist.html"

    def student_matric_no(self, obj):
        if obj.student is None:
            return "—"
        return obj.student.matric_no or "—"
    student_matric_no.short_description = "Matric No"
    student_matric_no.admin_order_field = "student__matric_no"

    def student_department(self, obj):
        if obj.student is None:
            return "—"
        return obj.student.department or "—"
    student_department.short_description = "Department"
    student_department.admin_order_field = "student__department"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload-csv/',
                self.admin_site.admin_view(self.upload_csv),
                name='appointments_medicaltestschedule_upload_csv'
            ),
        ]
        return custom + urls

    def upload_csv(self, request):
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                raw = form.cleaned_data['csv_file'].read()
                detected = chardet.detect(raw)
                enc = detected.get('encoding') or 'utf-8'
                text = raw.decode(enc, errors='replace')
                sio = io.StringIO(text, newline='')
                try:
                    reader = csv.DictReader(sio)
                    schedules = list(reader)
                except csv.Error as e:
                    self.message_user(request, f"CSV error: {e}", level=messages.ERROR)
                    return redirect(request.path)

                from .utils import allocate_medical_tests
                allocate_medical_tests(schedules)

                self.message_user(request, "Medical tests scheduled.", level=messages.SUCCESS)
                return redirect('admin:appointments_medicaltestschedule_changelist')
        else:
            form = CSVUploadForm()

        ctx = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'form': form,
        }
        return render(request, 'admin/appointments/upload_csv.html', ctx)
