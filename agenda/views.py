from django.http import HttpResponse
import pymongo
import json
from bson import json_util
from .helpers import checkAvailability, getIDEvento, checkData, check_keys, updateData, checkForChangeOfID
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
    id_evento = getIDEvento(data)
    message = id_evento
    print(data)
    if isDataCorrect:
        query = {"location": data['location'], "date": data['date']}
        eventFound = checkAvailability(query, collection)
        if eventFound:
            message = 'Blocked spot'
        else:
            print(eventFound)
            data['id_evento'] = id_evento
            message = 'Available spot'

            res = collection.insert_one(data)  
            status = "successful." if res.inserted_id  else "failed."   
            message = 'Event added {}'.format(status)
    
    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json')
    return response

def delEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    keys = ['id_evento']
    
    isDataCorrect, message = checkData(data, keys)

    if isDataCorrect:
        res = collection.delete_one(data)

        # Check if the deletion was successful
        if res.deleted_count == 1:
            message = 'Event deleted successfully.'
        else:
            message = 'Event not found or wrong id_evento'
    else:
        message = 'Not event found with {} and location {}'.format(data['date'], data['location'])
    json_data = json_util.dumps([{"message": message}])
    
    return HttpResponse(json_data, content_type='application/json')

# check if all the keys are part of the collection

def getEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')
    
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))

    expected_keys = ['name', 'type', 'date', 'location', 'num_of_people', 'cost', 'upfront']
    res =''
    if check_keys(data, expected_keys):
        res = collection.find(data)
    elif checkData(data, ['id_evento'])[0]:
        res = collection.find_one({'id_evento' : data['id_evento']})
    else:
        res = [{'message':'Missing filter'}]
    if res == None:
        res = {'message':'Not data found with the filters asked'}
    return HttpResponse([res], content_type='application/json')


def modifyEvento(request):
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    expected_keys = ['name',  'type', 'date', 'location', 'num_of_people', 'cost', 'upfront', 'id_evento']

    response = {}
    print(data)
    if checkData(data, ['id_evento','location', 'date'])[0]:
        if check_keys(data, expected_keys):
            query = {"location": data['location'], "date": data['date'], "id_evento" : { "$ne" : data['id_evento']}}

            if checkAvailability(query, collection):
                response = {'message':'Blocked spot. Cannot change event to the desired place and date'}
            else:
                print("Not blocked")
                data['id_evento'], old_id = checkForChangeOfID(data, collection)

                response = updateData(collection, {'id_evento': old_id}, { "$set" : data })
    elif not checkData(data, ['location', 'date'])[0] and checkData():
        response = updateData(collection, {'id_evento': data['id_evento']}, { "$set" : data })
        
    json_data = json_util.dumps(response)
    return HttpResponse(json_data, content_type='application/json')