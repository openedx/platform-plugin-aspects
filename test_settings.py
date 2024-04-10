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
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "platform_plugin_aspects",
)

ROOT_URLCONF = 'platform_plugin_aspects.urls'

SECRET_KEY = 'very-insecure-key'

MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

EVENT_SINK_CLICKHOUSE_MODEL_CONFIG = {
    "auth_user": {
        "module": "django.contrib.auth.models",
        "model": "User",
    },
    "user_profile": {
        "module": "common.djangoapps.student.models",
        "model": "UserProfile",
    },
    "course_overviews": {
        "module": "openedx.core.djangoapps.content.course_overviews.models",
        "model": "CourseOverview",
    },
    "external_id": {
        "module": "openedx.core.djangoapps.external_user_ids.models",
        "model": "ExternalId",
    },
    "user_preference": {
        "module": "openedx.core.djangoapps.user_api.models",
        "model": "UserPreference",
    },
}

EVENT_SINK_CLICKHOUSE_COURSE_OVERVIEWS_ENABLED = True

FEATURES = {
    "CUSTOM_COURSES_EDX": True,
}

DEBUG = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",  # this is required for admin
                "django.contrib.messages.context_processors.messages",  # this is required for admin
            ],
        },
    }
]

SUPERSET_EXTRA_FILTERS_FORMAT = []

SUPERSET_CONFIG = {
    "internal_service_url": "http://superset:8088",
    "service_url": "http://dummy-superset-url",
    "username": "superset",
    "password": "superset",
}

SUPERSET_CONFIG = {
    "internal_service_url": "http://superset:8088",
    "service_url": "http://superset.local.overhang.io",
    "username": "superset",
    "password": "superset",
}
ASPECTS_INSTRUCTOR_DASHBOARDS = [
    {
        "name": "Instructor Dashboard",
        "slug": "instructor-dashboard",
        "uuid": "1d6bf904-f53f-47fd-b1c9-6cd7e284d286",
        "allow_translations": True,
    }
]
EVENT_SINK_CLICKHOUSE_BACKEND_CONFIG = {
    "url": "https://foo.bar",
    "username": "bob",
    "password": "secret",
    "database": "cool_data",
    "timeout_secs": 1,
}

SUPERSET_DASHBOARD_LOCALES = ["en_US", "es_419"]
