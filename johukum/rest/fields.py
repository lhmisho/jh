from rest_framework import fields

class ObjectIDField(fields.IntegerField):

    def to_representation(self, value):
        return str(value)


class EmbededModelField(fields.Field):

    def to_representation(self, value):
        return value.to_dict()

    