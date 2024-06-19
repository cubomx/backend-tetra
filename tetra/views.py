from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, updateData, check_keys
from helpers.admin import verifyRole, generateBearer, hashPassword, TokenVerification, verifyPassword
from .helpers import addToOptions, getOptions, delOptions
from django.conf import settings

client =  pymongo.MongoClient(settings.DB['HOST'], settings.DB['PORT'], username=settings.DB['USER'], password=settings.DB['PASS'])
db = client[settings.DB['NAME']]
usuariosTable = db['usuarios']
adminTable = db['configuraciones']
projection = {"_id": False}

def users(request):
    result, statusCode = TokenVerification(request)
    res = {}

    allowed_roles = {'admin'}
    if statusCode != 200:
        res = result
    elif result.decoded_token['role'] in allowed_roles:
        usuarios = [usuariosTable.find({}, {'password':0})]
        res['users'] = usuarios[0]
    else:
        res['message'] = 'Accion no permitida al usuario'

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def changePass(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    result, statusCode = TokenVerification(request)

    res = {}

    data = json.loads(request.body.decode('utf-8'))
    keys = ['password', 'email', 'role', 'name']
    onlyAllowed = check_keys(data, keys)
    roles = {'admin', 'secretary', 'finance', 'inventary'}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)

    if statusCode != 200:
        res = result
    elif onlyAllowed and checkData(data, ['email'], {'email':str})[0]:
        email = data['email']
        user = usuariosTable.find_one({'email': email}, projection)
        if checkData(data, ['password'], {'password':str})[0]:
            data['password'] = hashPassword(data['password']).decode('utf-8')
        if user and len(user) > 0:
            update = {'$set': data}
            if 'isMaster' in user:
                statusCode = 401
                res['message'] = 'No se puede modificar la cuenta maestra'
            elif data['role']:
                if data['role'] in roles:
                    res = updateData(usuariosTable, {'email':data['email']}, update)
                else:
                    res['message'] = 'Rol no permitido {}'.format(data['role'])
                    statusCode = 400
            else:
                res = updateData(usuariosTable, {'email':data['email']}, update)
        else:
            res['message'] = 'Usuario no encontrado {}'.format(data['email'])
    else:
        res['message'] = 'Datos enviados incorrectos'
        statusCode = 400

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def delUsuario(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    result, statusCode = TokenVerification(request)

    res = {}

    data = json.loads(request.body.decode('utf-8'))
    keys = ['email']
    onlyAllowed = check_keys(data, keys)
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)

    if statusCode != 200:
        res = result
    elif onlyAllowed and checkData(data, ['email'], {'email':str})[0]:
        email = data['email']
        user = usuariosTable.find_one({'email': email}, projection)
        if user and len(user) > 0:
            if 'isMaster' in user:
                statusCode = 401
                res['message'] = 'No se puede eliminar la cuenta maestra'
            else:
                result = usuariosTable.delete_one(data)
                if result.acknowledged:
                    res['message'] = 'Usuario eliminado satisfactoriamente'
                else:
                    statusCode = 500
                    res['message'] = 'Se produjo un error al eliminar el usuario'
        else:
            res['message'] = 'Usuario no encontrado {}'.format(data['email'])
    else:
        res['message'] = 'Datos enviados incorrectos'
        statusCode = 400

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
            hPass = user['password']
            if verifyPassword(data['password'], hPass):
                
                role = user['role']
                secret_key = settings.SECRET_KEY
                bearer_token = generateBearer(secret_key, role=role)
                res['token'] = bearer_token
            else:
                res['message'] = 'Credenciales incorrectas'
                statusCode = 401
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
    keys = ['password', 'email', 'role', 'name']
    types = {'password' : str, 'email': str, 'role':str, 'name':str}
    isDataCorrect, message = checkData(data, keys, types)
    roles = {'admin', 'auditor', 'finance', 'vendor', 'chef'}
    allowed_roles = {'admin'}
    if statusCode != 200:
        res = result
    elif not isDataCorrect:
        res['message'] = message
        statusCode = 400
    elif statusCode == 200:
        request = result
        if result.decoded_token['role'] in allowed_roles:
            hashedPass = hashPassword(data['password']).decode('utf-8')
            if data['role'] in roles:
                if usuariosTable.find_one({'email':data['email']}) == None:
                    createResult = usuariosTable.insert_one({'email': data['email'], 
                                                        'password':hashedPass, 'role': data['role'], 'name':data['name']})
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

def delOption(request, key, types, optionsKey, message):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    res = {}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode =  delOptions(adminTable, request, key, types, optionsKey, message)
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def addOption(request, key, types, optionsKey, message):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    res = {}
    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode = addToOptions(adminTable, request, key, types, optionsKey, message)
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def get(request, key, message):
    allowed_roles = {'admin', 'auditor', 'finance', 'vendor', 'chef'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    else:
        res, statusCode = getOptions(adminTable, key, message)
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def addEventType(request):
    return addOption(request, ['type'], {'type': str}, 'types', 'tipo de evento')

def getEventTypes(request):
    return get(request, 'types', 'tipo de evento')

def delEventType(request):
    return delOption(request, ['type'], {'type':str}, 'types', 'tipo de evento')

def addLocation(request):
    return addOption(request, ['location'], {'location': str}, 'locations', 'lugar de evento')

def getLocations(request):
    return get(request, 'locations', 'lugar de evento')

def delLocation(request):
    return delOption(request, ['location'], {'location':str}, 'locations', 'lugar de evento')

# Expenses/Ingresses Options
def addConcept(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return addOption(request, ['concept'], {'concept':str}, type_, 'ingreso de evento')

def getConcepts(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return get(request, type_, 'ingreso de evento')

def delConcepts(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return delOption(request, ['concept'], {'concept':str}, type_ , 'ingreso de evento')


# Providers
def addProvider(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return addOption(request, ['provider'], {'provider':str}, type_, 'proveedor')

def getProviders(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return get(request, type_, 'ingreso de evento')

def delProvider(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    type_ = data['type']
    return delOption(request, ['provider'], {'concept':str}, type_ , 'ingreso de evento')

