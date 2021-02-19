# Generated by Django 2.0 on 2019-12-04 08:36

from django.db import migrations, models
import django.utils.timezone
import djongo.models.fields
import djongo.models.json


class Migration(migrations.Migration):

    dependencies = [
        ('johukum', '0034_auto_20191124_1131'),
    ]

    operations = [
        migrations.CreateModel(
            name='BangladeshMap',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, primary_key=True, serialize=False)),
                ('FID', models.CharField(max_length=255)),
                ('the_geom', djongo.models.json.JSONField(blank=True, null=True)),
                ('Div_ID', models.IntegerField(blank=True, null=True)),
                ('Dist_ID', models.IntegerField(blank=True, null=True)),
                ('Upz_ID', models.IntegerField(blank=True, null=True)),
                ('Un_ID', models.IntegerField(blank=True, null=True)),
                ('Un_UID', models.IntegerField(blank=True, null=True)),
                ('Divi_name', models.CharField(blank=True, max_length=255, null=True)),
                ('Dist_name', models.CharField(blank=True, max_length=255, null=True)),
                ('Upaz_name', models.CharField(blank=True, max_length=255, null=True)),
                ('Uni_name', models.CharField(blank=True, max_length=255, null=True)),
                ('Area_SqKm', models.DecimalField(blank=True, decimal_places=4, max_digits=11, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='review',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]