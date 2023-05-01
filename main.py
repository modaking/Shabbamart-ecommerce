import os
import re
import csv
import random
from tkinter.font import names

import requests
import pdfkit
from requests.auth import HTTPBasicAuth
from datetime import datetime
from datetime import time
from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, make_response
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_principal import Principal

app = Flask(__name__)

CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/Modda/PycharmProjects/Web database/Test21.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://shabamar_ian:h8uP}LVH,FHy@localhost/shabarmar_test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Secret key'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.role_id != 1:
            flash('You are not authorised', 'warning')
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    return decorated_view


def employee_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.role_id != 1 or current_user.role_id != 2:
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    return decorated_view


closing = time(21, 0, 0)
opening = time(8, 0, 0)
now = datetime.now()
now = time(now.hour, now.minute, now.second)

dtx = [i for i in range(opening.hour, closing.hour)]


def opening_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if now.hour not in dtx:
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    return decorated_view


product_tag = db.Table('product_tag',
                       db.Column('product_id', db.Integer, db.ForeignKey('product.product_id')),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tag.tag_id'))
                       )

pinned_product = db.Table('pinned_product',
                          db.Column('product_id', db.Integer, db.ForeignKey('product.product_id')),
                          db.Column('profile_id', db.Integer, db.ForeignKey('profile.profile_id'))
                          )


