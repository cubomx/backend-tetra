from datetime import datetime, timedelta
import bcrypt
from jwt import decode, ExpiredSignatureError, encode
from django.conf import settings

def getToken(authorization_header):
    if authorization_header:
        # Check if the header starts with 'Bearer '
        if authorization_header.startswith('Bearer '):
            # Extract the token from the header
            bearer_token = authorization_header[len('Bearer '):]
            # You now have the Bearer token
            return ({'token': bearer_token }, 200)
        else:
            # Authorization header does not start with 'Bearer '
            return ({'error': 'Invalido token'}, 400)
    else:
        # Authorization header is missing
        return ({'error': 'Falta token'}, 400)
    
def generateBearer(secret_key, expiration_time=3600):
    exp_time = datetime.utcnow() + timedelta(seconds=expiration_time)

    # Create the payload for the JWT token
    payload = {
        'exp': exp_time,
        'iat': datetime.utcnow()
        # You can add other claims as needed
    }

    # Generate the JWT token with the payload and the secret key
    token = encode(payload, secret_key, algorithm='HS256')
    return token

def hashPassword(password):
    # Generate a salt for hashing
    salt = bcrypt.gensalt()

    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    return hashed_password

def verifyPassword(plain_password, hashed_password):
    # Hash the plain password using the same salt as the hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))



def TokenVerification(request):
    auth_token = request.META.get("HTTP_AUTHORIZATION")

    if auth_token and auth_token.startswith('Bearer '):
        token = auth_token.split(' ')[1]

        try:
            # Decode and verify the token
            decoded_token = decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            # Optionally, perform additional checks or validations on the decoded token

            # Set the decoded token as an attribute of the request for access in views
            request.decoded_token = decoded_token
            request.token = token
            return (request, 200)

        except ExpiredSignatureError:
            return ({'error': 'Expired token'}, 401)

        except Exception as e:
            return ({'error': 'Invalid token'}, 401)
