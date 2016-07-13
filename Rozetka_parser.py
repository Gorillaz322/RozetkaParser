import json

from flask import abort, render_template, request
from sqlalchemy.orm.exc import NoResultFound

from app import app, db, app_redis
from models import Product, Price


@app.route('/')
def main():
    products_data_json = app_redis.get('daily_price_changes_json')
    products_data = json.loads(products_data_json)

    return render_template("Main.html", data=products_data)


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
      data['prices'][0]['data'].append(item.value))
     for item in product.prices.order_by(Price.date) if item.value]

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