class User(db.Model, UserMixin):
    username = db.Column('username', db.String(80), unique=True, nullable=False)
    id = db.Column('id', db.Integer, primary_key=True)
    email = db.Column('email', db.String(100), unique=True, nullable=False)
    password = db.Column('password', db.String(150), nullable=False)
    date_added = db.Column('date_added', db.DateTime, default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    active = db.Column('active', db.Boolean, default=True)


class Role(db.Model):
    name = db.Column('name', db.String(25), unique=True, nullable=False)
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    Users = db.relationship('User', backref='users')


class Profile(db.Model):
    username = db.Column('username', db.String(80))
    user_id = db.Column('user_id', db.Integer)
    profile_id = db.Column('profile_id', db.Integer, primary_key=True)
    pinned = db.relationship('Product', secondary=pinned_product, backref='profile')
    # orders_completed = db.relationship('orders_completed', backref='orders_completed')
    cart_id = db.Column('cart_id', db.Integer, unique=True)


class Cart(db.Model):
    customer_name = db.Column('customer_name', db.String(100), nullable=True)
    # second_name = db.Column('second_name', db.String(100))
    # phone_number= db.Column('phone_number', db.String(18))
    customer_id = db.Column('customer_id', db.Integer, nullable=False)
    ordered_products = db.relationship('Cart_products', backref='cart_products')
    id = db.Column('id', db.Integer, primary_key=True)
    # order_code = db.Column('order_code', db.String(), nullable=False)
    total_amount = db.Column('total_amount', db.Integer)
    location = db.Column('delivery_location', db.String(100))
    status = db.Column('delivery_status', db.Boolean)
    order_date = db.Column('order_date', db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.Integer, db.ForeignKey('payment.id'))
    order_complete = db.Column('order_complete', db.Boolean, default=False)
    complete = db.Column('completed', db.Boolean, default=False)
    active = db.Column('active', db.Boolean, default=True)


class Cart_products(db.Model):
    row_id = db.Column('row_id', db.Integer, primary_key=True)
    product_name = db.Column('product_name', db.String(100), nullable=False)
    product_id = db.Column('product_id', db.Integer, nullable=False)
    # position_no = db.Column('position_no', db.Integer, nullable=False default=0)
    quantity = db.Column('quantity', db.Integer(), nullable=False)
    total_price = db.Column('total_price', db.Integer, nullable=False)
    parent_cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    item_price = db.Column('item_price', db.Integer())
    size = db.Column('size', db.String(), default=None)
    color = db.Column('color', db.String(80), default=None)
    # coupons = db.Column('coupons', db.String(), default=None)
    # discount = db.Column('discount', db.Integer, default=0)


class Payment(db.Model):
    name = db.Column('name', db.String(25), unique=True, nullable=False)
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    carts = db.relationship('Cart', backref='carts')


"""

class Orders(db.Model):
    customer_name= db.Column('customer_name', db.String(100), nullable=False)
    customer_id= db.Column('customer_id', db.Integer, nullable=False)
    second_name = db.Column('second_name', db.String(100))
    phone_number= db.Column('phone_number', db.String(18))
    order_code = db.Column('order_code', db.String(), nullable=False)
    ordered_products = db.relationship('Ordered_products', backref='ordered_products')
    order_id = db.Column('order_id', db.Integer, primary_key=True)
    order_code = db.Column('order_code', db.String(), nullable=False)
    total_amount = db.Column('total_amount', db.Integer)
    location = db.Column('delivery_location', db.String(100))
    delivered = db.Column('delivered', db.Boolean default=False)
    order_date = db.Column('order_date',db.DateTime, default=datetime.utcnow)
    payment_method = db.Column('payment_type', db.ForeignKey('payment_type.name'))
    payment_code = db.Column('payment_code', db.String(20))
    profile = db.Column('profile',db.Integer,db.ForeignKey('profile.profile_id'))


class Ordered_products(db.Model):
    row_id = db.Column('row_id', db.Integer, primary_key=True)
    product_name = db.Column('product_name', db.String(100), nullable=False)
    product_id = db.Column('product_id', db.Integer nullable=False)
    position_no = db.Column('position_no', db.Integer, nullable=False default=0)
    quantities = db.Column('quantity', db.Integer(),nullable=False)
    total_price = db.Column('total_price',db.Integer,nullable=False)
    parent_order = db.Column(db.Integer, db.ForeignKey('orders.order_id'))
    item_price = db.Column('item_price', db.Integer())
    size = db.Column('size', db.String(), default=None)
    color = db.Column('color', db.String(80), default=None)
    coupons = db.Column('coupons', db.String(), default=None)
    discount = db.Column('discount', db.Integer, default=0)


class Payment_Confirm(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    code = db.Column('code', db.String(), nullable=False unique=True)
    customer_id= db.Column('customer_id', db.Integer, nullable=False)
    pay_date = db.Column('pay_date',db.DateTime, default=datetime.utcnow)
    parent_cart = db.Column('cart_id', db.String(), nullable=False)
    parent_order= db.Column('order_id', db.String(), nullable=False)
    order_code = db.Column('order_code', db.String())
    paid_amount = db.Column('paid_amount', db.Integer)
    order_amount = db.Column('order_amount', db.Integer,nullable=False)
    active = db.Column('active', db.Boolean, default=True)


class Sales(db.Model):
    prod_name = db.Column('product_name', db.String(100), nullable=False)
    purchases_quantity = db.Column('purchases_quantity', db.Integer, default=0)
    returns_quantity = db.Column('returns_quantity', db.Integer, default=0)
    revenue = db.Column('revenue', db.Integer, default=0)
    category_id = db.Column('category_id', db.Integer, primary_key=True)


"""


class Product(db.Model):
    product_id = db.Column('product_id', db.Integer, primary_key=True)
    file_path = db.Column('file_path', db.String(), nullable=False)
    product_name = db.Column('product_name', db.String(80), nullable=False)
    product_variations = db.relationship('Variation', backref='product')
    product_category = db.Column('product_category', db.String(50), nullable=False)
    product_description = db.Column('product_description', db.Text, nullable=False)
    product_price = db.Column('price', db.Integer, nullable=False)
    product_tags = db.relationship('Tag', secondary=product_tag, backref='product')
    date_added = db.Column('date_added', db.DateTime, default=datetime.utcnow)
    in_stock = db.Column('in_stock', db.Boolean, default=True, nullable=False)
    # deal_id = db.Column(db.Integer, db.ForeignKey('deals.deal_id'))
    # size = db.Column('size', db.String(), default=None)
    # color = db.Column('color', db.String(80), default=None)
    # limit = db.Column('limit', db.Integer, default=None)
    # active = db.Column('active', db.Boolean, default=True)


class Variation(db.Model):
    id = db.Column('var_id', db.Integer, primary_key=True)
    # position = db.Column('position', db.Integer)
    file_path = db.Column('file_path', db.String())
    parent_product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    variation_name = db.Column('var_name', db.String(), nullable=False)
    price = db.Column('price', db.Integer())
    color = db.Column('color', db.String(50))
    # in_stock = db.Column('in_stock', db.Boolean, default=True, nullable=False)
    # active = db.Column('active', db.Boolean, default=True)


class Tag(db.Model):
    id = db.Column('tag_id', db.Integer, primary_key=True)
    tag = db.Column('tag', db.String(25), nullable=False, unique=True)


"""

class Deals(db.Model):
    id = db.Column('deal_id', db.Integer, primary_key=True)
    category_name = db.Column('category_name', db.String)
    deal_products = db.relationship('Deal_products', backref='deals')
    active = db.Column('active', db.Boolean, default=False)
    position = db.Column('position', db.Integer)
    discount = db.Column('discount',db.Integer)

class Categories(db.Model):
    id = db.Column('deal_id', db.Integer, primary_key=True)
    category_name = db.Column('category_name', db.String)
    position = db.Column('position', db.Integer)
    active = db.Column('active', db.Boolean, default=False)    

"""


class Employee(db.Model):
    employee_name = db.Column('employee_name', db.String(100))
    employee_id = db.Column('employee_id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer())
    employee_email = db.Column('employee_email', db.String(100))
    department_name = db.Column('department', db.ForeignKey('department.name'))
    active = db.Column('active', db.Boolean(), default=True)
    date_added = db.Column('date_added', db.DateTime, default=datetime.utcnow)


class Department(db.Model):
    name = db.Column('name', db.String(25), unique=True, nullable=False)
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    employees = db.relationship('Employee', backref='employee')


"""
a = Role(name='Admin')
b = Role(name='Employee')
c = Role(name='User')

db.session.add_all([a, b, c])

email1 = 'ModaKing@gmail.com'
email3 = 'Aphrodite@gmail.com'
email2 = 'Ian9toz@gmail.com'

password_1 = 'Bongcloud'
password_2 = 'Fianchetto'
password_3 = 'Estoy_loco'

user_1 = User(username='Moda', email=email1, password=generate_password_hash(password_1, method='sha256'), role_id=1)
user_2 = User(username='Iantoz', email=email2, password=generate_password_hash(password_2, method='sha256'), role_id=1)
user_3 = User(username='Tory', email=email3, password=generate_password_hash(password_3, method='sha256'), role_id=1)

email4 = 'Crossbones@gmail.com'
email5 = 'Biggiesmalls@gmail.com'
email6 = 'Dawn@gmail.com'
email7 = 'Tupac_Shakur@gmail.com'

password_4 = 'Valor_Morghulis'
password_5 = 'Juicy'
password_6 = 'Amore'
password_7 = 'Westcoast'

user_4 = User(username='Cross', email=email4, password=generate_password_hash(password_4, method='sha256'), role_id=2)
user_5 = User(username='BIG', email=email5, password=generate_password_hash(password_5, method='sha256'), role_id=2)
user_6 = User(username='Dawn', email=email6, password=generate_password_hash(password_6, method='sha256'), role_id=2)
user_7 = User(username='Tupac', email=email7, password=generate_password_hash(password_7, method='sha256'), role_id=2)

db.session.add_all([user_1, user_2, user_3, user_4, user_5, user_6, user_7])

usid1 = User.query.filter_by(email=email1).first()
usid2 = User.query.filter_by(email=email2).first()
usid3 = User.query.filter_by(email=email3).first()
usid4 = User.query.filter_by(email=email4).first()
usid5 = User.query.filter_by(email=email5).first()
usid6 = User.query.filter_by(email=email6).first()
usid7 = User.query.filter_by(email=email7).first()

prof_1 = Profile(username='Moda', user_id=usid1.id)
prof_2 = Profile(username='Iantoz', user_id=usid2.id)
prof_3 = Profile(username='Tory', user_id=usid3.id)
prof_4 = Profile(username='Cross', user_id=usid4.id)
prof_5 = Profile(username='BIG', user_id=usid5.id)
prof_6 = Profile(username='Dawn', user_id=usid6.id)
prof_7 = Profile(username='Tupac', user_id=usid7.id)

db.session.add_all([prof_1, prof_2, prof_3, prof_4, prof_5, prof_6, prof_7])
db.session.commit()
"""
"""
x = User.query.filter_by(role_id=1).all()

for i in x:
    print(str(i.date_added))
    # db.session.delete(i)
    # db.session.commit()

x = Role.query.all()
for i in x:
    print("\n\n" + i.name, "|" + str(i.Users) + "\n")
    for e in i.Users:
        print(e.email, " | " + str(e.id), " | " + e.username, " | " + str(e.date_added), " | " + e.password)

print('Users finished' + "\n\n")
"""

"""
dep_1 = Department(name="Delivery")
dep_2 = Department(name="Marketing")
dep_3 = Department(name="Accounting")
dep_4 = Department(name="Clerk")
dep_5 = Department(name="Supervisor")
dep_6 = Department(name="Management")

db.session.add_all([dep_1, dep_2, dep_3, dep_4, dep_5, dep_6])

y = User.query.filter_by(role_id=2).all()
for i in y:
    employee = Employee(employee_name=i.username, user_id=i.id, department_name="Delivery", employee_email=i.email)
    db.session.add_all([employee])

db.session.commit()
"""

"""
good = Employee.query.all()
print("Employee names and department:")
for vb in good:
    print(vb.employee_name + " -> " + vb.department_name)

"""
"""
lod = Product.query.all()
for lid in lod:
    n = Product.query.filter_by(product_id=lid.product_id).first()
    db.session.delete(n)
db.session.commit()
"""
"""
pro = Profile.query.all()
for p in pro:
    print(p.username + "|" + str(p.user_id))

cb = Cart.query.all()
for c in cb:

    n = []
    for ab in c.ordered_products:
        n.append(ab.product_name)
    print(c.customer_name + "|", n)
"""


# Order coding system

def mixer(v):
    n = len(v)
    p = []
    if n == 1:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, "0")
        p.insert(3, "X")
        p.insert(4, "0")
        p.insert(5, "Z")
        p.insert(6, "0")
        p.insert(7, "B")
        p.insert(8, "0")
        p.insert(9, "0")
        p.insert(10, "A")
        p.reverse()
        return p
    elif n == 2:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, v[1])
        p.insert(3, "X")
        p.insert(4, "0")
        p.insert(5, "Z")
        p.insert(6, "0")
        p.insert(7, "C")
        p.insert(8, "0")
        p.insert(9, "0")
        p.insert(10, "H")
        p.reverse()
        return p
    elif n == 3:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, v[1])
        p.insert(3, "X")
        p.insert(4, v[2])
        p.insert(5, "Z")
        p.insert(6, "0")
        p.insert(7, "F")
        p.insert(8, "0")
        p.insert(9, "0")
        p.insert(10, "Q")
        p.reverse()
        return p
    elif n == 4:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, v[1])
        p.insert(3, "X")
        p.insert(4, v[2])
        p.insert(5, "Z")
        p.insert(6, v[3])
        p.insert(7, "C")
        p.insert(8, "0")
        p.insert(9, "0")
        p.insert(10, "W")
        p.reverse()
        return p
    elif n == 5:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, v[1])
        p.insert(3, "X")
        p.insert(4, v[2])
        p.insert(5, "Z")
        p.insert(6, v[3])
        p.insert(7, "N")
        p.insert(8, v[4])
        p.insert(9, "0")
        p.insert(10, "Y")
        p.reverse()
        return p
    elif n == 6:
        p.insert(0, "X")
        p.insert(1, v[0])
        p.insert(2, v[1])
        p.insert(3, "X")
        p.insert(4, v[2])
        p.insert(5, "Z")
        p.insert(6, v[3])
        p.insert(7, "C")
        p.insert(8, v[4])
        p.insert(9, v[5])
        p.insert(10, "Z")
        p.reverse()
        return p
    else:
        return None


