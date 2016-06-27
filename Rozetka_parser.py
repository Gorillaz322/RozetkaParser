import json
import datetime
import re
import urllib

from flask import abort, render_template, request

from sqlalchemy.orm.exc import NoResultFound
import requests
from bs4 import BeautifulSoup

from app import app, db, logger
from models import Product, Price


@app.route('/')
def main():
    return render_template("Main.html")


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
    pages_amount = 5
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
                product['slug'],
                product['price'],
                datetime.date.today())

        logger.info('END OF HANDLING {} | page {}'.format(tag, current_page))

        current_page += 1

    db.session.commit()

    return True


@app.route('/product/<slug>')
def product_chart_handler(slug):
    try:
        product = Product.query.filter_by(slug=slug).one()
    except NoResultFound:
        return abort(404)

    data = {
        'dates': [],
        'prices': [{
            'data': [],
            'name': 'Product price'
        }]
    }

    [(data['dates'].append(str(item.date)),
      data['prices'][0]['data'].append(item.price))
     for item in product.prices.order_by(Price.date)]

    return render_template('Product.html', product=product, data=json.dumps(data))


@app.route('/autocomplete/product')
def product_autocomplete_handler():
    if 'query' not in request.args:
        return abort(404)

    query = request.args['query']

    search_string = query.strip()

    try:
        products = db.session.query(Product)\
            .filter(Product.name.startswith(search_string))\
            .limit(7)\
            .all()

        return json.dumps({
            'query': search_string,
            'suggestions': [
                {'value': pr.name, 'data': pr.slug}
                for pr in products
                ]
        })

    except NoResultFound:
        return json.dumps({
            'query': search_string,
            'suggestions': []
        })

