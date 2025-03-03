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

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref=db.backref('alerts', lazy=True))