def convert(x):
    lock = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "A": 10,
        "B": 11,
        "C": 12,
        "D": 13,
        "E": 14,
        "F": 15,
        "G": 16,
        "H": 17,
        "I": 18,
        "J": 19,
        "K": 20,
        "L": 21,
        "M": 22,
        "N": 23,
        "O": 24,
        "P": 25,
        "Q": 26,
        "R": 27,
        "S": 28,
        "T": 29,
        "U": 30,
        "V": 31,
    }

    y = 0
    a = int(x)
    lap = []
    while a != 0:
        m = a / 32
        n = int(m)
        # n = float(n)
        p = m - n
        z = p * 32
        z = int(z)
        for key in lock:
            if lock[key] == z:
                lap.append(key)
        a = n
        y += 1
    lap = mixer(lap)

    return lap


c = convert(1000000052)
print(c)


@app.route('/')
@login_required
def index():
    cat_1 = "Foods and drinks"
    cat_6 = "Electronics and accessories"
    cat_3 = "Skincare and cosmetics"
    cat_7 = "Clothes and accessories"
    cat_8 = "Shoes"
    cat_2 = "Soaps and detergents"
    cat_4 = "Toiletries"
    cat_5 = "Books and stationery"

    col_1 = []
    col_2 = []
    col_3 = []
    col_4 = []
    col_5 = []
    col_6 = []
    col_7 = []
    col_8 = []

    photos = Product.query.all()
    prods = []

    for photo in photos:
        if photo.product_category == cat_1:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_1.append(detail)

        elif photo.product_category == cat_2:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_2.append(detail)

        elif photo.product_category == cat_3:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_3.append(detail)

        elif photo.product_category == cat_4:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_4.append(detail)

        elif photo.product_category == cat_5:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_5.append(detail)

        elif photo.product_category == cat_6:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_6.append(detail)

        elif photo.product_category == cat_7 and photo.product_name != "B***h":
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Products/Product_variations/" + fid.file_path[35:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_7.append(detail)

        elif photo.product_category == cat_8:
            many = photo.product_variations
            most = []
            for fid in many:
                rav = {
                    "var_name": fid.variation_name,
                    "var_path": "Product_variations/" + fid.file_path[26:],
                    "var_id": fid.id
                }
                most.append(rav)

            jump = []
            for tag in photo.product_tags:
                jump.append(tag.tag)
            detail = {
                "path": "Products/" + photo.file_path[16:],
                "name": photo.product_name,
                "id": photo.product_id,
                "price": photo.product_price,
                "category": photo.product_category,
                "description": photo.product_description,
                "tags": jump,
                "variations": most
            }
            col_8.append(detail)
    random.shuffle(col_1)
    col_1.append(cat_1)
    prods.append(col_1)
    random.shuffle(col_2)
    col_2.append(cat_2)
    prods.append(col_2)
    random.shuffle(col_3)
    col_3.append(cat_3)
    prods.append(col_3)
    random.shuffle(col_4)
    col_4.append(cat_4)
    prods.append(col_4)
    random.shuffle(col_5)
    col_5.append(cat_5)
    prods.append(col_5)
    random.shuffle(col_6)
    col_6.append(cat_6)
    prods.append(col_6)
    random.shuffle(col_7)
    col_7.append(cat_7)
    prods.append(col_7)
    random.shuffle(col_8)
    col_8.append(cat_8)
    prods.append(col_8)

    return render_template("index.html", images=prods)


