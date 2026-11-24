from pathlib import PurePath
from uuid import uuid4

from django.db import IntegrityError, transaction
from django.urls import reverse
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from rest_framework import serializers

from .models import Document, StudyArea
from .study_areas import areas_for, normalize_area_name


class FilenameBatchSerializer(serializers.Serializer):
    names = serializers.ListField(child=serializers.CharField(max_length=255), min_length=1, max_length=10)


class DocumentQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=120, allow_blank=True, default="")
    category = serializers.ChoiceField(choices=[*Document.Category.values, "uncategorized"], allow_blank=True, default="")


class DocumentDeletionSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, required=False)
    all = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if set(attrs) == {"ids"} or attrs == {"all": True}:
            return attrs
        raise serializers.ValidationError("Укажите выбранные документы или подтвердите удаление всего архива.")


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyArea
        fields = ["slug", "name", "description"]
        read_only_fields = ["slug"]

    def other_areas(self):
        areas = areas_for(self.context["request"].user)
        return areas.exclude(pk=self.instance.pk) if self.instance else areas

    def validate_name(self, name):
        name = normalize_area_name(name)
        if self.other_areas().filter(name_key=name.casefold()).exists():
            raise serializers.ValidationError("Такая область уже есть.")
        return name

    def save(self, **kwargs):
        name = self.validated_data.get("name")
        if name is not None:
            kwargs["name_key"] = name.casefold()
        if self.instance is None:
            kwargs.update(owner=self.context["request"].user, slug=uuid4().hex)
        try:
            with transaction.atomic():
                return super().save(**kwargs)
        except IntegrityError:
            if name is not None and self.other_areas().filter(name_key=kwargs["name_key"]).exists():
                raise serializers.ValidationError({"name": "Такая область уже есть."}) from None
            raise


class StudyAreaField(serializers.SlugRelatedField):
    def get_queryset(self):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return StudyArea.objects.none()
        return areas_for(request.user)


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    file_url = serializers.SerializerMethodField()
    upload_key = serializers.UUIDField(write_only=True, required=False)
    search_match = serializers.SerializerMethodField()
    areas = StudyAreaField(many=True, slug_field="slug", required=False)

    class Meta:
        model = Document
        fields = [
            "id", "file", "file_url", "original_name", "title", "category", "study_date", "areas",
            "upload_key", "index_status", "search_match",
        ]
        read_only_fields = ["id", "original_name", "index_status"]

    def get_file_url(self, document):
        return reverse("original", args=[document.id])

    def get_search_match(self, document):
        return getattr(document, "search_match", None)

    def validate_file(self, uploaded):
        if PurePath(uploaded.name).suffix.lower() != ".pdf" or uploaded.read(5) != b"%PDF-":
            raise serializers.ValidationError("Выберите файл в формате PDF.")
        if uploaded.size > 25 * 1024 * 1024:
            raise serializers.ValidationError("Размер PDF должен быть не больше 25 МБ.")
        uploaded.seek(0)
        try:
            pdf = PdfReader(uploaded)
            if pdf.is_encrypted or not len(pdf.pages):
                raise serializers.ValidationError("Нужен PDF со страницами и без пароля.")
        except (PdfReadError, ValueError, RecursionError) as error:
            raise serializers.ValidationError("PDF не удалось прочитать.") from error
        uploaded.seek(0)
        return uploaded

    def create(self, validated_data):
        uploaded = validated_data.pop("file")
        areas = validated_data.pop("areas", [])
        document = Document(original_name=uploaded.name, **validated_data)
        previous = Document.objects.filter(owner=document.owner, upload_key=document.upload_key)
        if document.upload_key and (existing := previous.first()):
            return existing

        document.original.save(uploaded.name, uploaded, save=False)
        try:
            with transaction.atomic():
                document.save()
                document.areas.set(areas)
        except Exception as error:
            document.original.delete(save=False)
            if isinstance(error, IntegrityError) and document.upload_key and (existing := previous.first()):
                return existing
            raise
        return document


class DocumentEditSerializer(DocumentSerializer):
    class Meta(DocumentSerializer.Meta):
        fields = ["id", "file_url", "original_name", "title", "category", "study_date", "areas", "index_status", "search_match"]

    file = None
    upload_key = None

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
