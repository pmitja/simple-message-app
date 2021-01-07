import os
from sqla_wrapper import SQLAlchemy
from sqlalchemy import ForeignKey


db = SQLAlchemy(os.getenv("DB_URL", "sqlite:///message-app.sqlite"))


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    session_token = db.Column(db.String)
    location = db.Column(db.String)
    messages = db.relationship("Message")


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String)
    receiver_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    sender_name = db.Column(db.String)