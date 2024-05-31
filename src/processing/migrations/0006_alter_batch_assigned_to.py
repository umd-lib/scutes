# Generated by Django 4.2.3 on 2024-05-08 12:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("processing", "0005_batch_export_zip"),
    ]

    operations = [
        migrations.AlterField(
            model_name="batch",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]