# Generated by Django 2.0 on 2019-01-09 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0015_mobilenumberdata_land_line_numbers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobilenumberdata',
            name='name',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]
