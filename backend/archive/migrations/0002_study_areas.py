from django.db import migrations


def add_study_areas(apps, schema_editor):
    Area = apps.get_model("archive", "Area")
    for slug, name in [
        ("thyroid", "Щитовидная железа"),
        ("cardiology", "Кардиология"),
        ("gastroenterology", "Гастроэнтерология"),
        ("hematology", "Гематология"),
        ("general", "Общий обзор"),
    ]:
        Area.objects.using(schema_editor.connection.alias).get_or_create(slug=slug, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("archive", "0001_initial")]
    operations = [migrations.RunPython(add_study_areas, migrations.RunPython.noop)]
