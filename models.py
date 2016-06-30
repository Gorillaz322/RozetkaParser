from sqlalchemy.orm.exc import NoResultFound

from app import db


class Product(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    type = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(256), nullable=False, unique=True)

    @classmethod
    def get_or_create(cls, name, prod_type, slug, price, date):

        try:
            prod = Product.query.filter_by(slug=slug).one()
        except NoResultFound:
            prod = Product(name=name, slug=slug, type=prod_type)
            db.session.add(prod)

        if not prod.prices.filter_by(date=date).all():
            price_obj = Price(price=price, product=prod, date=date)
            db.session.add(price_obj)

        return prod


class Price(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    price = db.Column(db.Float(), nullable=False)
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product',
                              backref=db.backref("prices", lazy='dynamic'))
    date = db.Column(db.Date, nullable=False)



