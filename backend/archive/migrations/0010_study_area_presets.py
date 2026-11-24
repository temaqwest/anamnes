import django.db.models.deletion
from django.db import migrations, models


IMMUNOLOGY_NAME = "Иммунология"
IMMUNOLOGY_DESCRIPTION = "изучение и лечение нарушений иммунной системы"

UPDATED_PRESETS = (
    ("immunology", "Аллергология и иммунология", "аллергические заболевания и нарушения иммунной системы"),
    ("obstetrics_gynecology", "Акушерство и гинекология", "беременность, роды и здоровье женской репродуктивной системы"),
    ("nephrology", "Нефрология", "заболевания почек"),
    ("urology", "Урология", "заболевания мочевыводящих путей и мужской репродуктивной системы"),
    ("otolaryngology", "Оториноларингология (ЛОР)", "заболевания уха, горла и носа"),
    ("ophthalmology", "Офтальмология", "заболевания глаз и нарушения зрения"),
    ("orthopedics", "Травматология и ортопедия", "травмы и заболевания опорно-двигательного аппарата"),
)

ALIASES = {
    "immunology": ("иммунология", "аллергология", "аллергология-иммунология"),
    "obstetrics_gynecology": ("гинекология", "акушерство", "акушерство-гинекология"),
    "otolaryngology": ("лор", "оториноларингология", "отоларингология", "лор-заболевания"),
    "orthopedics": (
        "ортопедия", "травматология", "ортопедия и травматология", "травматология-ортопедия",
        "травматология/ортопедия", "травматология / ортопедия",
    ),
}


def bind_presets(apps, schema_editor):
    alias = schema_editor.connection.alias
    catalogue = apps.get_model("archive", "Area").objects.using(alias)
    StudyArea = apps.get_model("archive", "StudyArea")
    personal = StudyArea.objects.using(alias)

    for slug, name, description in UPDATED_PRESETS:
        catalogue.update_or_create(slug=slug, defaults={"name": name, "description": description})
    presets = list(catalogue.order_by("slug"))
    preset_slugs = {preset.slug for preset in presets}

    owners = personal.order_by().values_list("owner_id", flat=True).distinct()
    for owner_id in owners.iterator():
        owned = list(personal.filter(owner_id=owner_id).order_by("pk"))
        by_name = {area.name_key: area for area in owned}
        # Reserve the original default rows before matching names or aliases.
        by_preset = {area.slug: area for area in owned if area.slug in preset_slugs}
        for slug, area in by_preset.items():
            area.preset_id = slug

        new_areas = []
        for preset in presets:
            slug, name, description = preset.slug, preset.name, preset.description
            name_key = name.casefold()
            area = by_preset.get(slug)
            if area is None:
                for matching_name in (name_key, *ALIASES.get(slug, ())):
                    candidate = by_name.get(matching_name)
                    if candidate is not None and candidate.preset_id is None:
                        area = candidate
                        break
            if area is None:
                # A renamed default may already occupy the canonical name.
                if name_key not in by_name:
                    new_areas.append(StudyArea(
                        owner_id=owner_id, preset_id=slug, slug=slug, name=name, name_key=name_key,
                        description=description,
                    ))
                continue

            area.preset_id = slug
            if slug == "immunology" and area.name == IMMUNOLOGY_NAME and name_key not in by_name:
                area.name = name
                area.name_key = name_key
                if area.description == IMMUNOLOGY_DESCRIPTION:
                    area.description = description

        personal.bulk_update(owned, ["preset", "name", "name_key", "description"])
        personal.bulk_create(new_areas)

    # Validate deferred foreign keys before Django creates the new index.
    schema_editor.connection.check_constraints(table_names=[StudyArea._meta.db_table])


class Migration(migrations.Migration):
    dependencies = [("archive", "0009_study_area_descriptions")]

    operations = [
        migrations.AddField(
            model_name="studyarea",
            name="preset",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="+", to="archive.area",
            ),
        ),
        migrations.AddConstraint(
            model_name="studyarea",
            constraint=models.UniqueConstraint(fields=("owner", "preset"), name="unique_study_area_preset"),
        ),
        migrations.RunPython(bind_presets, migrations.RunPython.noop),
    ]
