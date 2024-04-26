from django.http import HttpResponse, FileResponse
import pandas as pd
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import search, getIDEvento, checkData, check_keys, updateData, returnExcel
client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']

projection = {"_id": False}

def index(request):
    collection = db['agenda']
    event_details = collection.find()

    json_data = json_util.dumps(list(event_details))
   
    response = HttpResponse(json_data, content_type='application/json')
    return response


def addEvento(request):
    collection = db['agenda']
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
        eventFound = search(query, collection)
        if eventFound:
            message = 'Blocked spot'
            statusCode = 404
        else:
            data['id_event'] = id_event
            data['inventory'] = []
            result = collection.insert_one(data)  
            
            if result.inserted_id:
                status = 'successful.'
                res['id_event'] = id_event
                statusCode = 200
            else:
                status = 'failed.'
                statusCode = 400 

            message = 'Event added {}'.format(status)
    res['message'] = message
    json_data = json_util.dumps([res])
    response = HttpResponse(json_data, content_type='application/json', status=statusCode)
    return response

def delEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_event']
    statusCode = 404
    
    isDataCorrect, message = checkData(data, keys, {'id_event' : str})

    if isDataCorrect:
        res = collection.delete_one(data)
        # Check if the deletion was successful
        if res.deleted_count == 1:
            message = 'Event deleted successfully.'
            statusCode = 200
        else:
            message = 'Event not found or wrong id_event'
            statusCode = 404

    json_data = json_util.dumps([{"message": message}])
    
    return HttpResponse(json_data, content_type='application/json', status=statusCode)

# check if all the keys are part of the collection

def getEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')
    
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    statusCode = 200

    expected_keys = ['name', 'type', 'year', 'day', 'month', 'location', 'num_of_people', 'cost', 'upfront', 'excel']
    res = {}
    if check_keys(data, expected_keys):
        res['events'] = list(collection.find(data, projection))
    elif checkData(data, ['id_event'], {'id_event' : str})[0]:
        res['events'] = [(collection.find_one({'id_event' : data['id_event']}, projection))]
    else:
        res = [{'message':'Missing filter or mispelled'}]
        statusCode = 400
    if res == None or res == []:
        res = [{'message':'Not data found with the filters asked'}]
        statusCode = 404
    elif checkData(data, ['excel'], {'excel' : str})[0]:
        headers = {
            'name':'nombre', 'type':'categoria', 'year':'año', 'day':'día', 'month':'mes', 
            'location':'ubicacion', 'num_of_people':'invitados', 'cost':'costo', 'upfront':'adelanto'
        }
        df = pd.DataFrame(res['events'])
        return returnExcel(df, headers, 'eventos', 'detalles')
    return HttpResponse([res], content_type='application/json', status=statusCode)


def modifyEvento(request):
    collection = db['agenda']
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
                if search(query, collection):
                    response = {'message':'Blocked spot. Cannot change event to the desired place and date'}
                    statusCode = 404
                else:
                    print("Not blocked")
                    response = updateData(collection, {'id_event': data['id_event']}, { "$set" : data })
            # checking if some of the date/location variables are present
            elif not checkData(data, ['day', 'month', 'year', 'location'], {'location' : str, 'day' : int, 'month' : int, 'year' : int})[0]:
                response = updateData(collection, {'id_event': data['id_event']}, { "$set" : data })
            else:
                response = {'message':'Please if sending "location" or "day/month/year", send all four variables'}
                statusCode = 400

    else:
        response = {'message': 'Not id_event in JSON'}
        statusCode = 400
        
    json_data = json_util.dumps(response)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)