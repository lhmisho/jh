from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from johukum.models import BusinessInfo
import pymongo


class Command(BaseCommand):
    help = 'Fix GEO search issues'

    def add_arguments(self, parser):
        # parser.add_argument('path', type=str, help='File path for the exported json file', def)
        pass

    def handle(self, *args, **kwargs):

        BusinessInfo.objects.mongo_update_many({'location.geo': ''}, {
            '$set': {
                'location.geo': None
            }
        })
        print("Fixing issues with lat long")
        for item in BusinessInfo.objects.mongo_find({'location.geo.type': 'Point'}):

            if len(item['location']['geo']['coordinates']) == 0:
                BusinessInfo.objects.mongo_update_one({'_id': item['_id']}, {
                    '$set': {
                        'location.geo': None
                    }
                })
            else:
                coordinates = item['location']['geo']['coordinates']
                if any([isinstance(x, str) for x in item['location']['geo']['coordinates']]):
                    for i in range(len(coordinates)):
                        if isinstance(coordinates[i], str):
                            coordinates[i] = coordinates[i].replace('-', '')
                            coordinates[i] = coordinates[i].replace(' ', '')
                            coordinates[i] = coordinates[i].replace(',', '.')
                            coordinates[i] = float(coordinates[i])

                if coordinates[0] < coordinates[1]:
                    tmp = coordinates[1]
                    coordinates[1] = coordinates[0]
                    coordinates[0] = tmp

                if coordinates[0] > 180 or coordinates[0] < -180 or coordinates[1] > 90 or coordinates[1] < -90:

                    BusinessInfo.objects.mongo_update_one({'_id': item['_id']}, {
                        '$set': {
                            'location.geoOld': item['location']['geo']['coordinates'],
                            'location.geo': None
                        }
                    })
                else:
                    BusinessInfo.objects.mongo_update_one({'_id': item['_id']}, {
                        '$set': {
                            'location.geo.coordinates': coordinates
                        }
                    })


        BusinessInfo.objects.mongo_create_index([('location.geo', pymongo.GEOSPHERE)])
