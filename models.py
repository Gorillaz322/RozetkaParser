import urllib2
import StringIO

from sqlalchemy.orm.exc import NoResultFound
from boto.s3.connection import Key

from app import db, bucket

BUCKET_LIST = [item.key for item in list(bucket.list())]


class Product(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    type = db.Column(db.String(256), nullable=False)
    link = db.Column(db.String(256))
    img = db.Column(db.String(256))
    slug = db.Column(db.String(256), nullable=False, unique=True)

    @classmethod
    def get_or_create(cls, name, prod_type, link, slug, value, date, img=None):

        try:
            prod = Product.query.filter_by(slug=slug).one()
            if not prod.link:
                prod.link = link
        except NoResultFound:
            prod = Product(
                name=name,
                slug=slug,
                type=prod_type,
                link=link)
            db.session.add(prod)

        if not prod.img and img:
            prod.img = img
            prod.save_product_image_to_s3()

        if not prod.prices.filter_by(date=date).all():
            price_obj = Price(value=value, product=prod, date=date)
            db.session.add(price_obj)

        return prod

    def save_product_image_to_s3(self):
        if any([key == self.slug
                for key in BUCKET_LIST]):
            return

        k = Key(bucket)
        k.key = self.slug
        file_object = urllib2.urlopen(self.img)
        fp = StringIO.StringIO(file_object.read())
        k.set_contents_from_file(fp)


class Price(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.Integer())
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product',
                              backref=db.backref("prices", lazy='dynamic'))
    date = db.Column(db.Date, nullable=False)



