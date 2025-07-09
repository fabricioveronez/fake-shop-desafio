from sqlalchemy import Column, Integer, String, Float
from models.base import db

class Product(db.Model):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))
    short_description = Column(String(200))
    image = Column((255))

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
