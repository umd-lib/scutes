# Generated by Django 4.2.3 on 2024-05-27 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processing', '0009_alter_batch_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='content_disposition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='content_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='content_type',
            field=models.TextField(blank=True, null=True),
        ),
    ]