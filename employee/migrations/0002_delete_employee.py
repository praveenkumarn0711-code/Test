# Generated manually — removes Employee model; profiles are not stored separately.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("employee", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Employee",
        ),
    ]
