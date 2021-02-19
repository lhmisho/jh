from django.contrib import admin
from django import forms
from johukum import models


class BangladeshMapModelForm(forms.ModelForm):
    class Meta:
        model = models.BangladeshMap
        exclude = ['the_geom']


class BangladeshMapAdmin(admin.ModelAdmin):
    form = BangladeshMapModelForm
    search_fields = ('Uni_name', 'Upaz_name', 'Dist_name', 'Divi_name')


admin.site.register(models.Snippet)
admin.site.register(models.Page)
admin.site.register(models.Slider)
admin.site.register(models.Review)
admin.site.register(models.BangladeshMap, BangladeshMapAdmin)
