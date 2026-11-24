from rest_framework import serializers

from .models import Medication


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = (
            "id", "name", "dose", "course_type", "schedule", "start_date", "intake_date", "intake_time",
            "end_date", "created_at", "archived_at",
        )
        read_only_fields = ("end_date", "created_at", "archived_at")

    def validate(self, attrs):
        errors = {}
        if attrs["course_type"] == Medication.CourseType.REGULAR:
            if not attrs.get("schedule"):
                errors["schedule"] = "Укажите режим приёма."
            if not attrs.get("start_date"):
                errors["start_date"] = "Укажите дату начала курса."
            if attrs.get("intake_date"):
                errors["intake_date"] = "Дата приёма относится к разовой записи."
            if attrs.get("intake_time"):
                errors["intake_time"] = "Время приёма относится к разовой записи."
        else:
            if not attrs.get("intake_date"):
                errors["intake_date"] = "Укажите дату разового приёма."
            if attrs.get("schedule"):
                errors["schedule"] = "Режим приёма относится к регулярному курсу."
            if attrs.get("start_date"):
                errors["start_date"] = "Дата начала относится к регулярному курсу."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class MedicationArchiveSerializer(serializers.Serializer):
    end_date = serializers.DateField(allow_null=True, required=False)

    def validate(self, attrs):
        medication = self.instance
        end_date = attrs.get("end_date")
        if medication.course_type == Medication.CourseType.REGULAR:
            if end_date is None:
                raise serializers.ValidationError({"end_date": "Укажите фактическую дату окончания курса."})
            if end_date < medication.start_date:
                raise serializers.ValidationError({"end_date": "Дата окончания должна быть не раньше даты начала."})
        elif end_date is not None:
            raise serializers.ValidationError({"end_date": "Дата окончания относится к регулярному курсу."})
        return attrs
