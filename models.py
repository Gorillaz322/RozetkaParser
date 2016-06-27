from sqlalchemy.orm.exc import NoResultFound

from app import db


class Product(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(256))
    slug = db.Column(db.String(256), unique=True)

    @classmethod
    def get_or_create(cls, name, slug, price, date):

        try:
            prod = Product.query.filter_by(slug=slug).one()
        except NoResultFound:
            prod = Product(name=name, slug=slug)
            db.session.add(prod)

        if not prod.prices.filter_by(date=date).all():
            price_obj = Price(price=price, product=prod, date=date)
            db.session.add(price_obj)

        return prod


class Price(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    price = db.Column(db.Float())
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id'))
    product = db.relationship('Product',
                              backref=db.backref("prices", lazy='dynamic'))
    date = db.Column(db.Date)



