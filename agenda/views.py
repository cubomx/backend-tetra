from django.http import HttpResponse, FileResponse
import pandas as pd
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import search, getIDEvento, checkData, check_keys, updateData, returnExcel, searchWithProjection
client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']
agendaTable = db['agenda']

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
    id_event = getIDEvento(data, 4)
    res = {}
    

    if isDataCorrect:
        target_year, target_month, target_day = data['year'], data['month'], data['day']
        future = data['isFuture']
        query = {}
        if future:
            query = {
                '$or': [{'year': {'$gt': target_year}},
                    {'$and': [{'year': target_year},
                        {'$or': [{'month': {'$gt': target_month}},
                            {'month': {'$eq': target_month}, 'day': {'$gte': target_day}}]}
                    ]}
                ]}
        else:
            query = {
                '$or': [{'year': {'$lt': target_year}},
                    {'$and': [{'year': target_year},
                        {'$or': [{'month': {'$lt': target_month}},
                            {'month': {'$eq': target_month}, 'day': {'$lt': target_day}}]}
                    ]}
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
             'location' : str, 'num_of_people' : int, 'cost': float, 'upfront': float         
    }

    isDataCorrect, message = checkData(data, keys, types)
    statusCode = 400
    id_event = getIDEvento(data, 4)
    res = {}

    if isDataCorrect:
        query = {'location': data['location'], 'day': data['day'], 'month' : data['month'], 'year' : data['year']}
        eventFound = search(query, agendaTable)
        if eventFound:
            message = 'Espacio no disponible'
            statusCode = 404
        else:
            data['id_event'] = id_event
            data['expenses'] = []
            result = agendaTable.insert_one(data)  
            
            if result.inserted_id:
                status = 'con éxito.'
                res['id_event'] = id_event
                statusCode = 200
            else:
                status = 'fallido.'
                statusCode = 400 

            message = 'Evento añadido {}'.format(status)
    res['message'] = message
    json_data = json_util.dumps([res])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def delEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json', status=400)

    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_event']
    statusCode = 404
    
    isDataCorrect, message = checkData(data, keys, {'id_event' : str})

    if isDataCorrect:
        res = agendaTable.delete_one(data)
        # Check if the deletion was successful
        if res.deleted_count == 1:
            message = 'Evento eliminado exitosamente.'
            statusCode = 200
        else:
            message = 'Evento no encontrado o ID de evento equivocado'
            statusCode = 404

    json_data = json_util.dumps([{"message": message}])
    
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

# check if all the keys are part of the collection

def getEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200

    expected_keys = ['name', 'type', 'year', 'day', 'month', 'location', 'num_of_people', 'cost', 'upfront', 'excel']
    res = {}
    if check_keys(data, expected_keys):
        res['events'] = list(agendaTable.find(data, projection))
    elif checkData(data, ['id_event'], {'id_event' : str})[0]:
        res['events'] = [(agendaTable.find_one({'id_event' : data['id_event']}, projection))]
    else:
        res = [{'message':'Faltan filtros o estan incorrectos. Filtros: name, type, year, day, month...'}]
        statusCode = 400
    if res['events'] == [None]:
        res = [{'message':' No información encontrada con los filtros usados'}]
        statusCode = 404
    elif checkData(data, ['excel'], {'excel' : str})[0]:
        print(res)
        headers = {
            'name':'nombre', 'type':'categoria', 'year':'año', 'day':'día', 'month':'mes', 
            'location':'ubicacion', 'num_of_people':'invitados', 'cost':'costo', 'upfront':'adelanto'
        }
        df = pd.DataFrame(res['events'])
        return returnExcel(df, headers, 'eventos', 'detalles')
    return HttpResponse([res], content_type='application/json', status=statusCode)


def modifyEvento(request):
    data = json.loads(request.body.decode('utf-8'))
    expected_keys = ['name',  'type', 'day', 'month', 'year', 'location', 'num_of_people', 'cost', 'upfront', 'id_event']
    statusCode = 200

    response = {}
    print(data)
    if checkData(data, ['id_event'], {'id_event' : str})[0]:
        if check_keys(data, expected_keys):
            if checkData(data, ['location', 'day', 'month', 'year'], {'location' : str, 'day' : int, 'month' : int, 'year' : int})[0]:
                query = {'location': data['location'], 
                         'day': data['day'], 'month' : data['month'], 'year' : data['year'], 
                         'id_event' : { '$ne' : data['id_event']}}
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
                response = {'message':'Por favor, si envías alguna de estas variables "location" o "day", "month, year", envía todas '}
                statusCode = 400

    else:
        response = {'message': 'No esta presente el ID del evento en JSON'}
        statusCode = 400
        
    json_data = json_util.dumps(response)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)