# Generated by Django 2.0 on 2019-11-21 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0031_auto_20191120_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='varification_code',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
