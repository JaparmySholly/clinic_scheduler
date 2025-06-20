# appointments/models.py

from django.conf import settings
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('staff',   'Staff'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student'
    )

    #–– store each student’s matric_no and department on their Profile
    matric_no = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="For students: their matriculation number"
    )
    DEPARTMENT_CHOICES = [
        ('CPT', 'Computer Science'),
        ('PHY', 'Physics'),
        ('CSS', 'Cyber Security Science'),
        ('IMT', 'Information and Media Technology'),
        # …etc
    ]
    department = models.CharField(
        max_length=30,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Student’s department"
    )

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended',  'Attended'),
        ('no_show',   'No-Show'),
        ('rejected',  'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_student'
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_staff'
    )
    date_time        = models.DateTimeField()
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason_for_visit = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('staff', 'date_time')
        ordering        = ['-date_time']

    def __str__(self):
        return f"Appointment: {self.student.username} with {self.staff.username} on {self.date_time}"


class AuditLog(models.Model):
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action    = models.CharField(max_length=50)
    details   = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.action} @ {self.timestamp}"


class MedicalTestSchedule(models.Model):
    """
    One row per new‐student medical test slot.
    """
    student = models.ForeignKey(
        Profile,
        limit_choices_to={'role': 'student'},
        on_delete=models.CASCADE,
        related_name='medical_tests',
        null=True,
        blank=True,
        help_text="(temporary) link to the student's profile"
    )

    # date/time slot
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()

    # who’s running it
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'profile__role': 'staff'},
        on_delete=models.PROTECT
    )
    ward_number = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']
        unique_together = ('student',)

    def __str__(self):
        matric = self.student.matric_no if self.student else '—'
        return f"{matric} → {self.scheduled_date} @ {self.scheduled_time}"
