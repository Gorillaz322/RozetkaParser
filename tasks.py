import datetime
import re
import urllib
import json

import requests
from bs4 import BeautifulSoup
from sqlalchemy import func

from app import celery as flask_celery, logger, app_redis,\
    db
import models

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

        img_url = product_el.find(
            'div', class_=['g-i-tile-i-image']).find('img').get('data_src')

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
            'price': price,
            'img': img_url,
            'link': link
        })

    return products


def save_products(tag):
    # response = requests.get(
    #     'http://rozetka.com.ua/{}/filter'.format(tag))
    # soup = BeautifulSoup(response.content, 'html.parser')
    # pages_amount = int(
    #     soup.find_all('li', attrs={'class': 'paginator-catalog-l-i'})[-1]
    #         .get('id')[4:])
    pages_amount = 7
    logger.info('{} has {} pages'.format(tag, pages_amount))

    current_page = 1
    while current_page <= pages_amount:
        logger.info('START OF HANDLING {} | page {}'.format(tag, current_page))

        products = get_products_per_page(tag, page=current_page)
        if not products:
            return True

        for product in products:
            models.Product.get_or_create(
                product['name'],
                tag.split('/')[0],
                product['link'],
                product['slug'],
                product['price'],
                datetime.date.today(),
                img=product['img'])

        logger.info('END OF HANDLING {} | page {}'.format(tag, current_page))

        current_page += 1

    db.session.commit()

    return True


def save_daily_price_changes_to_redis():
    data = {}
    current_date = datetime.datetime.now()

    for product in models.Product.query\
            .join(models.Price)\
            .group_by(models.Product.id)\
            .having(func.count(models.Price.id) >= 2):

        prices = product.prices.order_by(models.Price.date)

        today_price = prices[-1]
        yesterday_price = prices[-2]

        if not (today_price.value and yesterday_price.value):
            continue

        if prices[-1].date != current_date.date():
            continue

        if product.type not in data:
            data[product.type] = {}
            data[product.type]['increase'] = []
            data[product.type]['decrease'] = []

        price_change = yesterday_price.value - today_price.value

        product_info = {
            'name': product.name,
            'slug': product.slug,
            'yesterday_price': yesterday_price.value,
            'current_price': today_price.value
        }

        if price_change > 0:
            data[product.type]['decrease'].append(product_info)
        elif price_change < 0:
            data[product.type]['increase'].append(product_info)

    def sort_products_by_price_change(item):
        return 100 - item['current_price'] * 100 / item['yesterday_price']

    sorted_data = {}

    for product_type in data:
        products_info = data[product_type]
        sorted_data[product_type] = {}

        for price_change_type in products_info:
            sorted_products = sorted(
                products_info[price_change_type],
                key=sort_products_by_price_change)

            sorted_data[product_type][price_change_type] = \
                sorted_products

    app_redis.set("daily_price_changes_json", json.dumps(sorted_data))

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

