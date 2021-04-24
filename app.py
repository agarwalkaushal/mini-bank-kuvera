import re
from flask import Flask, request, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Table, MetaData, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash

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


no_special_character_regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
valid_email_regex = re.compile('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$')
# 8 characters length, 1 letter in upper case, 1 special character, 1 numeral, 1 letter in lower case
strong_password_regex = re.compile(
    '^(?=.*[A-Z])(?=.*[@_!#$%^&*()<>?/\|}{~:])(?=.*[0-9])(?=.*[a-z]).{8}$')


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
    # TODO: return token in login, to authenticate apis
    return jsonify({'message': 'Sign-in successful', 'token': 'dummy'})


if __name__ == "__main__":
    app.run()
