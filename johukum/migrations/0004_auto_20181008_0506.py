# Generated by Django 2.1.2 on 2018-10-08 05:06

from django.db import migrations, models
import zero_auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0003_auto_20181002_0608'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', zero_auth.models.UserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='email address'),
        ),
    ]