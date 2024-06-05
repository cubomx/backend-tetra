import math
from django.http import HttpResponse, FileResponse
from django.conf import settings
import pandas as pd
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import search, getIDEvento, checkData, check_keys, updateData, returnExcel, searchWithProjection
from helpers.admin import verifyRole

client =  pymongo.MongoClient(settings.DB['HOST'], settings.DB['PORT'], username=settings.DB['USER'], password=settings.DB['PASS'])
db = client[settings.DB['NAME']]
agendaTable = db['agenda']
gastosTable = db['gastos']
abonosTable = db['abonos']
projection = {"_id": False}

def index(request):
    collection = db['agenda']
    event_details = collection.find()

    json_data = json_util.dumps(list(event_details))
   
    response = HttpResponse(json_data, content_type='application/json')
    return response

def agenda(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200

    keys = ['day', 'month', 'year', 'isFuture'] 
    types = {'day' : int, 'month' : int, 'year' : int, 'isFuture':bool}

    isDataCorrect, message = checkData(data, keys, types)
    statusCode = 400
    res = {}
    
    allowed_roles = {'admin', 'secretary', 'finance', 'inventary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        res = result
    elif isDataCorrect:
        target_year, target_month, target_day = data['year'], data['month'], data['day']
        print(target_month)
        future = data['isFuture']
        query = {}
        if future:
            query = {
            '$and': [{'year': {'$gte': target_year}},
                    {'$or': [{'month': {'$gt': target_month}},
                        {'month': {'$eq': target_month}, 'day': {'$gte': target_day}}]}
                ]}
        else:
            query = {
                '$and': [{'year': {'$lte': target_year}},
                    {'$or': [{'month': {'$lt': target_month}},
                        {'month': {'$eq': target_month}, 'day': {'$lt': target_day}}]}
                ]}
        result, statusCode = searchWithProjection(query, projection, agendaTable, 'No se encontraron eventos')
        if statusCode == 200:
            res['events'] = []
            for event in result:
                res['events'].append(event)      
        else:
            error = 'despues' if future else 'anteriores'
               
            res['message'] = 'No se encontraron eventos {} de la {}/{}/{}'.format(error, target_day, target_month, target_year)
            statusCode = 404
    else:
        res['message'] = message
        statusCode = 400

    json_data = json_util.dumps(res)
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

    
def addEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)
    
    data = json.loads(request.body.decode('utf-8'))
    keys = ['name',  'type', 'day', 'month', 'year', 'location', 'num_of_people', 'cost', 'upfront']
    types = {'name': str, 'type': str, 'day' : int, 'month' : int, 'year' : int,  
             'location' : str, 'num_of_people' : int, 'cost': int, 'upfront': int         
    }

    isDataCorrect, message = checkData(data, keys, types)
    statusCode = 400
    id_event = getIDEvento(data, 2)
    res = {}
    allowed_roles = {'admin', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        message = result['message']
    elif isDataCorrect:
        if data['cost'] < data['upfront']:
            statusCode = 400
            message = 'El pago del evento {} es menor al pago inicial {}'.format(data['cost'], data['upfront'])
        else:  

            query = {'location': data['location'], 
                     'day': data['day'], 'month' : data['month'], 'year' : data['year'],
                     'state': {'$in':['completado', 'pendiente']}}
            eventFound = search(query, agendaTable)
            if eventFound:
                message = 'Espacio no disponible'
                statusCode = 404
            else:
                data['id_event'] = id_event
                data['expenses'] = []
                data['state'] = 'pendiente'
                result = agendaTable.insert_one(data)  
                
                if result.inserted_id:
                    status = 'con exito.'
                    res['id_event'] = id_event
                    statusCode = 200
                else:
                    status = 'fallido.'
                    statusCode = 400 

                message = 'Evento agregado {}'.format(status)
    res['message'] = message
    json_data = json_util.dumps(res)
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def delEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_event']
    statusCode = 404
    
    isDataCorrect, message = checkData(data, keys, {'id_event' : str})

    allowed_roles = {'admin'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        message = result['message']
    elif isDataCorrect:
        id_event = data['id_event']
        result = agendaTable.find_one({'id_event':data['id_event']}, {"expenses": 1, "_id": 0})

        if result:
            expenses = result['expenses']
            #res = agendaTable.delete_one(data)
            updateData(agendaTable, {'id_event':id_event}, {'$set': {'expenses': [], 'state': 'cancelado'}})
            # Check if the deletion was successful
            for expense in expenses:
                queryUpdateGastos = {'$inc': {'available': expense['portion']}, 
                                        '$pull' : {'allocation':{'id_event':id_event}}}
                updateData(gastosTable, {'id_expense':expense['id_expense']}, queryUpdateGastos)                
                
            abonosTable.delete_many({'id_event':id_event})
            message = 'Evento eliminado exitosamente.'
            statusCode = 200
        else:
            message = 'Evento no encontrado o ID de evento equivocado'
            statusCode = 404

    json_data = json_util.dumps({"message": message})
    
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

# check if all the keys are part of the collection

def getEvento(request):
    if not request.content_type == 'application/json':
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200

    expected_keys = ['name', 'type', 'year', 'day', 'month', 'location', 'num_of_people', 'cost', 'upfront', 'excel', 'state', 'sortear']
    res = {}
    allowed_roles = {'admin', 'secretary', 'finance', 'inventary'}
    result, statusCode = verifyRole(request, allowed_roles)

    if statusCode != 200:
        res = result
    elif 'state' in data and isinstance(data['state'], list):
        data['state'] = {'$in':data['state']}
        if 'sortear' in data and data['sortear'] <= 1:
            sort = data['sortear']
            del data['sortear']
            res['events'] = list(agendaTable.find(data, projection).sort([('margin.margin', sort)]))
        else:
            res['events'] = list(agendaTable.find(data, projection))
         

    elif check_keys(data, expected_keys):
        res['events'] = list(agendaTable.find(data, projection))
    elif checkData(data, ['id_event'], {'id_event' : str})[0]:
        res['events'] = [(agendaTable.find_one({'id_event' : data['id_event']}, projection))]
    else:
        res = [{'message':'Faltan filtros o estan incorrectos. Filtros: name, type, year, day, month...'}]
        statusCode = 400

    if 'events' in res and res['events'] == [None]:
        res = [{'message':' No informacion encontrada con los filtros usados'}]
        statusCode = 404
    elif checkData(data, ['excel'], {'excel' : str})[0]:
        print(res)
        headers = {
            'name':'nombre', 'type':'categoria', 'year':'año', 'day':'día', 'month':'mes', 
            'location':'ubicacion', 'num_of_people':'invitados', 'cost':'costo', 'upfront':'adelanto', 'state':'estado'
        }
        df = pd.DataFrame(res['events'])
        return returnExcel(df, headers, 'eventos', 'detalles')
    json_data = json_util.dumps(res)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)


def modifyEvento(request):
    data = json.loads(request.body.decode('utf-8'))
    expected_keys = ['name',  'type', 'day', 'month', 'year', 'location', 'num_of_people', 'cost', 'upfront', 'id_event', 'state']
    statusCode = 200

    response = {}
    allowed_roles = {'admin', 'secretary'}
    result, statusCode = verifyRole(request, allowed_roles)
    if statusCode != 200:
        response = result
    elif checkData(data, ['id_event'], {'id_event' : str})[0]:
        if check_keys(data, ['cost', 'upfront']):
            if data['cost'] < data['upfront']:
                statusCode = 400
                response['message'] = 'El pago del evento {} es menor al pago inicial {}'.format(data['cost'], data['upfront'])
        if statusCode == 200 and check_keys(data, expected_keys):
            if checkData(data, ['location', 'day', 'month', 'year'], {'location' : str, 'day' : int, 'month' : int, 'year' : int})[0]:
                query = {'location': data['location'], 
                         'day': data['day'], 'month' : data['month'], 'year' : data['year'], 
                         'id_event' : { '$ne' : data['id_event']}, 'state': {'$in':['completado', 'pendiente']}}
                if search(query, agendaTable):
                    response = {'message':'Espacio bloqueado. No se puede cambiar el evento a la fecha y lugar deseado.'}
                    statusCode = 404
                else:
                    print("Not blocked")
                    response = updateData(agendaTable, {'id_event': data['id_event']}, { "$set" : data })
            # checking if some of the date/location variables are present
            elif not checkData(data, ['day', 'month', 'year', 'location'], {'location' : str, 'day' : int, 'month' : int, 'year' : int})[0]:
                response = updateData(agendaTable, {'id_event': data['id_event']}, { "$set" : data })
            else:
                response = {'message':'Por favor, si envias alguna de estas variables "location" o "day", "month, year", envia todas '}
                statusCode = 400
        else:
            response={'message': 'Estas enviando datos de mas'}
            statusCode = 400
    else:
        response = {'message': 'No esta presente el ID del evento en JSON'}
        statusCode = 400
        
    json_data = json_util.dumps(response)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)