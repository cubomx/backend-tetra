from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
import bcrypt

def hash_password(password):
    # Generate a salt for hashing
    salt = bcrypt.gensalt()

    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    return hashed_password



def login(request):
    if not request.content_type == 'application/json':
       return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    password = "my_password"
    hashed_password = hash_password(password)
    print("Hashed password:", hashed_password.decode('utf-8'))
    res ={}
    res['pass'] = hashed_password
    statusCode = 200
    
    json_data = json_util.dumps([res])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def register(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
