from flask import Flask, request, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from constants import no_special_character_regex, valid_email_regex, strong_password_regex
from utils import decode_auth_token, encode_auth_token

app = Flask(__name__)
app.config.from_object(Config)

DB_URI = app.config['SQLALCHEMY_DATABASE_URI']

engine = create_engine(DB_URI)
metadata = MetaData(engine)
Session = sessionmaker()
Base = declarative_base()
Session.configure(bind=engine)
session = Session()


@app.route("/foo")
def hello():
    return "bar"


@app.route('/register', methods=["POST"])
def register():
    username_input = request.args.get('username')
    email_input = request.args.get('email')
    users = Table('users', Base.metadata, autoload=True, autoload_with=engine)

    exists = session.query(users).filter(
        or_(users.columns.username == username_input, users.columns.email == email_input)).first() is not None

    if exists:
        return jsonify({'message': 'User already registered'})

    password_input = request.args.get('password')

    if no_special_character_regex.search(username_input) != None:
        return jsonify({'message': 'Username cannot contain special characters'})

    if valid_email_regex.search(email_input) == None:
        return jsonify({'message': 'Enter valid email'})

    if strong_password_regex.search(password_input) == None:
        return jsonify({'message': 'Enter a strong password'})

    password_hash = generate_password_hash(password_input)
    users = Table('users', metadata, autoload=True)
    engine.execute(users.insert(), username=username_input,
                   email=email_input, password=password_hash)
    return jsonify({'message': 'Registered successfully'})


@app.route('/sign_in', methods=["GET", "POST"])
def sign_in():
    username_input = request.args.get('username')
    password_input = request.args.get('password')
    users = Table('users', Base.metadata, autoload=True, autoload_with=engine)

    user = session.query(users).filter_by(
        username=username_input).first()

    if user is not None and password_input and check_password_hash(user.password, password_input):
        auth_token = encode_auth_token(user.id)
        return jsonify({'signed_in': True, 'user_id': user.id, 'username': user.username, 'email': user.email, 'auth_token': auth_token})

    return jsonify({'signed_in': False})


if __name__ == "__main__":
    app.run()
