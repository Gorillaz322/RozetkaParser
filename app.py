import os
import logging
import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from celery import Celery

import redis
import boto.s3.connection

import celeryconfig
import settings

app = Flask(__name__)

app_redis = redis.from_url(settings.REDIS_URL)

app.debug = True

app.config.update(
    SQLALCHEMY_DATABASE_URI=settings.DATABASE_URL
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

celery.conf.defaults[1]['CELERYBEAT_SCHEDULE'] = celeryconfig.CELERYBEAT_SCHEDULE

conn = boto.s3.connect_to_region(settings.REGION_HOST,
                                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 is_secure=True,
                                 calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                 )
bucket = conn.get_bucket(settings.AWS_S3_BUCKET_NAME)

import Rozetka_parser
import models
import tasks