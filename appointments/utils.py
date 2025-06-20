# appointments/utils.py

import itertools
from datetime import timedelta, time
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from .models import MedicalTestSchedule, Profile

User = get_user_model()

def _make_unique_username(base):
    """
    Normalize a candidate username and, if taken, append a counter.
    """
    uname = base.lower().replace(" ", "")
    if not User.objects.filter(username=uname).exists():
        return uname
    # try uname1, uname2, … until we find a free one
    for i in itertools.count(1):
        trial = f"{uname}{i}"
        if not User.objects.filter(username=trial).exists():
            return trial

def allocate_medical_tests(students_list):
    """
    students_list: list of dicts with keys 'name', 'matric_no', 'department'
    
    Steps:
    1) get_or_create User(username=first_name) + Profile(role=student)
    2) sync Profile.matric_no & Profile.department
    3) assign sequential dates/times
    4) rotate staff & wards
    """
    start_date   = timezone.localdate() + timedelta(days=1)
    daily_slots  = [time(9,0), time(9,30), time(10,0), time(10,30),
                    time(11,0), time(11,30), time(12,0)]
    ward_numbers = [f"W{n}" for n in range(1, 11)]

    staff_cycle = itertools.cycle(
        User.objects.filter(profile__role="staff")
    )
    slot_cycle = itertools.cycle(daily_slots)
    ward_cycle = itertools.cycle(ward_numbers)

    current_date = start_date

    for row in students_list:
        name      = (row.get("name") or row.get("full name") or "").strip()
        matric_no = (row.get("matric_no") or row.get("matric no") or "").strip()
        dept      = (row.get("department") or row.get("dept") or "").strip()

        if not (name and matric_no):
            continue

        # --- 1) create or get User with first-name login ---
        first = name.split()[0]
        uname = _make_unique_username(first)
        try:
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={"first_name": name}
            )
        except IntegrityError:
            # rare race condition: regenerate
            uname = _make_unique_username(first)
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={"first_name": name}
            )

        if created:
            user.set_password(matric_no)
            user.save()

        # --- 2) sync Profile ---
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={"role": "student"}
        )
        changed = False
        if profile.matric_no != matric_no:
            profile.matric_no = matric_no
            changed = True
        if profile.department != dept:
            profile.department = dept
            changed = True
        if changed:
            profile.save()

        # --- 3) pick next slot & bump date when wrapping ---
        slot = next(slot_cycle)
        if slot == daily_slots[0]:
            current_date += timedelta(days=1)

        # --- 4) create the MedicalTestSchedule ---
        MedicalTestSchedule.objects.create(
            student        = profile,
            scheduled_date = current_date,
            scheduled_time = slot,
            staff          = next(staff_cycle),
            ward_number    = next(ward_cycle),
        )
