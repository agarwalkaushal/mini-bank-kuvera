import jwt
import datetime
from config import Config

SECRET_KEY = Config.SECRET_KEY

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(bytes.fromhex(auth_token), SECRET_KEY)
        return str(payload['sub'])
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'


def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=0),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        ).hex()
    except Exception as e:
        return e