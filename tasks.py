import datetime
import re
import urllib
import json

from app import celery as flask_celery, logger, app_redis, db
from Rozetka_parser import Price, Product

import requests
from bs4 import BeautifulSoup

TAGS = ['notebooks/c80004', 'computers/c80095', 'tablets/c130309',
        'mobile-phones/c80003', 'photo/c80001', 'refrigerators/c80125',
        'washing_machines/c80124']


def get_products_per_page(tag, page=1):
    products = []

    response = requests.get(
        'http://rozetka.com.ua/{}/filter?page={}'.format(tag, page))
    try:
        response.request.path_url.split('/')[4]
    except IndexError:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    for product_el in soup.find_all('div',
                                    attrs={'class': 'g-i-tile-i-box-desc'}):

        raw_name = product_el.find('div', class_='g-i-tile-i-title')\
            .contents[1].contents[0]

        name = raw_name.encode('ascii', errors='ignore').strip()

        link = product_el\
            .find(attrs={'class': 'g-i-tile-i-title clearfix'})\
            .find('a').get('href')

        slug = link.split('/')[3]

        price_box = product_el.find('div', attrs={
                                'class': 'inline',
                                'name': 'prices_active_element_original'
                            })

        if price_box:
            raw_js = price_box.contents[5].text

            raw_price_data = re.findall(
                r'var.*?=\s*(.*?);', raw_js, re.DOTALL | re.MULTILINE)[0]

            price_data_str = urllib.unquote(json.loads(raw_price_data)) \
                .decode('utf8')

            price_dict = eval(price_data_str)

            price = int(price_dict['price'])
        else:
            price = 0

        products.append({
            'name': name,
            'slug': slug,
            'price': price
        })

    return products


def save_products(tag):
    # response = requests.get(
    #     'http://rozetka.com.ua/{}/filter'.format(tag))
    # soup = BeautifulSoup(response.content, 'html.parser')
    # pages_amount = int(
    #     soup.find_all('li', attrs={'class': 'paginator-catalog-l-i'})[-1]
    #         .get('id')[4:])
    pages_amount = 6
    logger.info('{} has {} pages'.format(tag, pages_amount))

    current_page = 1
    while current_page <= pages_amount:
        logger.info('START OF HANDLING {} | page {}'.format(tag, current_page))

        products = get_products_per_page(tag, page=current_page)
        if not products:
            return True

        for product in products:
            Product.get_or_create(
                product['name'],
                tag.split('/')[0],
                product['slug'],
                product['price'],
                datetime.date.today())

        logger.info('END OF HANDLING {} | page {}'.format(tag, current_page))

        current_page += 1

    db.session.commit()

    return True


def save_daily_price_changes_to_redis():
    data = {}
    current_date = datetime.datetime.now()
    yesterday_date = current_date - datetime.timedelta(days=1)

    for product in Product.query.all():
        if len(product.prices.all()) < 2:
            continue

        prices = product.prices.order_by(Price.date)

        today_price = prices[-1]
        yesterday_price = prices[-2]

        if (int(today_price.price) and int(yesterday_price.price)) == 0:
            continue

        if prices[-1].date != current_date.date() or \
                prices[-2].date != yesterday_date.date():
            continue

        if product.type not in data:
            data[product.type] = {}
            data[product.type]['increase'] = []
            data[product.type]['decrease'] = []

        price_change = int(yesterday_price.price - today_price.price)

        if price_change > 0:
            data[product.type]['decrease'].append(product.slug)
        elif price_change < 0:
            data[product.type]['increase'].append(product.slug)

    app_redis.delete('daily_price_changes')
    app_redis.set("daily_price_changes_json", json.dumps(data))

    return True


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


@flask_celery.task()
def save_daily_price_changes_to_redis_task():
    save_daily_price_changes_to_redis()
    return 'Success'