@app.route('/description/<number>')
@login_required
def description(number):
    prod = Product.query.filter_by(product_id=number).first()
    info = []
    many = prod.product_variations
    most = []
    for fid in many:
        rav = {
            "var_name": fid.variation_name,
            "var_path": "Product_variations/" + fid.file_path[26:],
            "var_id": fid.id
        }
        most.append(rav)
    detail = {
        "path": "Products/" + prod.file_path[16:],
        "name": prod.product_name,
        "id": prod.product_id,
        "description": prod.product_description,
        "price": prod.product_price,
        "category": prod.product_category,
        "variations": most
    }
    info.append(detail)
    return render_template("description.html", info=info)


@app.route('/deals')
@login_required
def deals():
    return render_template("deals.html")


@app.route('/view_more/<uni>')
@login_required
def view_more(uni):
    cat = uni
    return render_template("viewer.html", category=cat)


@app.route('/add_cart/<digit>', methods=['GET', 'POST'])
@login_required
def add_cart(digit):
    pont = Product.query.filter_by(product_id=digit).first()
    b = int(current_user.id)
    uba = Profile.query.filter_by(user_id=b).first()

    if uba.cart_id is None:
        name = current_user.username
        cuid = b
        cart = Cart(customer_name=name, customer_id=cuid, active=True, total_amount=0)
        db.session.add(cart)

        cart = Cart.query.filter_by(customer_id=cuid, active=True).first()

        uba.cart_id = cart.id

        pname = pont.product_name
        pid = pont.product_id
        quantity = 1
        total_price = quantity * pont.product_price
        cg = Cart_products(product_name=pname, product_id=pid, quantity=quantity, item_price=pont.product_price,
                           total_price=total_price, parent_cart_id=cart.id)
        db.session.add(cg)
        cart.total_amount += total_price
        db.session.commit()
        # flash("Product added to cart")
        return jsonify({"digit": cart.id})
    elif uba.cart_id:
        pname = pont.product_name
        pid = pont.product_id
        quantity = 1
        total_price = quantity * pont.product_price
        cab = Cart.query.filter_by(id=uba.cart_id).first()
        cab = [i.product_id for i in cab.ordered_products]

        if pid in cab:
            return jsonify({"digit": [{"no": 1}, {"no": 2}, {"no": 3}]})
        else:
            cart = Cart.query.filter_by(id=uba.cart_id).first()
            cg = Cart_products(product_name=pname, product_id=pid, quantity=quantity, total_price=total_price,
                               item_price=pont.product_price, parent_cart_id=uba.cart_id)
            db.session.add(cg)
            cart.total_amount += total_price
            db.session.commit()
            return jsonify({"digit": uba.cart_id})

    return jsonify({"digit": "Added to cart"})


