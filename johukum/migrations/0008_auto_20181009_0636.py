# Generated by Django 2.1.2 on 2018-10-09 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0007_auto_20181009_0450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessinfo',
            name='annual_turnover',
            field=models.CharField(blank=True, choices=[('1-500000', '1-500000'), ('500001-1000000', '500001-1000000'), ('1000001-5000000', '1000001-5000000'), ('5000001-20000000', '5000001-20000000'), ('20000001-50000000', '20000001-50000000'), ('50000001+', '50000001+')], max_length=30, null=True),
        ),
    ]
