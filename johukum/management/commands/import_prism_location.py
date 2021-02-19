from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from johukum.models import Location

class Command(BaseCommand):
    help = 'Imports prism location from a file'

    def add_arguments(self, parser):
        # parser.add_argument('path', type=str, help='File path for the exported json file', def)
        pass

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'data', 'location.json')

        with open(path, 'r') as f:
            data = json.load(f)

        

        object_id_mapper = {}
        
        for item in data:
            location, _ = Location.objects.get_or_create(
                prism_id = item.get('id'),
                defaults = {
                    'location_type': item.get('type'),
                    'name': item.get('name')
                }    
            )

            print('Location %s added\n' % item.get('name'))
            object_id_mapper[item.get('id')] = location
        

        print('\n\n-------------------\n\n')
        for item in data:
            if item.get('parent_id'):
                location = object_id_mapper[item.get('id')]
                parent = object_id_mapper[item.get('parent_id')]
                location.parent = parent
                location.save()
                print('Parent added to %s\n' % item.get('name'))

