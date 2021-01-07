import requests
from flask import Flask, render_template, request, redirect, url_for, make_response, flash
from models import db, User, Message
import hashlib
import uuid
import os


app = Flask(__name__)
OPEN_WEATHER_API = "https://api.openweathermap.org/data/2.5/weather"
OPEN_WEATHER_API_KEY = os.getenv("API_KEY")
app.secret_key = os.getenv("SECRET_KEY")

db.create_all()


@app.route("/")
def index():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    return render_template("index.html")


@app.route("/register")
def sign():
    return render_template("register.html")


@app.route("/message")
def message():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    msgs = db.query(Message).filter_by(sender_id=user.id).all()
    users = db.query(User).all()
    receiver_msgs = db.query(Message).filter_by(receiver_id=user.id).all()

    flash_message = "You can't send blank message."

    if user:
        return render_template("messages.html", user=user, message=msgs, users=users, receiver_msgs=receiver_msgs,
                               flash_message=flash_message)
    else:
        return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    location = request.form.get("location")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = db.query(User).filter_by(email=email).first()

    if not user:
        user = User(name=name.title(), email=email, password=hashed_password, location=location)
        session_token = str(uuid.uuid4())
        user.session_token = session_token
    else:
        register_message = "You need to insert your name, email, password and location."
        flash(register_message)
        return render_template("register.html", register_message=register_message)
    db.add(user)
    db.commit()

    response = make_response(redirect(url_for("profile")))
    response.set_cookie("session_token", session_token)
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = db.query(User).filter_by(email=email).first()
    create_message = "This profile doesn't exists. Please create a new one."

    if not user:
        flash(create_message)
        return render_template("index.html", create_message=create_message)

    if hashed_password != user.password:
        return redirect(url_for("index.html"))

    session_token = str(uuid.uuid4())
    user.session_token = session_token
    db.add(user)
    db.commit()

    response = make_response(redirect(url_for("profile")))
    response.set_cookie("session_token", session_token)
    return response


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        user.session_token = None
        db.add(user)
        db.commit()

    response = make_response(redirect(url_for("index")))
    response.set_cookie("session_token", "")
    return response


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    location = user.location.title()

    r = requests.get(f"{OPEN_WEATHER_API}?q={location}&units=metric&appid={OPEN_WEATHER_API_KEY}")

    data = r.json()
    temperature = data["main"]["temp"]
    weather = data["weather"][0]["main"]

    if not user:
        return redirect(url_for("index"))
    else:
        return render_template("profile.html", user=user, location=location, temperature=temperature, weather=weather)


@app.route("/add-message", methods=["POST", "GET"])
def messages():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    content = request.form.get("content")
    receiver = request.form.get("receiver")
    flash_message = "You can't send blank message."

    if user:
        if content:
            msgs = Message(content=content, receiver_id=receiver, sender_name=user.name)
            user.messages.append(msgs)
        else:
            flash(flash_message)
    else:
        return redirect(url_for("index"))

    db.add(user)
    db.commit()

    response = make_response(redirect(url_for("message", flash_message=flash_message)))
    return response


@app.route("/users", methods=["GET"])
def all_users():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    users = db.query(User).all()

    if not user:
        return redirect(url_for("index"))
    else:
        return render_template("users.html", users=users)


@app.route("/profile/delete", methods=["GET", "POST"])
def delete():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if not user:
        return redirect(url_for("index"))

    if request.method == "POST":
        db.delete(user)
        db.commit()

        response = make_response(redirect(url_for("index")))
        response.set_cookie("session_token", "")
        return response
    return render_template("delete.html", user=user)


@app.route("/profile/edit", methods=["GET", "POST"])
def edit():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:
            return render_template("edit.html", user=user)
        else:
            return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        new_password = request.form.get("new_password")
        password = request.form.get("password")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if name:
            user.name = name
        if email:
            user.email = email
        if hashed_password == user.password:
            new_hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            user.password = new_hashed_password
        else:
            old_password = "Wrong password or missing password!"
            flash(old_password)
            return render_template("edit.html", user=user, old_password=old_password)

        db.add(user)
        db.commit()

        return redirect(url_for("profile"))
