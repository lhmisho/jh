from rest_framework import renderers, utils
from bson import ObjectId

class JSONEncoder(utils.encoders.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return super().default(obj)

class JSONRenderer(renderers.JSONRenderer):
    encoder_class = JSONEncoder