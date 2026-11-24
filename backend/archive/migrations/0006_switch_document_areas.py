from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("archive", "0005_personal_study_areas")]

    operations = [
        migrations.RemoveField(model_name="document", name="areas"),
        migrations.RenameField(model_name="document", old_name="personal_areas", new_name="areas"),
    ]
