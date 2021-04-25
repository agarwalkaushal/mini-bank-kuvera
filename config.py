import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    DEBUG = False
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost:5432/kuverabank?user=admin&password=test'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgres://genumdbjsvpwwy:d69e137cec89140dc2b961a07bc03060d509189bf1be93909d833d7cb535f90a@ec2-3-217-219-146.compute-1.amazonaws.com:5432/d44gnuspci1ope'

class DevelopmentConfig(Config):
    DEBUG = True