web: gunicorn run:app --log-file -
worker: celery -A app.celery worker --concurrency=4 --loglevel=info -B