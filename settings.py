import os

if os.environ.get('REDIS_URL'):
    REDIS_URL = os.environ['REDIS_URL']
else:
    REDIS_URL = 'redis://h:puprotofkmnugcjbfecic9803t@ec2-54-243-230-243.' \
                'compute-1.amazonaws.com:12169'

DATABASE_URL = os.environ.get('DATABASE_URL')

AWS_S3_BUCKET_NAME = 'rozetka-parser'

REGION_HOST = os.environ.get('REGION_HOST')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')