from django.db import migrations, models


SPECIALTIES = (
    ("gastroenterology", "Гастроэнтерология", "лечение желудочно-кишечного тракта"),
    ("pulmonology", "Пульмонология", "лечение легких и дыхательных путей"),
    ("neurology", "Неврология", "лечение нервной системы"),
    ("endocrinology", "Эндокринология", "лечение желез внутренней секреции и гормональных нарушений"),
    ("hematology", "Гематология", "лечение крови и кроветворных органов"),
    ("rheumatology", "Ревматология", "лечение суставов и соединительной ткани"),
    ("dermatology", "Дерматология", "лечение кожи, ногтей и волос"),
    ("oncology", "Онкология", "лечение опухолевых заболеваний"),
    ("immunology", "Иммунология", "изучение и лечение нарушений иммунной системы"),
    ("hepatology", "Гепатология", "узкий раздел гастроэнтерологии, занимающийся печенью"),
)


def add_specialties(apps, schema_editor):
    database = schema_editor.connection.alias
    catalogue = apps.get_model("archive", "Area").objects.using(database)
    StudyArea = apps.get_model("archive", "StudyArea")
    personal = StudyArea.objects.using(database)

    for slug, name, description in SPECIALTIES:
        catalogue.update_or_create(slug=slug, defaults={"name": name, "description": description})
        personal.filter(name_key=name.casefold(), description="").update(description=description)

    owners = personal.order_by().values_list("owner_id", flat=True).distinct()
    for owner_id in owners.iterator():
        personal.bulk_create([
            StudyArea(owner_id=owner_id, slug=slug, name=name, name_key=name.casefold(), description=description)
            for slug, name, description in SPECIALTIES
        ], ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [("archive", "0008_pending_original_deletion")]

    operations = [
        migrations.AddField(
            model_name="area",
            name="description",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="studyarea",
            name="description",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.RunPython(add_specialties, migrations.RunPython.noop),
    ]
