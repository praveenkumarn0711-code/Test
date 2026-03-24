from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def clear_employees(apps, schema_editor):
    Employee = apps.get_model("employee", "Employee")
    Employee.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("employee", "0003_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(clear_employees, migrations.RunPython.noop),
        migrations.AddField(
            model_name="employee",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="employees",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
