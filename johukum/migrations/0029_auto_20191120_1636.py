# Generated by Django 2.0 on 2019-11-20 16:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0028_slider_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='slider',
            old_name='banner_1',
            new_name='banner',
        ),
    ]
