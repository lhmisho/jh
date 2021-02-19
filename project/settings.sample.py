from project.settings_base import *


DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'johukumdb',
        'ENFORCE_SCHEMA': False
    }
}

# ZERO_AUTH_MAX_RETRY = 10
# ZERO_AUTH_LOCK_TIMEOUT = 20