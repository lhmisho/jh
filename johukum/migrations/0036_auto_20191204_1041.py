# Generated by Django 2.0 on 2019-12-04 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0035_auto_20191204_0836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bangladeshmap',
            name='Area_SqKm',
            field=models.DecimalField(blank=True, decimal_places=12, max_digits=20, null=True),
        ),
    ]
