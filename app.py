from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

app = Flask(__name__)
app.config.from_object(Config)
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(DB_URI)


@app.route("/foo")
def hello():
  return "bar"

if __name__ == "__main__":
  app.run()
  
