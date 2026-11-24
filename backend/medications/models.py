import uuid

from django.conf import settings
from django.db import models


class Medication(models.Model):
    class CourseType(models.TextChoices):
        REGULAR = "regular", "Регулярный"
        SINGLE = "single", "Разовый"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    dose = models.CharField(max_length=120, blank=True)
    course_type = models.CharField(max_length=7, choices=CourseType.choices)
    schedule = models.CharField(max_length=240, blank=True)
    start_date = models.DateField(null=True, blank=True)
    intake_date = models.DateField(null=True, blank=True)
    intake_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(course_type="regular", start_date__isnull=False,
                             intake_date__isnull=True, intake_time__isnull=True) & ~models.Q(schedule="")
                    | models.Q(course_type="single", start_date__isnull=True,
                               intake_date__isnull=False, schedule="")
                ),
                name="medication_has_course_fields",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(archived_at__isnull=True, end_date__isnull=True)
                    | models.Q(course_type="single", archived_at__isnull=False, end_date__isnull=True)
                    | models.Q(course_type="regular", archived_at__isnull=False, end_date__isnull=False,
                               end_date__gte=models.F("start_date"))
                ),
                name="medication_has_valid_end_date",
            ),
        ]
