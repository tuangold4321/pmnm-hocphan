from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    books = db.relationship('Book', backref='category', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    author = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    year = db.Column(db.Integer)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    order_items = db.relationship('OrderItem', backref='book', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text)
    
    # Thêm trường này để lưu phương thức thanh toán
    payment_method = db.Column(db.String(20), nullable=False, default='cod')
    
    shipping_fee = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Chờ xác nhận')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    history = db.relationship('OrderHistory', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)

class OrderHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)