import os
import logging
import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from celery import Celery
from celery.schedules import crontab
import redis
import boto.s3.connection

import celeryconfig

app = Flask(__name__)

app_redis = redis.from_url(os.environ.get('REDIS_URL'))

app.debug = True

app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL')
)

db = SQLAlchemy(app)

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.getLogger("requests").setLevel(logging.WARNING)


def make_celery(flask_app):
    celery_obj = Celery(
        flask_app.import_name)
    celery_obj.config_from_object(celeryconfig)
    TaskBase = celery_obj.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_obj.Task = ContextTask
    return celery_obj

celery = make_celery(app)

CELERYBEAT_SCHEDULE = {
    'save_products': {
        'task': 'tasks.update_products_main_task',
        'schedule': datetime.timedelta(seconds=15),
    },
    'save_daily_price_changes_to_redis': {
        'task': 'tasks.save_daily_price_changes_to_redis_task',
        'schedule': crontab(minute=30, hour=3)
    }
}


celery.conf.defaults[1]['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

conn = boto.s3.connect_to_region(os.environ.get('REGION_HOST'),
                                 aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                                 is_secure=True,
                                 calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                 )
bucket = conn.get_bucket('rozetka-parser')

import Rozetka_parser
import models
import tasks