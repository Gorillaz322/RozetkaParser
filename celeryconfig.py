from celery.schedules import crontab

import settings

BROKER_URL = settings.REDIS_URL

CELERY_RESULT_BACKEND = BROKER_URL

CELERYBEAT_SCHEDULE = {
    'save_products': {
        'task': 'tasks.update_products_main_task',
        'schedule': crontab(minute=0, hour=3),
    },
    'save_daily_price_changes_to_redis': {
        'task': 'tasks.save_daily_price_changes_to_redis_task',
        'schedule': crontab(minute=30, hour=3)
    }
}