from django.http import HttpResponse
import pymongo
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

def checkData(data, keys):
    for key in keys:
        if key not in data:
            return (False, "Missing key {} in data sent".format(key))
    return (True, "Data seems good")

def checkAvailability(data, collection):
    location = data['location']
    date = data['date']

    return list(collection.find({"location": location, "date": date}))


def addEvento(request):
    collection = db['agenda']
    data = json.loads(request.body.decode('utf-8'))
    keys = ['name', 'clients', 'type', 'date', 'location', 'num_of_people', 'cost', 'upfront']

    isDataCorrect, message = checkData(data, keys)

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

def delEvento(request):
    if not request.content_type == 'application/json':\
        return HttpResponse([[{'message':'missing JSON'}]], content_type='application/json')

    collection = db['agenda']
    message = 'Entry not found'
    data = json.loads(request.body.decode('utf-8'))
    keys = ['name', 'date', 'location']
    
    isDataCorrect, message = checkData(data, keys)

    if isDataCorrect:
        eventFound = checkAvailability(data, collection)
        if eventFound:
            print("Event found")
            res = collection.delete_one(data)

            # Check if the deletion was successful
            if res.deleted_count == 1:
                message = 'Event deleted successfully.'
            else:
                message = 'Event was found but No event was deleted'
        else:
            message = 'Not event found with {} and location {}'.format(data['date'], data['location'])
    json_data = json_util.dumps([{"message": message}])
    response = HttpResponse(json_data, content_type='application/json')
    return response
