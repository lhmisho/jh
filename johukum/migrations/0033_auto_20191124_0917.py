# Generated by Django 2.0 on 2019-11-24 09:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0032_user_varification_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=5, null=True)),
                ('comment', models.CharField(blank=True, default=None, max_length=500, null=True)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            managers=[
                ('dobjects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='businessinfo',
            name='aggregate_rating',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=19, null=True),
        ),
        migrations.AddField(
            model_name='businessinfo',
            name='total_reviews',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='review',
            name='business_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='johukum.BusinessInfo'),
        ),
    ]
