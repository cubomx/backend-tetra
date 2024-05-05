from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import checkData, updateData
from helpers.admin import getToken, generateBearer, hashPassword, TokenVerification, verifyPassword
from django.conf import settings

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
usuariosTable = db['usuarios']
adminTable = db['configuraciones']
tokensTable = db['tokens']
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

        if len(user) > 0:
            print(user)
            hPass = user['password']
            if verifyPassword(data['password'], hPass):
                
                role = user['role']
                secret_key = settings.SECRET_KEY
                bearer_token = generateBearer(secret_key)
                res['token'] = bearer_token
                result = tokensTable.insert_one({'token':bearer_token, 'role':role})
                print(tokensTable.find_one({'token':bearer_token}))
                if not result.inserted_id:
                    res['error'] = 'El token no puede ser guardado satisfactoriamente'
                    del res['token']
                    statusCode = 500
            else:
                res['message'] = 'Credenciales incorrectas'
                statusCode = 404
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

    if not isDataCorrect:
        res['message'] = message
        statusCode = 400
    elif statusCode == 200:
        request = result
        resToken = tokensTable.find_one({'token': request.token}, projection)

        if resToken:
            if resToken['role'] == 'admin':
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
                        statusCode = 200
                else:
                    res['message'] = 'El rol {} no se encuentra dentro de los posibles roles'.format(data['role'])
                    statusCode = 400
            else:
                res['message'] = 'El usuario no cuenta con los permisos necesarios para crear nuevos usuarios'
           
        else:
            res['message'] = 'No se encontro el token'
            statusCode = 500
    else:
        res = result 
    
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def addEventType(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    data = json.loads(request.body.decode('utf-8'))
    res = {}

    isDataCorrect, message = checkData(data, ['type'], {'type':str})
    statusCode = 200
    if isDataCorrect:
        query = { "types": { '$exists': True } }
        result = adminTable.find_one(query)
        if result != None:
            # check duplicates
            if adminTable.find_one({'types':data['type']}) != None:
                print("yupi")
                statusCode = 406
                res['message'] = 'El tipo de evento {} ya esta disponible para seleccionar'.format(data['type'])
            else:
                update_query = {'$addToSet': {"types": data['type']}}
                result = updateData(adminTable, query, update_query)
                if result['result'] > 0:
                    res['message'] = 'Fue agregado con exito el nuevo tipo de evento {}'.format(data['type'])
                else:
                    statusCode = 500
                    res['message'] = 'Hubo un error al querer insertar el nuevo tipo de evento {}'.format(data['type'])
        else:
            resultInsert = adminTable.insert_one({'types': [data['type']]})
            if resultInsert.inserted_id:
                res['message'] = 'Fue agregado con exito el nuevo tipo de evento {}'.format(data['type'])
            else:
                statusCode = 500
                res['message'] = 'Hubo un error al querer insertar el nuevo tipo de evento {}'.format(data['type'])
    else:
        statusCode = 400
        res['message'] = message

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)



def addLocation(request):
    return

def getEventTypes(request):
    res = {}
    statusCode = 200
    query = { "types": { '$exists': True } }
    result = adminTable.find_one(query)
    if result != None:
        print(result)
        res['types'] = result['types']
    else:
        res['message'] = 'No se encontro ningun tipo de evento, dile al administrador que agregue tipos'
        statusCode = 404

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

def getLocation(request):
    return

def delEventType(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    data = json.loads(request.body.decode('utf-8'))
    res = {}

    isDataCorrect, message = checkData(data, ['type'], {'type':str})
    statusCode = 200
    if isDataCorrect:
        query = { "types": { '$exists': True } }
        delUpdate = {'$pull': {'types': data['type']}}
        result = updateData(adminTable, query, delUpdate)
        if result['result'] > 0:
            res['message'] = 'Se elimino el tipo de evento {} satisfactoriamente'.format(data['type'])
        else:
            res['message'] = 'Hubo un error al eliminar el tipo de evento {}'.format(data['type'])
            statusCode = 500
    else:
        statusCode = 400
        res['message'] = message

    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)