from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    emergency1 = db.Column(db.String(10), nullable=False)
    emergency2 = db.Column(db.String(10), nullable=False)
    emergency3 = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(100), nullable=False)