@app.route('/view_cart', methods=['GET', 'POST'])
def view_cart():
    prof = Profile.query.filter_by(user_id=current_user.id).first()
    cid = prof.cart_id
    arr = []

    if cid is None:
        return jsonify({"digit": [], "total_amount": 0})
    else:

        cirt = Cart.query.filter_by(id=cid).first()
        cort = cirt.ordered_products
        if len(cort) > 0:
            for cr in cort:
                item = Product.query.filter_by(product_id=cr.product_id).first()
                details = {
                    "path": "/static/Products/" + item.file_path[16:],
                    "name": cr.product_name,
                    "id": cr.row_id,
                    "description": item.product_description,
                    "price": item.product_price,
                    "quantity": cr.quantity,
                    "total_cost": cr.total_price

                }
                arr.append(details)

            return jsonify({"digit": arr, "total_amount": cirt.total_amount})
        else:
            return jsonify({"digit": [], "total_amount": cirt.total_amount})


@app.route('/del_cart/<number>')
@login_required
def del_cart(number):
    cart = Cart_products.query.filter_by(row_id=number).first()
    tot = cart.total_price
    db.session.delete(cart)
    vn = Profile.query.filter_by(user_id=current_user.id).first()

    cart = Cart.query.filter_by(id=vn.cart_id).first()
    cart.total_amount -= int(tot)
    db.session.commit()
    return jsonify({"result": number, "total_amount": cart.total_amount})


