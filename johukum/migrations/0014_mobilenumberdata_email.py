# Generated by Django 2.0 on 2019-01-09 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0013_auto_20190109_0600'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilenumberdata',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]