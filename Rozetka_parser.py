import json
import datetime

from flask import abort, render_template, request,\
    redirect, url_for

from sqlalchemy.orm.exc import NoResultFound

from app import app, db, app_redis
from models import Product, Price


@app.route('/')
def main():
    data_json = app_redis.get('daily_price_changes_json')
    data = json.loads(data_json)
    prod_data = {}

    def sort_products_by_daily_price_change(item):
        prices = item.prices.order_by(Price.date)
        return 100 - prices[-1].price * 100 / prices[-2].price

    for key in data:
        pr_data = data[key]
        prod_data[key] = {}
        for pr_key in pr_data:
            products = Product.query.filter(Product.slug.in_(pr_data[pr_key]))
            sorted_products = sorted(
                products, key=sort_products_by_daily_price_change)
            prod_data[key][pr_key] = sorted_products

    return render_template("Main.html", data=prod_data, price_date_obj=Price.date)


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


@app.route('/price_changes/daily')
def order_products_by_price_change_daily():
    product_data = []
    for prod in Product.query.all():
        prices = prod.prices.order_by(Price.date)

        changes_rate = 0
        if len(prices.all()) >= 2 and \
                prices[-2].price != 0 and prices[-1].price != 0:
            changes_rate = 100 - prices[-1].price * 100 / prices[-2].price

        if changes_rate == 0:
            continue
        elif changes_rate < 0:
            price_change_type = 'decrease'
        else:
            price_change_type = 'increase'

        product_data.append({
            'product': prod,
            'changes_rate': changes_rate,
            'price_change_type': price_change_type
        })

    sorted_data = sorted(Product.query.all(),
                         key=lambda item: 100 - item.prices.order_by(Price.date)[-1].price * 100 /
                                                item.prices.order_by(Price.date)[-2].price,
                         reverse=True)

    return render_template('PriceChanges.html', data=sorted_data)


@app.route('/order_products/<order_type>')
def order_products_by_price(order_type):
    current_date = datetime.datetime.now()
    if order_type == 'day':
        timedelta_days = 2
    elif order_type == 'week':
        timedelta_days = 8
    elif order_type == 'month':
        timedelta_days = 31
    elif order_type == 'all_time':
        timedelta_days = 100
    else:
        return redirect_to_order_page()

    products_data = []

    def get_closest_price_by_date(pr_list, main_date):
        def key_func(item):
            date = item.date
            delta = date - main_date \
                if date > main_date and item.price != 0 \
                else datetime.timedelta.max
            return delta

        return min(pr_list, key=key_func)

    for product in Product.query.all():
        prices = product.prices.order_by(Price.date)
        if len(prices.all()) < 2 or \
                prices[-1].date != current_date.date() or \
                prices[-1].price == 0:
            continue

        if timedelta_days == 100:
            start_price = get_closest_price_by_date(prices, prices[0].date)
        else:
            start_price = \
                get_closest_price_by_date(
                    prices,
                    (current_date - datetime.timedelta(days=timedelta_days)).date())

        price_change = 100 - prices[-1].price * 100 / start_price.price

        if price_change == 0:
            continue

        products_data.append({
            'product': product,
            'price_change': price_change,
            'start_price': start_price,
            'end_price': prices[-1]
        })

    return products_data


def redirect_to_order_page():
    return redirect(url_for('order_products_by_price', order_type='day'))

app.add_url_rule('/order_products',
                 view_func=redirect_to_order_page)
