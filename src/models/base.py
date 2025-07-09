from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

teste = "Variável"

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)