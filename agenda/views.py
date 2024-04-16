from django.http import HttpResponse, JsonResponse
import pymongo
import requests
import json
from bson import json_util

client =  pymongo.MongoClient('localhost', 27017, username='root', password='example')
db = client['tetra']

def index(request):
    collection = db['agenda']
    event_details = collection.find()

    json_data = json_util.dumps(list(event_details))
   
    response = HttpResponse(json_data, content_type='application/json')
    return response

def json_contains_key(data, keys):
    for key in keys:
        if key not in data:
            return (False, "Missing key {} in data sent".format(key))
    return (True, "Data seems good")

def checkEventoData(data):
    keys = ['name', 'clients', 'type', 'date', 'location', 'num_of_people', 'cost', 'upfront']
    return json_contains_key(data, keys)


def checkAvailability(data, collection):
    location = data['location']
    date = data['date']

    return list(collection.find({"location": location, "date": date}))


def addEvento(request):
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))

    isDataCorrect, message = checkEventoData(data)

    if isDataCorrect:
        eventFound = checkAvailability(data, collection)
        if eventFound:
            message = 'Blocked spot'
        else:
            print(eventFound)
            message = 'Available spot'

            res = collection.insert_one(data)  
            status = "successful." if res.inserted_id  else "failed."   
            message = 'Event added {}'.format(status)



    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json')
    return response


'''event = {
    "id_evento": "SV_20240607",
    "fecha": "2024-06-06"
}

collection.insert_one(event)
'''


