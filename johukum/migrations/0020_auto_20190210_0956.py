# Generated by Django 2.0 on 2019-02-10 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0019_auto_20190121_0907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobilenumberdata',
            name='store_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Organaization'),
        ),
    ]
