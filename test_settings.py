
"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "default.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
    "read_replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "read_replica.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}


INSTALLED_APPS = (
    "platform_plugin_aspects",
)

EVENT_SINK_CLICKHOUSE_MODEL_CONFIG = {
    "user_profile": {
        "module": "common.djangoapps.student.models",
        "model": "UserProfile",
    },
    "course_overviews": {
        "module": "openedx.core.djangoapps.content.course_overviews.models",
        "model": "CourseOverview",
    }
}

EVENT_SINK_CLICKHOUSE_COURSE_OVERVIEWS_ENABLED = True

FEATURES = {
    'CUSTOM_COURSES_EDX': True,
}

DEBUG = True

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': False,
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth',  # this is required for admin
            'django.contrib.messages.context_processors.messages',  # this is required for admin
        ],
    },
}]

ASPECTS_INSTRUCTOR_DASHBOARD_UUID = "test-dashboard-uuid"

SUPERSET_CONFIG = {
    "url": "http://dummy-superset-url:8088",
    "username": "superset",
    "password": "superset",
}

SUPERSET_EXTRA_FILTERS_FORMAT = []
