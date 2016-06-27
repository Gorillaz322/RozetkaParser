from app import celery as flask_celery, logger
from Rozetka_parser import save_products

TAGS = ['notebooks/c80004', 'computers/c80095', 'tablets/c130309',
        'mobile-phones/c80003', 'photo/c80001', 'refrigerators/c80125',
        'washing_machines/c80124']


@flask_celery.task()
def update_products_by_tag(tag):
    logger.info('START UPDATE FOR {}'.format(tag))
    save_products(tag)


@flask_celery.task()
def update_products_main_task():
    logger.info('START OF MAIN UPDATE')
    for tag in TAGS:
        update_products_by_tag.apply_async(args=[tag])
    logger.info('END OF MAIN UPDATE')
    return 'Success'
