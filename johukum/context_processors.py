from django.conf import settings # import the settings file

def custom_values(request):
    return {
        'AGENT_GROUP': settings.AGENT_GROUP,
        'MODERATOR_GROUP': settings.MODERATOR_GROUP,
        'EDITOR_GROUP': settings.EDITOR_GROUP,
        'GCO_GROUP': settings.GCO_GROUP,
        'ADMIN_GROUP': settings.ADMIN_GROUP
    }