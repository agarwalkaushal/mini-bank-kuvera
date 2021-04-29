import os
import config
from config import Config
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from constants import no_special_character_regex, valid_email_regex, strong_password_regex
from utils import decode_auth_token, encode_auth_token
import datetime
from fpdf import FPDF
from flask_mail import Mail, Message
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize app
app = Flask(__name__)

# Configuration of mail
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'kuverabank@gmail.com'
app.config['MAIL_PASSWORD'] = 'Test@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Setup environment
env_config = os.getenv("APP_SETTINGS")
app.config.from_object(env_config)

# Setup db
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(DB_URI)
metadata = MetaData(engine)
Session = sessionmaker()
Base = declarative_base()
Session.configure(bind=engine)
session = Session()


def check_if_first_day_of_month(date):
    if date.day == 1:
        return True
    return False


def get_table(name):
    return Table(name, Base.metadata, autoload=True, autoload_with=engine)


def get_last_transaction(transactions_table, user_id):
    return session.query(transactions_table).filter_by(
        u_id=user_id).order_by(transactions_table.columns.id.desc()).first()


def get_all_transactions_in_desc_order(transactions_table, user_id):
    return session.query(transactions_table).filter_by(
        u_id=user_id).order_by(transactions_table.columns.id.desc()).all()


def get_last_months_transactions_in_desc_order(transactions_table, user_id):
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    first_day_of_last_month = now.replace(
        hour=0, minute=0, second=0, microsecond=0)

    if today.month == 1:
        first_day_of_last_month = now.replace(
            year=now.year - 1, month=12, hour=0, minute=0, second=0, microsecond=0)
    else:
        first_day_of_last_month = now.replace(
            month=now.month-1, hour=0, minute=0, second=0, microsecond=0)

    return session.query(transactions_table).filter(and_(
        transactions_table.columns.u_id == user_id, transactions_table.columns.date_time < str(today),  transactions_table.columns.date_time >= str(first_day_of_last_month))).order_by(transactions_table.columns.id.desc()).all()


def send_statement_to_user(user, transactions_data):
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
        sender='kuverabank@gmail.com',
        recipients=recipients
    )
    msg.body = 'Please find attached your historical statememt'
    with open(os.getcwd()+"/"+path, 'rb') as fh:
        msg.attach(filename=path, disposition="attachment",
                   content_type="application/pdf", data=fh.read())
    mail.send(msg)


@app.route("/")
@app.route("/index")
@app.route("/foo")
def hello():
    return "bar"


@app.route('/register', methods=["POST"])
def register():
    username_input = request.args.get('username')
    email_input = request.args.get('email')
    password_input = request.args.get('password')
    users_table = get_table('users')
    exists = session.query(users_table).filter(
        or_(users_table.columns.username == username_input, users_table.columns.email == email_input)).first() is not None

    if exists:
        return jsonify({'message': 'User already registered'})

    if no_special_character_regex.search(username_input) != None:
        return jsonify({'message': 'Username cannot contain special characters'})

    if valid_email_regex.search(email_input) == None:
        return jsonify({'message': 'Enter valid email'})

    if strong_password_regex.search(password_input) == None:
        return jsonify({'message': 'Enter a strong password'})

    password_hash = generate_password_hash(password_input)

    engine.execute(users_table.insert(), username=username_input,
                   email=email_input, password=password_hash)
    return jsonify({'message': 'Registered successfully'})


@app.route('/sign_in', methods=["GET", "POST"])
def sign_in():
    username_input = request.args.get('username')
    password_input = request.args.get('password')
    users_table = get_table('users')

    user = session.query(users_table).filter_by(
        username=username_input).first()

    if user is not None and password_input and check_password_hash(user.password, password_input):
        auth_token = encode_auth_token(user.id)
        return jsonify({'signed_in': True, 'user_id': user.id, 'username': user.username, 'email': user.email, 'auth_token': auth_token})

    return jsonify({'signed_in': False})


@app.route('/transaction/transact', methods=["POST"])
def new_transaction():
    auth_token = request.headers['authtoken']
    request_data = request.get_json()

    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    transactions_table = get_table('transactions')

    last_transaction = get_last_transaction(transactions_table, user_id)

    amount = request_data['amount']

    if last_transaction == None:
        data = engine.execute(transactions_table.insert(), u_id=user_id, date_time=str(datetime.datetime.utcnow()),
                              balance=amount, amount=amount)
    else:
        balance = last_transaction.balance + amount
        data = engine.execute(transactions_table.insert(), u_id=user_id, date_time=str(datetime.datetime.utcnow()),
                              balance=balance, amount=amount)

    return jsonify({'message': 'Transaction successful', 'transaction_id': data.inserted_primary_key[0]})


@app.route('/transaction/balance', methods=["GET"])
def fetch_balance():
    auth_token = request.headers['authtoken']
    request_data = request.get_json()
    user_id = decode_auth_token(auth_token)

    if user_id.isnumeric() != True:
        return jsonify({'message': user_id})

    transactions_table = get_table('transactions')

    last_transaction = get_last_transaction(transactions_table, user_id)

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

    transactions_table = get_table('transactions')

    transactions_data = get_all_transactions_in_desc_order(
        transactions_table, user_id)

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

    transactions_table = get_table('transactions')

    transactions_data = get_all_transactions_in_desc_order(
        transactions_table, user_id)

    if len(transactions_data) == 0:
        return jsonify({'message': 'No records found'})

    users_table = get_table('users')

    user = session.query(users_table).filter_by(id=user_id).first()

    send_statement_to_user(user, transactions_data)

    return jsonify({'message': 'Please check your mail for the statement'})


def generate_statements():
    with app.app_context():
        if check_if_first_day_of_month(datetime.datetime.now()):
            transactions_table = get_table('transactions')
            users_table = get_table('users')
            users_data = session.query(users_table).all()
            if len(users_data) > 0:
                for user in users_data:
                    transactions_data = get_last_months_transactions_in_desc_order(
                        transactions_table, user.id)
                    if len(transactions_data) == 0:
                        continue
                    send_statement_to_user(user, transactions_data)
            return jsonify({'message': 'Statements generated successfully'})


if __name__ == "__main__":
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=generate_statements, trigger="interval", days=1)
    scheduler.start()
    app.run()

atexit.register(lambda: scheduler.shutdown())
