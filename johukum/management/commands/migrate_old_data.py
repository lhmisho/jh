from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from johukum.models import *
from django.db import transaction

class Command(BaseCommand):
    help = 'Generates display name for all categories'

    def add_arguments(self, parser):
        # parser.add_argument('path', type=str, help='File path for the exported json file', def)
        pass

    @transaction.atomic
    def handle(self, *args, **kwargs):
        categories = Category.objects.all()

        for category in categories:
            if category._id == category.parent_id:
                category.parent = None
                category.save()
                print(category)

        for category in categories:
            self.generate_display_name(category)

    def generate_display_name(self, instance):
        if instance.display_name is None:
            display_name_builder = [instance.name]
            try:
                parent = instance.parent
                while parent is not None:
                    display_name_builder.append(parent.name)
                    parent = parent.parent
            except Exception as e:
                pass
            display_name_builder.reverse()
            display_name = ' > '.join(list(map(lambda x: x.strip(), display_name_builder)))
            if instance.display_name != display_name:
                instance.display_name = display_name
                instance.save()
            print(display_name)