@app.route('/cart_quantity/<unique>/<quant>')
@login_required
def cart_quantity(unique, quant):
    item = Cart_products.query.filter_by(row_id=unique).first()
    item.quantity = quant
    item.total_price = int(quant) * item.item_price
    vn = Profile.query.filter_by(user_id=current_user.id).first()
    cart = Cart.query.filter_by(id=item.parent_cart_id).first()
    cort = cart.ordered_products
    st = 0
    for cr in cort:
        st += cr.total_price

    cart.total_amount = st
    db.session.commit()
    details = {
        "total": item.total_price,
        "total_amount": st

    }

    return jsonify({"result": item.total_price, "total_amount": st})


@app.route('/add_pin/<pin>')
def add_pin(pin):
    pdp = Product.query.filter_by(product_id=pin).first()
    usp = Profile.query.filter_by(user_id=current_user.id).first()
    if pdp and usp:
        if pdp in usp.pinned:
            return None

        else:
            usp.pinned.append(pdp)
            db.session.commit()
    else:
        print("Error in pinning")
    return jsonify({"digit": []})


@app.route('/view_pin')
@login_required
def view_pin():
    adp = []
    pp = Profile.query.filter_by(user_id=current_user.id).first()

    for i in pp.pinned:
        details = {

            "path": "/static/Products/" + i.file_path[16:],
            "name": i.product_name,
            "id": "p" + str(i.product_id),
            "price": i.product_price,
            "category": i.product_category,
            "description": i.product_description

        }
        adp.append(details)
    adp.reverse()
    return jsonify({"digit": adp})


@app.route('/del_pin/<pin>')
@login_required
def del_pin(pin):
    pdp = Product.query.filter_by(product_id=pin).first()
    usp = Profile.query.filter_by(user_id=current_user.id).first()
    if pdp and usp:
        if pdp in usp.pinned:
            usp.pinned.remove(pdp)
            db.session.commit()

        else:
            return None
    else:
        print("Error in pinning")
    return jsonify({"digit": []})


