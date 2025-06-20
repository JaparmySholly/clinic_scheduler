# appointments/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Profile, Appointment

User = get_user_model()

class StudentSignUpForm(forms.Form):
    full_name    = forms.CharField(label="Full Name", max_length=150)
    matric_no    = forms.CharField(label="Matriculation Number", max_length=20)
    department   = forms.ChoiceField(label="Department", choices=Profile.DEPARTMENT_CHOICES)
    phone_number = forms.CharField(label="Phone Number", max_length=15, required=False)
    password1    = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2    = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords must match.")
        return cleaned

    def save(self, commit=True):
        full_name = self.cleaned_data["full_name"].strip()
        # use first word of the full name (lowercased) as the username
        username = full_name.split()[0].lower()

        user = User(username=username, first_name=full_name)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                role="student",
                matric_no=self.cleaned_data["matric_no"],
                department=self.cleaned_data["department"],
                phone_number=self.cleaned_data.get("phone_number", ""),
            )
        return user


class BookAppointmentForm(forms.ModelForm):
    date_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Appointment Date & Time"
    )

    class Meta:
        model = Appointment
        fields = ['staff', 'date_time', 'reason_for_visit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only staff users
        self.fields['staff'].queryset = User.objects.filter(profile__role='staff')

    def clean_date_time(self):
        dt = self.cleaned_data['date_time']
        if dt < timezone.now():
            raise forms.ValidationError("Cannot book an appointment in the past.")
        return dt

    def clean(self):
        cleaned = super().clean()
        staff = cleaned.get('staff')
        dt    = cleaned.get('date_time')
        if staff and dt:
            if Appointment.objects.filter(staff=staff, date_time=dt).exists():
                raise forms.ValidationError("Selected staff is not available at this date and time.")
        return cleaned
