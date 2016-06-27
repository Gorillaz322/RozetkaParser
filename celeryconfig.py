from datetime import timedelta

BROKER_URL = 'redis://localhost:6379/'

CELERY_RESULT_BACKEND = BROKER_URL

CELERY_TIMEZONE = 'UTC'