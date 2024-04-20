from django.http import HttpResponse
import pymongo
import json
from bson import json_util
import sys
sys.path.append('../')
from helpers.helpers import search, getIDEvento, checkData, check_keys, updateData
client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']

def index(request):
    collection = db['agenda']
    event_details = collection.find()

    json_data = json_util.dumps(list(event_details))
   
    response = HttpResponse(json_data, content_type='application/json')
    return response


def addEvento(request):
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    keys = ['name',  'type', 'date', 'location', 'num_of_people', 'cost', 'upfront']

    isDataCorrect, message = checkData(data, keys)
    statusCode = 400
    id_evento = getIDEvento(data['date'], 4)
    res = {}

    if isDataCorrect:
        query = {"location": data['location'], "date": data['date']}
        eventFound = search(query, collection)
        if eventFound:
            message = 'Blocked spot'
            statusCode = 404
        else:
            data['id_evento'] = id_evento
            result = collection.insert_one(data)  
            
            if result.inserted_id:
                status = 'successful.'
                res['id_evento'] = id_evento
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
    keys = ['id_evento']
    statusCode = 404
    
    isDataCorrect, message = checkData(data, keys)

    if isDataCorrect:
        res = collection.delete_one(data)
        # Check if the deletion was successful
        if res.deleted_count == 1:
            message = 'Event deleted successfully.'
            statusCode = 200
        else:
            message = 'Event not found or wrong id_evento'
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

    expected_keys = ['name', 'type', 'date', 'location', 'num_of_people', 'cost', 'upfront']
    res = {}
    if check_keys(data, expected_keys):
        res['events'] = list(collection.find(data))
    elif checkData(data, ['id_evento'])[0]:
        res['events'] = (collection.find_one({'id_evento' : data['id_evento']}))
    else:
        res = [{'message':'Missing filter or mispelled'}]
        statusCode = 400
    if res == None or res == []:
        res = [{'message':'Not data found with the filters asked'}]
        statusCode = 404
    return HttpResponse([res], content_type='application/json', status=statusCode)


def modifyEvento(request):
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    expected_keys = ['name',  'type', 'date', 'location', 'num_of_people', 'cost', 'upfront', 'id_evento']
    statusCode = 200

    response = {}
    print(data)
    if checkData(data, ['id_evento'])[0]:
        if check_keys(data, expected_keys):
            if checkData(data, ['location', 'date'])[0]:
                query = {"location": data['location'], "date": data['date'], "id_evento" : { "$ne" : data['id_evento']}}
                if search(query, collection):
                    response = {'message':'Blocked spot. Cannot change event to the desired place and date'}
                    statusCode = 404
                else:
                    print("Not blocked")
                    response = updateData(collection, {'id_evento': data['id_evento']}, { "$set" : data })
            
            elif not checkData(data, ['date'])[0] and not checkData(data, ['location'])[0]:
                response = updateData(collection, {'id_evento': data['id_evento']}, { "$set" : data })
            else:
                response = {'message':'Please if sending "location" or "date", send both'}
                statusCode = 400

    else:
        response = {'message': 'Not id_evento in JSON'}
        statusCode = 400
        
    json_data = json_util.dumps(response)
    return HttpResponse(json_data, content_type='application/json', status=statusCode)