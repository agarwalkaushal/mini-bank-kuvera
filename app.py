import os
import config
from config import Config
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from constants import no_special_character_regex, valid_email_regex, strong_password_regex
from utils import decode_auth_token, encode_auth_token
import datetime
from fpdf import FPDF
from flask_mail import Mail, Message

# Initialize app
app = Flask(__name__)
mail = Mail(app)

# configuration of mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'samvans91@gmail.com'
app.config['MAIL_PASSWORD'] = '****'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Setup environment
env_config = os.getenv("APP_SETTINGS")
app.config.from_object(env_config)

# Fetch database uri
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']

engine = create_engine(DB_URI)
metadata = MetaData(engine)
Session = sessionmaker()
Base = declarative_base()
Session.configure(bind=engine)
session = Session()


@app.route("/")
@app.route("/index")
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


@app.route('/transaction/transact', methods=["POST"])
def new_transaction():
    auth_token = request.headers['authtoken']
    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    request_data = request.get_json()
    transactions = Table('transactions', Base.metadata,
                         autoload=True, autoload_with=engine)

    last_transaction = session.query(transactions).filter_by(
        u_id=user_id).order_by(transactions.columns.id.desc()).first()

    amount = request_data['amount']
    if last_transaction == None:
        data = engine.execute(transactions.insert(), u_id=user_id, date_time=str(datetime.datetime.utcnow()),
                              balance=amount, amount=amount)
    else:
        balance = last_transaction.balance + amount
        data = engine.execute(transactions.insert(), u_id=user_id, date_time=str(datetime.datetime.utcnow()),
                              balance=balance, amount=amount)
    return jsonify({'message': 'Transaction successful', 'transaction_id': data.inserted_primary_key[0]})


@app.route('/transaction/balance', methods=["GET"])
def fetch_balance():
    auth_token = request.headers['authtoken']
    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    request_data = request.get_json()
    transactions = Table('transactions', Base.metadata,
                         autoload=True, autoload_with=engine)

    last_transaction = session.query(transactions).filter_by(
        u_id=user_id).order_by(transactions.columns.id.desc()).first()

    if last_transaction != None:
        return jsonify({'balance': last_transaction.balance})

    return jsonify({'balance': 0})


@app.route('/transaction/history', methods=["GET"])
def transaction_history():
    auth_token = request.headers['authtoken']
    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    request_data = request.get_json()
    transactions = Table('transactions', Base.metadata,
                         autoload=True, autoload_with=engine)

    transactions_data = session.query(
        transactions).filter_by(u_id=user_id).all()

    if transactions_data == None:
        return jsonify({'message': 'No records found'})

    return jsonify({'history': transactions_data})


@app.route('/transaction/statement', methods=["GET"])
def transaction_statement():
    auth_token = request.headers['authtoken']
    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    request_data = request.get_json()
    transactions = Table('transactions', Base.metadata,
                         autoload=True, autoload_with=engine)

    transactions_data = session.query(transactions).filter_by(
        u_id=user_id).order_by(transactions.columns.id.desc()).all()

    if len(transactions_data) == 0:
        return jsonify({'message': 'No records found'})

    users = Table('users', Base.metadata, autoload=True, autoload_with=engine)
    user = session.query(users).filter_by(id=user_id).first()

    date = str(datetime.datetime.utcnow())
    balance = str(transactions_data[0].balance)
    email = user.email

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    pdf.cell(200, 10, txt="Kuvera Bank", ln=1, align='C')
    pdf.cell(200, 10, txt="Date: " + date, ln=2)
    pdf.cell(200, 10, txt="Email: " + email, ln=3)
    pdf.cell(200, 10, txt="Balance: " + balance, ln=4)
    pdf.cell(200, 10, txt="S/N      " +
             "TXN ID          " + "Amount                                    " + "Date", ln=5)

    for i in range(0, len(transactions_data)):
        ybefore = pdf.get_y()
        column_spacing = 5
        pdf.multi_cell(20, 10, str(i+1))
        pdf.set_xy(20 + column_spacing + pdf.l_margin, ybefore)
        pdf.multi_cell(20, 10, str(transactions_data[i].id))
        pdf.set_xy(2*(20 + column_spacing) + pdf.l_margin, ybefore)
        pdf.multi_cell(50, 10, str(transactions_data[i].amount))
        pdf.set_xy(2*(50 + column_spacing) + pdf.l_margin, ybefore)
        pdf.multi_cell(100, 10, str(transactions_data[i].date_time))

    pdf.output(str(transactions_data[0].u_id)+"_"+date+".pdf")
    path = str(transactions_data[0].u_id)+"_"+date+".pdf"
    recipients = [str(email)]
    msg = Message(
        'Statement from Kuvera Bank',
        sender='samvans91@gmail.com',
        recipients=recipients
    )
    msg.body = 'Please find attached your historical statememt'
    with open(os.getcwd()+"/"+path, 'rb') as fh:
        msg.attach(filename=path, disposition="attachment",
                   content_type="application/pdf", data=fh.read())
    mail.send(msg)
    return jsonify({'message': 'Please check your mail for the statement'})


if __name__ == "__main__":
    app.run()
