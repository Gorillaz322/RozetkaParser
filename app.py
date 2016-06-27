import os
import logging

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from celery import Celery
from celery.schedules import crontab

import celeryconfig

app = Flask(__name__)

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
        'schedule': crontab(minute=0, hour=21),
    }
}

celery.conf.defaults[1]['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE

import Rozetka_parser
import models
import tasks