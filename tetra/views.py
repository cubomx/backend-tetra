from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, updateData
from helpers.admin import verifyRole, generateBearer, hashPassword, TokenVerification, verifyPassword
from .helpers import addToOptions, getOptions, delOptions
from django.conf import settings

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
usuariosTable = db['usuarios']
adminTable = db['configuraciones']
projection = {"_id": False}

def users(request):
    usuarios = [usuariosTable.find()]
    res= {}
    statusCode = 200
    res['users'] = usuarios

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def login(request):
    if not request.content_type == 'application/json':
       return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    keys = ['password', 'email']
    types = {'password' : str, 'email': str}

    res ={}
    statusCode = 200

    isDataCorrect, message = checkData(data, keys, types)
    if isDataCorrect:
        email = data['email']
        user = usuariosTable.find_one({'email': email}, projection)

        if user and len(user) > 0:
            print(user)
            hPass = user['password']
            if verifyPassword(data['password'], hPass):
                
                role = user['role']
                secret_key = settings.SECRET_KEY
                bearer_token = generateBearer(secret_key, role=role)
                res['token'] = bearer_token
        else:
            res['message'] = 'Datos incorrectos'
            statusCode = 401
    else:
        res['message'] = message
        statusCode = 400

    
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def register(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    result, statusCode = TokenVerification(request)
    
    res = {}

    data = json.loads(request.body.decode('utf-8'))
    keys = ['password', 'email', 'role']
    types = {'password' : str, 'email': str, 'role':str}
    isDataCorrect, message = checkData(data, keys, types)
    roles = {'admin', 'secretary', 'finance', 'inventary'}
    allowed_roles = {'admin'}
    if statusCode == 200:
        print(result.decoded_token)

    if not isDataCorrect:
        res['message'] = message
        statusCode = 400
    elif statusCode == 200:
        request = result
        if result.decoded_token['role'] in allowed_roles:
            hashedPass = hashPassword(data['password']).decode('utf-8')
            if data['role'] in roles:
                if usuariosTable.find_one({'email':data['email']}) == None:
                    createResult = usuariosTable.insert_one({'email': data['email'], 
                                                        'password':hashedPass, 'role': data['role']})
                    if createResult.inserted_id:
                        res['message'] = 'Usuario creado con exito'
                    else:
                        res['message'] = 'Error al crear usuario'
                        statusCode = 500
                else:
                    res['message'] = 'Correo ya en uso'
                    statusCode = 400
            else:
                res['message'] = 'El rol {} no se encuentra dentro de los posibles roles'.format(data['role'])
                statusCode = 400
        else:
            res['message'] = 'El usuario no cuenta con los permisos necesarios para crear nuevos usuarios'
           
    else:
        res = result 
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def addEventType(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    res = {}
    if statusCode != 200:
        res = result
    else:
        res, statusCode = addToOptions(adminTable, request, ['type'], {'type': str}, 'types', 'tipo de evento')
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getEventTypes(request):
    allowed_roles = {'admin', 'finance', 'inventary', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode = getOptions(adminTable, 'types', 'tipo de evento')
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)


def delEventType(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    res = {}
    if statusCode != 200:
        res = result
    else:
        res, statusCode =  delOptions(adminTable, request, ['type'], {'type':str}, 'types', 'tipo de evento')
    
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def addLocation(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    res = {}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode = addToOptions(adminTable, request, ['location'], {'location': str}, 'locations', 'lugar de evento')
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getLocations(request):
    allowed_roles = {'admin', 'finance', 'inventary', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    res = {}
    if statusCode != 200:
        res = result
    else:
        res, statusCode = getOptions(adminTable, 'locations', 'lugar de evento')
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def delLocation(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    res = {}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode =  delOptions(adminTable, request, ['location'], {'location':str}, 'locations', 'lugar de evento')
    
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)