@app.route('/view_profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    prof = Profile.query.filter_by(user_id=current_user.id).first()

    return jsonify({"digit": prof.username})


@app.route('/details', methods=['GET', 'POST'])
@login_required
def details():
    return render_template("details.html")


@app.route('/delivery_details', methods=['GET', 'POST'])
@login_required
def delivery_details():
    if request.method == 'POST':
        name = request.form.get("first_name")
        address = request.form.get("address")
        payment = "M-pesa"

        vn = Profile.query.filter_by(user_id=current_user.id).first()

        cart = Cart.query.filter_by(id=vn.cart_id).first()

        if name and address:
            cart.location = address
            cart.customer_name = name
            cart.payment_method = payment

            db.session.commit()
            return redirect(url_for('confirm'))
        else:
            return redirect(url_for('details'))

    return render_template('details.html')


@app.route('/confirm')
@login_required
def confirm():
    vn = Profile.query.filter_by(user_id=current_user.id).first()

    part = Cart_products.query.filter_by(parent_cart_id=vn.cart_id).all()
    cart = Cart.query.filter_by(id=vn.cart_id).first()
    grand = cart.total_amount
    odp = []
    for od in part:
        dits = {
            "product": od.product_name,
            "price": od.item_price,
            "quantity": od.quantity,
            "total": od.total_price
        }
        odp.append(dits)
    return render_template("confirm.html", part=odp, grand=grand)


@app.route('/invoice')
@login_required
def invoice():
    vn = Profile.query.filter_by(user_id=current_user.id).first()

    part = Cart_products.query.filter_by(parent_cart_id=vn.cart_id).all()
    cart = Cart.query.filter_by(id=vn.cart_id).first()
    grand = cart.total_amount
    odp = []
    for od in part:
        dits = {
            "product": od.product_name,
            "price": od.item_price,
            "quantity": od.quantity,
            "total": od.total_price
        }
        odp.append(dits)
    return render_template("invoice.html", part=odp, grand=grand)


@app.route('/submit_payment', methods=['GET', 'POST'])
@login_required
def submit_payment():
    payment = request.form.get("payment")
    patt = '[^A-Z0-9]'
    if not payment:
        return redirect(url_for('invoice'))
    elif len(payment) != 10:
        return redirect(url_for('invoice'))
    elif re.search(patt, payment):
        return redirect(url_for('invoice'))
    else:
        """

        test_code = Payment_Confirm.query.filter_by(code=payment).first()
        if test_code:
            return redirect(url_for('invoice'))
        else:    
            vn = Profile.query.filter_by(user_id=current_user.id).first()

            cart = Cart.query.filter_by(id=vn.cart_id).first()
            new_payment = Payment_Confirm(code=payment, customer_id=current_user.id, order_amount=cart.total_amount,
            cart_id=cart.id)

            db.session.add(new_payment)
            db.session.commit()

        """
        return redirect(url_for('success'))
    return render_template("success.html")


@app.route('/success')
@login_required
def success():
    return render_template("success.html")


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get("Username")
        email = request.form.get("Email")
        password = request.form.get("password")
        confirm_password = request.form.get("Confirm_password")

        pattern = '[a-z A-Z 0-9]+@[a-zA-Z]+\.(com|edu|net)$'

        if not username:
            flash('Please enter Username')
            return redirect(url_for('sign_up'))
        elif not email:
            flash(" Please enter Email")
            return redirect(url_for('sign_up'))
        elif not password:
            flash('Please enter Password')
            return redirect(url_for('sign_up'))
        elif not confirm_password:
            flash('Please enter Password confirmation')
            return redirect(url_for('sign_up'))
        elif password != confirm_password:
            flash("Password does not match password confirmation")
            return redirect(url_for('sign_up'))
        elif len(password) <= 7:
            flash('Password is too short.At least 8 characters required')
            return redirect(url_for('sign_up'))
        elif len(email) <= 4:
            flash('Email is too short')
            return redirect(url_for('sign_up'))
        elif not (re.search(pattern, email)):
            flash('Invalid email')
            return redirect(url_for('sign_up'))
        else:
            username_exists = User.query.filter_by(username=username).first()

            email_exists = User.query.filter_by(email=email).first()

            if username_exists:
                flash('Username already exists')
                return redirect(url_for('sign_up'))

            elif email_exists:
                flash('Email already has an account. Please login to account')
                return redirect(url_for('login'))

            else:
                new_user = User(email=email, username=username,
                                password=generate_password_hash(password, method='sha256'),
                                role_id=3)

                db.session.add(new_user)
                usid1 = User.query.filter_by(email=email).first()
                prof_7 = Profile(username=usid1.username, user_id=usid1.id)
                db.session.add(prof_7)
                db.session.commit()
                login_user(new_user, remember=True)
                y = User.query.all()
                for i in y:
                    if i.email:
                        print(i.id, ' | ' + i.username, ' | ' + i.email, ' | ' + i.password, '|' + str(i.role_id))

                flash('Welcome ' + username)
                return redirect(url_for('index'))

    return render_template("signup.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("Username")
        password = request.form.get("password")
        if not username:
            flash('Please enter a username')
            return redirect(url_for('login'))
        elif not password:
            flash('Please enter Password')
            return redirect(url_for('login'))
        else:
            y = User.query.filter_by(username=username).first()
            if y:
                if check_password_hash(y.password, password):
                    login_user(y, remember=True)

                    if current_user.role_id == 1:
                        flash('Welcome Admin ' + username)
                        return redirect(url_for('index'))
                    elif current_user.role_id == 2:
                        flash('Welcome Employee ' + username)
                        return redirect(url_for('index'))
                    else:
                        flash('Welcome ' + username)
                        return redirect(url_for('index'))
                else:
                    flash('Please enter correct password')
                    return redirect(url_for('login'))
            else:
                flash('Please enter a valid username')
                return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    products = []
    workers = []
    fans = []

    pt = Product.query.order_by(Product.product_price.desc()).limit(10).all()
    ft = Product.query.all()

    for ea in pt:
        xo = random.randint(1, 100)
        dtsf = '%d %b %Y, %H:%M:%S'
        details = {
            "photo": "Products/" + ea.file_path[16:],
            "name": ea.product_name,
            "id": ea.product_id,
            "price": ea.product_price,
            "date": datetime.strftime(ea.date_added, dtsf)
            ,
            "in_stock": ea.in_stock,
            "orders": xo

        }
        products.append(details)

    et = Employee.query.all()
    for eb in et:
        details = {
            "name": eb.employee_name,
            "id": eb.employee_id,
            "department": eb.department_name,
            "active": eb.active
        }
        workers.append(details)

    ut = User.query.all()
    for ec in ut:
        xo = random.randint(1, 100)
        details = {
            "name": ec.username,
            "id": ec.id,
            "orders": xo,
            "active": ec.active
        }
        fans.append(details)
    xp = len(ft)
    xw = len(workers)
    xf = len(fans)
    return render_template("admin.html", products=products, workers=workers, fans=fans, xp=xp, xw=xw, xf=xf)


@app.route('/admin_employees', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_employees():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("Email")
        department = request.form.get("Department")

        pattern = '[a-z A-Z 0-9]+@[a-zA-Z]+\.(com|edu|net)$'

        if not name:
            flash("Please enter Employee's Username")
            return redirect(url_for('admin_employees'))
        elif not email:
            flash(" Please enter Employee's Email")
            return redirect(url_for('admin_employees'))

        elif not department:
            flash('Please choose department')
            return redirect(url_for('admin_employees'))

        elif len(email) <= 4:
            flash('Email is too short')
            return redirect(url_for('admin_employees'))
        elif not (re.search(pattern, email)):
            flash('Invalid email')
            return redirect(url_for('admin_employees'))
        else:

            email_exists = User.query.filter_by(email=email).first()
            employee_exists = Employee.query.filter_by(employee_name=name).first()

            if email_exists:
                a = email_exists.id
                b = email_exists.username

                if not employee_exists and name == b:
                    new_employee = Employee(employee_name=name, user_id=a, department_name=department,
                                            employee_email=email)

                    db.session.add(new_employee)
                    email_exists.role_id = int(2)

                    db.session.commit()
                    flash('Employee ' + name + ' added')
                    return redirect(url_for('admin_employees'))
                else:
                    flash("Employee already exists")
                    return redirect(url_for('admin_employees'))
            else:
                flash("Email does not exist.Please enter correct email")
                return redirect(url_for('admin_employees'))

    return render_template("admin_employees.html")


@app.route('/admin_noticeboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_noticeboard():
    return render_template("admin_noticeboard.html")


app.config['UPLOAD_PATH'] = 'static\Products'
app.config['VAR_PATH'] = 'static\Product_variations'


@app.route('/admin_product', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_product():
    if request.method == 'POST':
        product = request.files["Product"]
        variations = request.files.getlist("Variations[]")
        variation_names = request.form.get("Variation_names")
        name = request.form.get("Name")
        category = request.form.get("Category")
        price = request.form.get("Price")
        tags = request.form.get("Tags_out")
        desc = request.form.get("description")
        z = ""
        txt = []
        if tags:
            for p in tags:
                if p != ",":
                    z += p

                elif p == ",":
                    txt.append(z)
                    n = len(z) + 1
                    tags = tags[n:]
                    z = ""
        m = ""
        var_names = []
        if variation_names:

            for each in variation_names:
                if each != ",":
                    m += each

                elif each == ",":
                    var_names.append(m)
                    b = len(m) + 1
                    variation_names = variation_names[b:]
                    m = ""
        u = len(variations)
        t = len(var_names)
        var_names.reverse()
        if not product:
            flash('Please add a product file')
            return redirect(request.referrer)
        elif not name:
            flash("Please enter Product's name")
            return redirect(url_for('admin_product'))
        elif not category:
            flash("Please enter Product's category")
            return redirect(url_for('admin_product'))

        elif not price:
            flash(" Please enter Product's price")
            return redirect(url_for('admin_product'))
        elif not desc:
            flash("Please enter Product's description")
            return redirect(url_for('admin_product'))
        elif u != t:
            flash("Variations and variation names numbers must match")
            return redirect(url_for('admin_product'))
        else:
            prod_name = secure_filename(product.filename)
            product.save(os.path.join(app.config['UPLOAD_PATH'], prod_name))
            prod_path = os.path.join(app.config['UPLOAD_PATH'], prod_name)

            new_product = Product(file_path=prod_path, product_name=name, product_category=category,
                                  product_price=price,
                                  product_description=desc)
            db.session.add(new_product)

            for a in txt:
                d = Tag.query.filter_by(tag=a).first()
                if d:
                    new_product.product_tags.append(d)

                else:
                    new_tag = Tag(tag=a)

                    db.session.add_all([new_tag])

                    new_product.product_tags.append(new_tag)

            z = Product.query.filter_by(file_path=prod_path).first()

            a = 0

            ol = len(variations)

            if variations:
                for file in variations:
                    ind = variations.index(file)

                    for nm in var_names:
                        if a < ol and variations.index(file) == var_names.index(nm):
                            filename = secure_filename(file.filename)
                            filepath = os.path.join(app.config['VAR_PATH'], filename)

                            new_var = Variation(file_path=filepath, parent_product_id=z.product_id, variation_name=nm)
                            db.session.add_all([new_var])

                            file.save(filepath)
                    a += 1
            db.session.commit()
            flash("Product added")
            return redirect(url_for('admin'))
    return render_template("admin_product.html")


@app.route('/admin_users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    return render_template("admin_users.html")


@app.route('/admin_data', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_data():
    return render_template("admin_users.html")


consumer_key = "RG5bsJNUHL2jAqyR0dd3jWi6aIK0O7Mg"
consumer_secret = "t2CzF7qr7DvSP533"


@app.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    endpoint = ""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % ac_token()
    }


def ac_token():
    token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    response = (requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))).json()
    return response['access_token']


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Logged out Successfully')
    return redirect(url_for('login'))


db.create_all()

if __name__ == '__main__':
    app.run(debug=False)

