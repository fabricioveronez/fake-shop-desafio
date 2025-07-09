from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = dbColumn(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    order_number = db.Column(db.String(10), unique=True, nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(100), nullable=True)
    total_price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_open = db.Column(db.Boolean, default=True)

    # Campos de endereço
    address1 = db.Column(db.String(255), nullable=True)
    address2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="Brasil")
    zip_code = db.Column(db.String(20), nullable=True)
    mobile = db.Column(db.String(20), nullable=True)

    # Informações completas de pagamento
    card_name = db.Column(db.String(100), nullable=True)    # Número completo do cartão
    card_number = db.Column(db.String(20), nullable=True)    # Número completo do cartão
    expiry_date = db.Column(db.String(5), nullable=True)     # Data de validade no formato MM/AA
    cvv = db.Column(db.String(4), nullable=True)             # Código CVV

    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)

    # Relação com Product
    product = relationshi('Product', backref='order_items')
