web: gunicorn run:app --log-file -
worker: celery -A app.celery worker -c 6 --loglevel=info -B