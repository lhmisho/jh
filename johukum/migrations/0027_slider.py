# Generated by Django 2.0 on 2019-11-20 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0026_auto_20191004_0513'),
    ]

    operations = [
        migrations.CreateModel(
            name='Slider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('banner_1', models.ImageField(blank=True, default=None, null=True, upload_to='uploads/%Y/%m/%d')),
            ],
        ),
    ]
