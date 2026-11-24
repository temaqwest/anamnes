import uuid

from django.conf import settings
from django.db import models


def original_path(document, filename):
    return f"originals/{document.owner_id}/{document.id}.pdf"


class Area(models.Model):
    """Catalogue used to initialise each user's areas."""

    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300, blank=True, default="")


class StudyArea(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    preset = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    slug = models.SlugField()
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300, blank=True, default="")
    name_key = models.CharField(max_length=300, editable=False)

    class Meta:
        ordering = ["name", "slug"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug"], name="unique_study_area_slug"),
            models.UniqueConstraint(fields=["owner", "name_key"], name="unique_study_area_name"),
            models.UniqueConstraint(fields=["owner", "preset"], name="unique_study_area_preset"),
        ]


class Document(models.Model):
    class Category(models.TextChoices):
        DOCTOR_REPORT = "doctor_report", "Заключение врача"
        EXAMINATION = "examination", "Обследование"
        LAB = "lab", "Анализ"

    class IndexStatus(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        READY = "ready"
        NO_TEXT = "no_text"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original = models.FileField(upload_to=original_path)
    original_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=16, choices=Category, blank=True, default="")
    study_date = models.DateField()
    areas = models.ManyToManyField(StudyArea, blank=True, db_table="archive_document_study_areas")
    created_at = models.DateTimeField(auto_now_add=True)
    upload_key = models.UUIDField(null=True, editable=False)
    index_status = models.CharField(max_length=10, choices=IndexStatus, default=IndexStatus.PENDING, db_index=True)
    index_started_at = models.DateTimeField(null=True, editable=False)
    index_claim = models.UUIDField(null=True, editable=False)

    class Meta:
        ordering = ["-study_date", "-created_at", "id"]
        indexes = [
            models.Index(fields=["owner", "-study_date"]),
            models.Index(fields=["owner", "original_name"], name="document_owner_filename_idx"),
        ]
        constraints = [models.UniqueConstraint(fields=["owner", "upload_key"], name="unique_owner_upload")]


class DocumentPage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="indexed_pages")
    number = models.PositiveIntegerField()
    text = models.TextField()
    search_text = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "number"], name="unique_document_page")]


class PendingOriginalDeletion(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
